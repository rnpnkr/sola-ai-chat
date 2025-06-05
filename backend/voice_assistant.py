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
from tts_service import ElevenLabsService
from agents.langgraph_orchestrator import langgraph_pipeline
from agents.personality_agent import PersonalityAgent, neo_config

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
        self.tts_service = ElevenLabsService()
        self.langgraph_pipeline = langgraph_pipeline
        self.personality_agent = PersonalityAgent(neo_config)

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

    async def process_audio_with_langgraph(self, client_id: str, audio_data: bytes):
        """Process audio using LangGraph with DUAL streaming"""
        try:
            # Send recording_complete status for total time measurement
            await manager.send_status(client_id, "recording_complete")
            initial_state = {
                "audio_input": audio_data,
                "transcript": "",
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