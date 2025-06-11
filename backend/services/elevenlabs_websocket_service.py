import asyncio
from websockets.legacy.client import connect as ws_connect
import json
import logging
from typing import Callable, Optional
import os
import base64

class ElevenLabsWebSocketService:
    """
    WebSocket-based TTS service that can accept streaming text input
    and produce audio output in real-time
    """
    
    def __init__(self, api_key: str = None, voice_id: str = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "bIHbv24MWmeRgasZH58o")
        self.websocket = None
        self.is_connected = False
        self.audio_callback = None
        self.current_context_id = None  # Track current context
        self.context_counter = 0  # For generating unique context IDs
        
    async def connect_streaming_session(self, audio_callback: Callable[[bytes], None]):
        """Connect to Multi-Context WebSocket endpoint"""
        self.audio_callback = audio_callback
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/multi-stream-input?model_id=eleven_flash_v2_5"
        try:
            self.websocket = await ws_connect(uri)
            self.is_connected = True
            await self._create_new_context()
            asyncio.create_task(self._listen_for_audio())
            logging.info("ElevenLabs Multi-Context WebSocket connected")
        except Exception as e:
            logging.error(f"Failed to connect to ElevenLabs Multi-Context WebSocket: {e}")
            self.is_connected = False

    async def _create_new_context(self):
        """Create a new context for audio generation"""
        self.context_counter += 1
        self.current_context_id = f"context_{self.context_counter}"
        init_message = {
            "text": " ",
            "context_id": self.current_context_id,
            "xi_api_key": self.api_key,
            "voice_settings": {
                "stability": 0.0,
                "similarity_boost": 1.0,
                "style": 0.0,
                "use_speaker_boost": True
            },
            "generation_config": {
                "chunk_length_schedule": [120, 160, 250, 290],
                "auto_mode": True
            },
            "output_format": "mp3_22050_32"
        }
        await self.websocket.send(json.dumps(init_message))
        logging.info(f"Created new context: {self.current_context_id}")
        return self.current_context_id

    async def interrupt_current_speech(self):
        """Interrupt current speech and create new context"""
        if not self.is_connected or not self.current_context_id:
            return None
        close_message = {
            "text": "",
            "context_id": self.current_context_id
        }
        try:
            await self.websocket.send(json.dumps(close_message))
            logging.info(f"Closed context for interruption: {self.current_context_id}")
            new_context_id = await self._create_new_context()
            logging.info(f"Created new context after interruption: {new_context_id}")
            return new_context_id
        except Exception as e:
            logging.error(f"Error during speech interruption: {e}")
            return None

    async def ensure_connection(self):
        """Ensure WebSocket connection is active, reconnect if needed"""
        if not self.is_connected or not self.websocket:
            logging.warning("WebSocket disconnected, attempting to reconnect...")
            if self.audio_callback:
                await self.connect_streaming_session(self.audio_callback)
            else:
                logging.error("Cannot reconnect: no audio callback set")
                return False
        return True

    async def stream_text_chunk(self, text_chunk: str):
        """
        Send a text chunk to ElevenLabs for immediate audio generation
        """
        if not await self.ensure_connection() or not self.current_context_id:
            return
        try:
            message = {
                "text": text_chunk,
                "context_id": self.current_context_id,
                "try_trigger_generation": True
            }
            await self.websocket.send(json.dumps(message))
            logging.debug(f"Sent text chunk to {self.current_context_id}: {text_chunk}")
        except Exception as e:
            logging.error(f"Failed to send text chunk: {e}")
            self.is_connected = False

    async def finish_streaming(self):
        """
        Signal end of text input and wait for final audio from ElevenLabs.
        According to ElevenLabs docs, send empty string to close connection.
        """
        if not self.is_connected or not self.websocket:
            return
        try:
            eos_message = {"text": ""}
            await self.websocket.send(json.dumps(eos_message))
            logging.debug("Sent EOS message to ElevenLabs")
            try:
                await asyncio.wait_for(self.websocket.wait_closed(), timeout=15.0)
                logging.info("ElevenLabs WebSocket streaming finished (server closed connection)")
            except asyncio.TimeoutError:
                logging.warning("Timed out waiting for ElevenLabs to finish streaming audio")
                await self.websocket.close()
            self.is_connected = False
        except Exception as e:
            logging.error(f"Error finishing stream: {e}")
            self.is_connected = False

    async def flush_and_finish(self):
        """
        Flush any remaining text and finish streaming.
        ElevenLabs recommends using flush=true for conversational AI.
        """
        if not self.is_connected or not self.current_context_id:
            return
        try:
            flush_message = {
                "text": "",
                "context_id": self.current_context_id,
                "flush": True
            }
            await self.websocket.send(json.dumps(flush_message))
            logging.debug(f"Sent flush to context: {self.current_context_id}")
            await asyncio.sleep(0.5)
            close_message = {
                "text": "",
                "context_id": self.current_context_id
            }
            await self.websocket.send(json.dumps(close_message))
            logging.info(f"Closed context: {self.current_context_id}")
            await asyncio.sleep(1.0)
        except Exception as e:
            logging.error(f"Error during flush and finish: {e}")
            self.is_connected = False

    async def _listen_for_audio(self):
        try:
            while self.is_connected and self.websocket:
                msg = await self.websocket.recv()
                data = json.loads(msg)
                if "audio" in data:
                    context_id = data.get("contextId", "unknown")
                    is_final = data.get("isFinal", False)
                    audio_data = data["audio"]
                    if is_final:
                        logging.info(f"Context {context_id} generation complete")
                        continue  # Don't break, other contexts might be active
                    elif audio_data is not None and audio_data != "":
                        try:
                            audio_bytes = base64.b64decode(audio_data)
                            if len(audio_bytes) > 0 and self.audio_callback:
                                self.audio_callback(audio_bytes)
                                logging.debug(f"Audio chunk from {context_id}: {len(audio_bytes)} bytes")
                        except Exception as e:
                            logging.error(f"Failed to decode audio chunk: {e}")
        except Exception as e:
            logging.error(f"Error listening for audio: {e}")
        finally:
            self.is_connected = False 