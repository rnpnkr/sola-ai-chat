import os
import asyncio
import logging
import json
from typing import Callable, Optional
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from config import DEEPGRAM_CONFIG

logger = logging.getLogger(__name__)

class DeepgramStreamingService:
    def __init__(self, config=None):
        self.config = config or DEEPGRAM_CONFIG
        self.api_key = self.config["api_key"]
        self.dg_client = DeepgramClient(self.api_key)
        self.connection = None
        self.connected = False
        self._audio_queue = asyncio.Queue()
        self._stream_task = None
        self._reconnect_attempts = 0
        self._max_reconnects = 3
        self._transcript_callback = None
        self._vad_callback = None
        self._stop_event = asyncio.Event()
        self._keepalive_task = None
        # Store the latest non-empty transcript so callers can fall back if needed
        self._latest_good_transcript: str = ""
        # Store reference to the asyncio loop that owns this service
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def configure_vad_settings(self) -> LiveOptions:
        return LiveOptions(
            model="nova-2",
            punctuate=True,
            language="en-US",
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=500,
            smart_format=True,
        )

    def is_connected(self) -> bool:
        return self.connected

    async def start_streaming(self, transcript_callback: Callable, vad_callback: Optional[Callable] = None):
        """Start Deepgram WebSocket connection and begin streaming audio."""
        # Capture loop early so we can reference it from non-async threads later
        self._loop = asyncio.get_running_loop()
        self._transcript_callback = transcript_callback
        self._vad_callback = vad_callback
        self._stop_event.clear()
        try:
            options = self.configure_vad_settings()
            logger.info(f"Deepgram connection attempt:")
            logger.info(f"  API Key: {self.api_key[:10]}...")
            logger.info(f"  Options: {options.__dict__}")
            self.connection = self.dg_client.listen.websocket.v("1")
            self._register_event_handlers()
            result = self.connection.start(options)
            if result is False:
                logger.error("Failed to start Deepgram connection - start() returned False")
                self.connected = False
                return
            self.connected = True
            logger.info("Deepgram WebSocket connection started successfully.")
            self._keepalive_task = asyncio.create_task(self._send_keepalive())
            self._stream_task = asyncio.create_task(self._audio_stream_loop())
        except Exception as e:
            logger.error(f"Failed to start Deepgram streaming: {e}")
            logger.error(f"Config: {self.config}")
            self.connected = False

    async def send_audio_chunk(self, audio_data: bytes):
        """Queue audio chunk for streaming to Deepgram."""
        if not self.connected:
            logger.warning("Deepgram connection not active. Dropping audio chunk.")
            return
        # Validate chunk size and content
        if not audio_data or len(audio_data) < 1024:
            logger.debug(f"Insufficient audio data: {len(audio_data) if audio_data else 0} bytes, skipping")
            return
        if not audio_data or len(audio_data) != 2048:
            logger.warning(f"Dropping audio chunk: invalid size ({len(audio_data) if audio_data else 0} bytes), expected 2048 bytes of raw PCM.")
            return
        # Debug the first few audio chunks to verify format
        if not hasattr(self, '_debug_chunk_count'):
            self._debug_chunk_count = 0
        if self._debug_chunk_count < 3:
            # Check if it looks like WAV header
            if audio_data[:4] == b'RIFF':
                logger.info(f"  WAV header detected")
                logger.info(f"  File size: {int.from_bytes(audio_data[4:8], 'little')}")
                logger.info(f"  Format: {audio_data[8:12]}")
                logger.info(f"  Sample rate: {int.from_bytes(audio_data[24:28], 'little')}")
        self._debug_chunk_count += 1
        logger.debug(f"Queueing audio chunk: {len(audio_data)} bytes")
        await self._audio_queue.put(audio_data)

    async def stop_streaming(self):
        """Full shutdown (kept for compatibility)."""
        await self.stop_audio_only()
        await self.finish_connection()

    async def stop_audio_only(self):
        """Stop sending audio but keep WebSocket open so final transcripts can arrive."""
        self._stop_event.set()
        if self._stream_task:
            try:
                await self._stream_task
            except Exception:
                pass  # task may already be done

    async def finish_connection(self):
        """Close the WebSocket connection once we're done receiving transcripts."""
        if self.connection:
            try:
                self.connection.finish()
                logger.info("Deepgram WebSocket connection closed.")
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")
        self.connected = False
        self._audio_queue = asyncio.Queue()

    def _register_event_handlers(self):
        self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
        self.connection.on(LiveTranscriptionEvents.Transcript, self.handle_transcript_event)
        self.connection.on(LiveTranscriptionEvents.SpeechStarted, self.handle_vad_event)
        self.connection.on(LiveTranscriptionEvents.UtteranceEnd, self.handle_vad_event)
        self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
        self.connection.on(LiveTranscriptionEvents.Close, self._on_close)

    def _on_open(self, *args, **kwargs):
        logger.info("Deepgram WebSocket opened.")
        self.connected = True
        self._reconnect_attempts = 0

    def handle_transcript_event(self, *args, **kwargs):
        """Handle transcript events from Deepgram - synchronous handler"""
        #logger.info(f"[DeepgramStreamingService] handle_transcript_event called: args={args}, kwargs={kwargs}")
        result = None
        if len(args) >= 2:
            result = args[1]
        elif 'result' in kwargs:
            result = kwargs['result']
        if result is None:
            logger.warning("[DeepgramStreamingService] No transcript payload found in callback arguments")
            return
        logger.info(f"[DeepgramStreamingService] TRANSCRIPT RESULT TYPE: {type(result)}")
        # Store for async processing
        # Avoid pushing duplicate or empty final transcripts to the queue to
        # prevent double-processing on the caller side. Deepgram sometimes
        # sends an extra `is_final` message with an empty `transcript` string
        # right after the real final message. That leads to logs such as
        # "processing 2 transcripts" even though only one meaningful utterance
        # exists. We simply drop empty finals or consecutive duplicates.

        transcript_text: str = ""
        if hasattr(result, 'channel') and hasattr(result.channel, 'alternatives'):
            transcript_text = result.channel.alternatives[0].transcript or ""

        # Deduplication conditions
        should_enqueue = True
        if not transcript_text.strip():
            # Empty transcript – very common artefact – skip.
            should_enqueue = False
        else:
            # Skip consecutive duplicates (compare with latest good transcript)
            if transcript_text.strip() == getattr(self, '_latest_good_transcript', ""):
                # Only skip if *both* have is_final flag to avoid losing early partials
                if getattr(result, 'is_final', False):
                    should_enqueue = False

        if should_enqueue:
            if hasattr(self, '_pending_transcripts'):
                self._pending_transcripts.append(result)
            else:
                self._pending_transcripts = [result]
        else:
            logger.info("[DeepgramStreamingService] 🚫 Skipping empty/duplicate final transcript event")
        # Try to extract transcript for immediate logging
        try:
            if hasattr(result, 'channel') and hasattr(result.channel, 'alternatives'):
                transcript = result.channel.alternatives[0].transcript
                is_final = getattr(result, 'is_final', False)
                speech_final = getattr(result, 'speech_final', False)
                logger.info(f"[DeepgramStreamingService] LIVE TRANSCRIPT: '{transcript}' (is_final={is_final}, speech_final={speech_final})")
                # CRITICAL FIX: Only update latest good transcript if we have actual content
                if transcript.strip():  # Only update if we have real content
                    self._latest_good_transcript = transcript
                    logger.info(f"[DeepgramStreamingService] ✅ Updated latest good transcript: '{transcript}'")
                else:
                    logger.info(f"[DeepgramStreamingService] ❌ Ignoring empty transcript, keeping: '{self._latest_good_transcript}'")
            else:
                logger.info(f"[DeepgramStreamingService] TRANSCRIPT STRUCTURE: {dir(result)}")
        except Exception as e:
            logger.warning(f"[DeepgramStreamingService] Could not extract transcript: {e}")
        # --- CRITICAL: Immediately drain and run the async callback ---
        if self._transcript_callback and self._loop and not self._loop.is_closed():
            try:
                # Schedule the coroutine to process pending events on the service's loop
                asyncio.run_coroutine_threadsafe(self._process_pending_events(), self._loop)
            except Exception as e:
                logger.error(f"[DeepgramStreamingService] Error running transcript callback in event loop: {e}")

    def handle_vad_event(self, *args, **kwargs):
        """Handle VAD events from Deepgram - synchronous handler"""
        if not self._vad_callback:
            return

        event = None
        if len(args) >= 2:
            # args[0] is the connection object, args[1] is the actual event
            event = args[1]
        elif 'event' in kwargs:
            event = kwargs['event']
        if event is None and kwargs:
            # Fallback: take the first value in kwargs as the event payload
            event = next(iter(kwargs.values()))
        if event is None:
            logger.warning("[DeepgramStreamingService] No VAD payload found in callback arguments")
            return
        # Store the event for later async processing
        if hasattr(self, '_pending_vad_events'):
            self._pending_vad_events.append(event)
        else:
            self._pending_vad_events = [event]
        # Log the VAD event for debugging
        logger.info(f"VAD event received: {type(event).__name__}")

    def _on_error(self, *args, **kwargs):
        """Handle Deepgram WebSocket errors"""
        # args[0] is connection, args[1] is the error if present
        error = args[1] if len(args) >= 2 else (args[0] if args else "Unknown error")
        logger.error(f"Deepgram WebSocket error: {error}")
        self.connected = False

    def _on_close(self, *args, **kwargs):
        """Handle Deepgram WebSocket close"""
        # args[0] is connection, args[1] is close info if present  
        close_info = args[1] if len(args) >= 2 else (args[0] if args else "Connection closed")
        logger.info(f"Deepgram WebSocket closed: {close_info}")
        self.connected = False

    async def _process_pending_events(self):
        """Process any pending transcript and VAD events"""
        # Process transcripts
        if hasattr(self, '_pending_transcripts') and self._pending_transcripts:
            logger.info(f"[DeepgramStreamingService] _process_pending_events: processing {len(self._pending_transcripts)} transcripts")
            for result in self._pending_transcripts:
                if self._transcript_callback:
                    #logger.info(f"[DeepgramStreamingService] _process_pending_events: calling transcript_callback with result: {result}")
                    try:
                        await self._transcript_callback(result)
                    except Exception as e:
                        logger.error(f"Error in transcript callback: {e}")
            self._pending_transcripts = []
        # Process VAD events
        if hasattr(self, '_pending_vad_events') and self._pending_vad_events:
            logger.info(f"[DeepgramStreamingService] _process_pending_events: processing {len(self._pending_vad_events)} VAD events")
            for event in self._pending_vad_events:
                if self._vad_callback:
                    try:
                        await self._vad_callback(event)
                    except Exception as e:
                        logger.error(f"Error in VAD callback: {e}")
            self._pending_vad_events = []

    async def _audio_stream_loop(self):
        total_bytes_sent = 0
        chunk_count = 0
        while not self._stop_event.is_set():
            try:
                # Process pending events first
                await self._process_pending_events()
                # Then handle audio with timeout
                try:
                    audio_data = await asyncio.wait_for(self._audio_queue.get(), timeout=0.1)
                    if not self.connected:
                        logger.warning("Not connected, skipping audio chunk.")
                        continue
                    chunk_count += 1
                    total_bytes_sent += len(audio_data)
                    logger.debug(f"Sending PCM chunk #{chunk_count} to Deepgram: {len(audio_data)} bytes (total: {total_bytes_sent})")
                    self.connection.send(audio_data)
                except asyncio.TimeoutError:
                    # No audio data, continue loop to process events
                    continue
            except Exception as e:
                logger.error(f"Error in audio stream loop: {e}")
                await asyncio.sleep(0.1)
        logger.info(f"Audio stream loop ended. Sent {chunk_count} chunks, {total_bytes_sent} total bytes")

    async def _handle_reconnect(self):
        if self._reconnect_attempts < self._max_reconnects:
            self._reconnect_attempts += 1
            logger.info(f"Attempting Deepgram reconnect ({self._reconnect_attempts})...")
            await asyncio.sleep(2 ** self._reconnect_attempts)
            await self.start_streaming(self._transcript_callback, self._vad_callback)
        else:
            logger.error("Max Deepgram reconnect attempts reached. Giving up.")
            self.connected = False

    async def _send_keepalive(self):
        """Send periodic KeepAlive messages to prevent timeout"""
        while self.connected and not self._stop_event.is_set():
            try:
                await asyncio.sleep(5)  # Send every 5 seconds
                if self.connected:
                    keepalive_msg = {"type": "KeepAlive"}
                    # Send as text message, not binary
                    self.connection.send(json.dumps(keepalive_msg))
                    logger.debug("Sent KeepAlive message")
            except Exception as e:
                logger.error(f"KeepAlive error: {e}")
                break

    def get_accumulated_transcript(self) -> str:
        """Return the accumulated transcript from the streaming session."""
        return self._latest_good_transcript 