from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import asyncio
import json
import base64
import uuid
import tempfile
import os
from typing import Dict, Optional
import logging
logger = logging.getLogger(__name__)

# Import your existing services
from services.deepgram_service import DeepgramService
from services.ai_service import OpenRouterService
from services.elevenlabs_streaming import ElevenLabsStreamingService
from agents.langgraph_orchestrator import langgraph_pipeline
from agents.personality_agent import PersonalityAgent, neo_config
from services.deepgram_streaming_service import DeepgramStreamingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WebSocket Voice Assistant")

app.mount("/static", StaticFiles(directory="."), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_status: Dict[str, str] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.processing_status[client_id] = "connected"
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.processing_status:
            del self.processing_status[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")

    async def send_status(self, client_id: str, status: str, data: Optional[dict] = None):
        message = {"type": "status", "status": status}
        if data:
            message.update(data)
        await self.send_message(client_id, message)

    async def send_error(self, client_id: str, error: str):
        await self.send_message(client_id, {"type": "error", "message": error})

    async def send_result(self, client_id: str, result: dict):
        await self.send_message(client_id, {"type": "result", **result})


manager = ConnectionManager()


class VoiceAssistantWebSocket:
    def __init__(self):
        self.stt_service = DeepgramService()
        self.ai_service = OpenRouterService()
        self.tts_service = ElevenLabsStreamingService()
        self.langgraph_pipeline = langgraph_pipeline
        self.personality_agent = PersonalityAgent(neo_config)
        # Streaming state per client
        self.streaming_services = {}
        self.audio_buffers = {}
        self.streaming_vad_events = {}

    def convert_webm_to_pcm(self, webm_data: bytes) -> bytes:
        """
        Convert WebM audio data to PCM format for Deepgram.
        This is a simplified conversion - in production, use ffmpeg or similar.
        """
        try:
            # For now, return raw data and let Deepgram handle it
            # In production, implement proper WebM -> PCM conversion
            logger.debug(f"[AUDIO] Received WebM chunk of {len(webm_data)} bytes (no conversion applied)")
            return webm_data
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return webm_data

    async def start_audio_streaming(self, client_id: str, config: dict):
        """Initialize streaming STT service for client."""
        try:
            if client_id in self.streaming_services:
                await self.complete_audio_streaming(client_id)  # Cleanup any previous session
            service = DeepgramStreamingService()
            # initialize backup transcript store
            service._latest_good_transcript = ""
            final_transcript_holder = {"value": ""}
            speech_ended = asyncio.Event()
            self.audio_buffers[client_id] = []
            self.streaming_vad_events[client_id] = speech_ended
            async def transcript_callback(result):
                try:
                    alternatives = result.channel.alternatives
                    is_final = getattr(result, 'is_final', False)
                    speech_final = getattr(result, 'speech_final', False)
                    if alternatives and len(alternatives) > 0:
                        token = alternatives[0].transcript
                        logger.info(f"[{client_id}] Transcript event: is_final={is_final}, speech_final={speech_final}, token='{token}'")
                        # CRITICAL FIX: Only update final transcript with non-empty content
                        if token.strip():  # Prevent empty strings from overwriting good transcripts
                            final_transcript_holder["value"] = token
                            service._latest_good_transcript = token  # keep backup in service as well
                            logger.info(f"[{client_id}] ✅ Final transcript updated: '{final_transcript_holder['value']}'")
                            if (is_final or speech_final):
                                speech_ended.set()
                                logger.info(f"[{client_id}] ✅ Speech ended event set due to final transcript")
                            await manager.send_message(client_id, {"type": "transcript_token", "token": token})
                        else:
                            logger.info(f"[{client_id}] ❌ IGNORING empty transcript, keeping: '{final_transcript_holder['value']}'")
                            if (is_final or speech_final):
                                speech_ended.set()
                                logger.info(f"[{client_id}] ✅ Speech ended event set despite empty transcript")
                except Exception as e:
                    logger.error(f"[{client_id}] Transcript callback error: {e}")
            async def vad_callback(event):
                try:
                    event_type = getattr(event, 'type', None) or getattr(event, '__class__', type(event)).__name__.lower()
                    logger.info(f"[{client_id}] VAD event: {event_type}")
                    if "speech" in str(event_type).lower() and "start" in str(event_type).lower():
                        await manager.send_status(client_id, "speech_detected")
                    elif "utterance" in str(event_type).lower() or "end" in str(event_type).lower():
                        await manager.send_status(client_id, "speech_ended")
                        speech_ended.set()
                except Exception as e:
                    logger.error(f"VAD callback error: {e}")
            await service.start_streaming(transcript_callback, vad_callback)
            self.streaming_services[client_id] = {
                "service": service,
                "speech_ended": speech_ended,
                "final_transcript_holder": final_transcript_holder
            }
            await manager.send_status(client_id, "stream_started")
            logger.info(f"[{client_id}] Streaming STT service started successfully")
        except Exception as e:
            logger.error(f"Failed to start streaming for {client_id}: {e}")
            await manager.send_error(client_id, f"Streaming initialization failed: {str(e)}")

    def validate_audio_data(self, audio_data: bytes) -> bool:
        """Validate that audio data is properly formatted"""
        try:
            if len(audio_data) == 0:
                logger.warning("Empty audio data")
                return False
            # Check for WAV header
            if len(audio_data) >= 12 and audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
                logger.debug(f"Valid WAV header detected, total size: {len(audio_data)} bytes")
                return True
            # Also accept raw PCM data (for linear16 encoding)
            elif len(audio_data) >= 2:  # At least one 16-bit sample
                logger.debug(f"Accepting raw PCM data: {len(audio_data)} bytes")
                return True
            else:
                logger.warning(f"Invalid audio format, size: {len(audio_data)}")
                return False
        except Exception as e:
            logger.error(f"Audio validation error: {e}")
            return False

    async def process_audio_chunk(self, client_id: str, audio_data: bytes):
        """Forward audio chunk to streaming service."""
        if client_id not in self.streaming_services:
            logger.warning(f"No streaming service for client {client_id}")
            return
        # For streaming, extract raw PCM from WAV if present
        if len(audio_data) > 44 and audio_data[:4] == b'RIFF':
            # Extract raw PCM data (skip 44-byte WAV header)
            raw_pcm = audio_data[44:]
            logger.info(f"[{client_id}] Extracted {len(raw_pcm)} bytes raw PCM from WAV container")
            audio_to_send = raw_pcm
        else:
            # Already raw PCM
            audio_to_send = audio_data
        service = self.streaming_services[client_id]["service"]
        await service.send_audio_chunk(audio_to_send)
        self.audio_buffers[client_id].append(audio_data)  # Store original for fallback

    async def complete_audio_streaming(self, client_id: str):
        """Complete streaming, trigger LangGraph pipeline, cleanup."""
        if client_id not in self.streaming_services:
            logger.warning(f"No streaming service for client {client_id} on complete.")
            return
        service = self.streaming_services[client_id]["service"]
        speech_ended = self.streaming_services[client_id]["speech_ended"]
        final_transcript_holder = self.streaming_services[client_id]["final_transcript_holder"]

        # --- Phase 1: stop sending audio, but keep socket open ---
        await service.stop_audio_only()

        # Send STT processing status for frontend timing (after audio is done, before draining events)
        await manager.send_status(client_id, "stt_processing")

        # Wait for either VAD-based speech end OR user timeout of 0.4 s
        try:
            await asyncio.wait_for(speech_ended.wait(), timeout=0.4)
        except asyncio.TimeoutError:
            pass  # user may have clicked early; we'll rely on flush below

        # --- Phase 2: drain pending Deepgram events for up to 0.6 s ---
        drain_deadline = asyncio.get_event_loop().time() + 0.6
        while asyncio.get_event_loop().time() < drain_deadline and not final_transcript_holder["value"]:
            if hasattr(service, "_process_pending_events"):
                await service._process_pending_events()
            await asyncio.sleep(0.05)

        # After grace period, explicitly process once more
        if hasattr(service, "_process_pending_events"):
            await service._process_pending_events()

        # If we still don't have a transcript but service captured one, copy it
        if (not final_transcript_holder["value"].strip()) and getattr(service, "_latest_good_transcript", "").strip():
            final_transcript_holder["value"] = service._latest_good_transcript
            logger.info(f"[{client_id}] 🌟 Adopted service._latest_good_transcript before closing: '{final_transcript_holder['value']}'")

        # --- Phase 3: close WebSocket ---
        await service.finish_connection()

        # --- Phase 4: final drain for late events ---
        final_deadline = asyncio.get_event_loop().time() + 0.4
        while asyncio.get_event_loop().time() < final_deadline and not final_transcript_holder["value"]:
            if hasattr(service, "_process_pending_events"):
                await service._process_pending_events()
            await asyncio.sleep(0.05)

        # CRITICAL FIX: Use the best available transcript
        final_transcript = final_transcript_holder['value']
        # Backup: Check if the service has accumulated transcript
        if not final_transcript.strip():
            final_transcript = service.get_accumulated_transcript()
            logger.info(f"[{client_id}] 🔄 Using accumulated transcript from service: '{final_transcript}'")
        logger.info(f"[{client_id}] Debug - final_transcript_holder: '{final_transcript_holder['value']}'")
        logger.info(f"[{client_id}] Debug - service accumulated: '{service.get_accumulated_transcript()}'")
        logger.info(f"[{client_id}] Final transcript at end of streaming: '{final_transcript}'")
        logger.info(f"[{client_id}] Passing transcript to LangGraph: '{final_transcript}'")
        # Run LangGraph pipeline with accumulated audio and, if available, transcript
        audio_data = b"".join(self.audio_buffers[client_id])
        await self.process_audio_with_langgraph(client_id, audio_data, final_transcript)
        # Cleanup
        del self.streaming_services[client_id]
        del self.audio_buffers[client_id]
        del self.streaming_vad_events[client_id]

    async def process_audio_stream(self, client_id: str, audio_data: bytes):
        """Process audio with real-time status updates"""
        temp_dir = tempfile.gettempdir()
        session_id = str(uuid.uuid4())
        input_path = os.path.join(temp_dir, f"input_{session_id}.wav")
        output_path = os.path.join(temp_dir, f"output_{session_id}.mp3")

        try:
            # Save audio data
            await manager.send_status(client_id, "saving_audio")
            with open(input_path, 'wb') as f:
                f.write(audio_data)

            # Step 1: Speech to Text
            await manager.send_status(client_id, "stt_processing")
            transcript = await asyncio.to_thread(
                self.stt_service.transcribe, input_path
            )

            if not transcript:
                await manager.send_error(client_id, "Failed to transcribe audio")
                return

            await manager.send_status(client_id, "transcription_complete",
                                      {"transcript": transcript})

            # Step 2: Get AI Response
            await manager.send_status(client_id, "llm_streaming")
            ai_response = await asyncio.to_thread(
                self.ai_service.get_response, transcript
            )

            if not ai_response:
                await manager.send_error(client_id, "Failed to generate AI response")
                return

            await manager.send_status(client_id, "response_generated",
                                      {"ai_response": ai_response})

            # Step 3: Text to Speech
            await manager.send_status(client_id, "tts_generating")
            output_file = await asyncio.to_thread(
                self.tts_service.text_to_speech, ai_response, output_path
            )

            if not output_file:
                await manager.send_error(client_id, "Failed to generate speech")
                return

            # Read the generated audio file
            with open(output_path, 'rb') as f:
                audio_content = f.read()

            # Send final result with audio data
            await manager.send_result(client_id, {
                "transcript": transcript,
                "ai_response": ai_response,
                "audio_data": base64.b64encode(audio_content).decode('utf-8'),
                "session_id": session_id
            })

            await manager.send_status(client_id, "pipeline_complete")

        except Exception as e:
            logger.error(f"Processing error for client {client_id}: {e}")
            await manager.send_error(client_id, f"Processing failed: {str(e)}")

        finally:
            # Cleanup temp files
            for file_path in [input_path, output_path]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {file_path}: {e}")

    async def process_text_to_speech(self, client_id: str, text: str):
        """Convert text directly to speech"""
        temp_dir = tempfile.gettempdir()
        session_id = str(uuid.uuid4())
        output_path = os.path.join(temp_dir, f"tts_{session_id}.mp3")

        try:
            await manager.send_status(client_id, "generating_speech")

            output_file = await asyncio.to_thread(
                self.tts_service.text_to_speech, text, output_path
            )

            if not output_file:
                await manager.send_error(client_id, "Failed to generate speech")
                return

            # Read the generated audio file
            with open(output_path, 'rb') as f:
                audio_content = f.read()

            await manager.send_result(client_id, {
                "text": text,
                "audio_data": base64.b64encode(audio_content).decode('utf-8'),
                "session_id": session_id
            })

            await manager.send_status(client_id, "completed")

        except Exception as e:
            logger.error(f"TTS error for client {client_id}: {e}")
            await manager.send_error(client_id, f"TTS failed: {str(e)}")

        finally:
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup {output_path}: {e}")

    async def process_audio_with_langgraph(self, client_id: str, audio_data: bytes, transcript: str = ""):
        """Process audio using LangGraph with DUAL streaming"""
        try:
            logger.info(f"[{client_id}] process_audio_with_langgraph received transcript: '{transcript}'")
            # Send recording_complete status for total time measurement
            await manager.send_status(client_id, "recording_complete")
            initial_state = {
                "audio_input": audio_data,
                "transcript": transcript,
                "ai_response": "",
                "audio_output": b"",
                "personality_type": "neo",
                "client_id": client_id
            }
            # Pass manager through config for WebSocket updates
            config = {
                "configurable": {
                    "manager": manager,
                    "client_id": client_id
                }
            }
            # Stream mode "values" for node completion
            async for chunk in self.langgraph_pipeline.astream(
                initial_state,
                stream_mode="values",
                config=config
            ):
                # Node completion updates
                if chunk.get("transcript") and not chunk.get("ai_response"):
                    await manager.send_status(client_id, "transcription_complete", {"transcript": chunk["transcript"]})
                elif chunk.get("ai_response") and not chunk.get("audio_output"):
                    await manager.send_status(client_id, "response_generated", {"ai_response": chunk["ai_response"]})
                elif chunk.get("audio_output"):
                    await manager.send_result(client_id, {
                        "transcript": chunk["transcript"],
                        "ai_response": chunk["ai_response"],
                        "audio_data": base64.b64encode(chunk["audio_output"]).decode('utf-8'),
                        "session_id": str(uuid.uuid4())
                    })
                    await manager.send_status(client_id, "completed")
        except Exception as e:
            logger.error(f"LangGraph processing error: {e}")
            await manager.send_error(client_id, f"LangGraph failed: {str(e)}")


assistant = VoiceAssistantWebSocket()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "audio_upload":
                # Handle audio file upload
                audio_data = base64.b64decode(message["audio_data"])
                await assistant.process_audio_stream(client_id, audio_data)

            elif message_type == "audio_stream_start":
                # Initialize streaming STT service
                await assistant.start_audio_streaming(client_id, message.get("config", {}))

            elif message_type == "audio_chunk":
                # Forward audio chunk to streaming service
                audio_data = base64.b64decode(message["audio_data"])
                await assistant.process_audio_chunk(client_id, audio_data)

            elif message_type == "audio_stream_end":
                # Complete streaming and trigger LangGraph pipeline
                await assistant.complete_audio_streaming(client_id)

            elif message_type == "audio_stream":
                # Handle real-time audio streaming (for future enhancement)
                await manager.send_status(client_id, "streaming_not_implemented")

            elif message_type == "text_to_speech":
                # Handle direct text-to-speech
                text = message.get("text", "")
                if text:
                    await assistant.process_text_to_speech(client_id, text)
                else:
                    await manager.send_error(client_id, "No text provided")

            elif message_type == "langgraph_stream":
                audio_data = base64.b64decode(message["audio_data"])
                await assistant.process_audio_with_langgraph(client_id, audio_data)

            elif message_type == "ping":
                # Handle ping/keepalive
                await manager.send_message(client_id, {"type": "pong"})

            else:
                await manager.send_error(client_id, f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await manager.send_error(client_id, f"Connection error: {str(e)}")
        manager.disconnect(client_id)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "message": "WebSocket Voice Assistant is running"
    }

@app.get("/")
async def get_homepage():
    # Serve the new index.html instead of HTML string
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)