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
        
    async def connect_streaming_session(self, audio_callback: Callable[[bytes], None]):
        """
        Establish WebSocket connection for streaming TTS
        """
        self.audio_callback = audio_callback
        
        # ElevenLabs WebSocket streaming endpoint (model_id as query param)
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_turbo_v2_5"
        
        try:
            # Establish WebSocket without extra_headers to avoid incompat issues
            self.websocket = await ws_connect(uri)
            self.is_connected = True
            
            # Send initial configuration (include api_key)
            config_message = {
                "xi_api_key": self.api_key,
                "text": " ",
                "voice_settings": {
                    "stability": 0.0,
                    "similarity_boost": 1.0,
                    "style": 0.0,
                    "use_speaker_boost": True
                },
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]
                },
                "output_format": "mp3_22050_32"
            }
            
            await self.websocket.send(json.dumps(config_message))
            
            # Start listening for audio chunks
            asyncio.create_task(self._listen_for_audio())
            
            logging.info("ElevenLabs WebSocket connected and configured")
            
        except Exception as e:
            logging.error(f"Failed to connect to ElevenLabs WebSocket: {e}")
            self.is_connected = False
            
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
        # Ensure connection is active
        if not await self.ensure_connection():
            return
        try:
            # ElevenLabs requires try_trigger_generation true to force immediate audio
            message = {
                "text": text_chunk,
                "try_trigger_generation": True
            }
            await self.websocket.send(json.dumps(message))
            logging.debug(f"Sent text chunk: {text_chunk}")
        except Exception as e:
            logging.error(f"Failed to send text chunk: {e}")
            self.is_connected = False

    async def finish_streaming(self):
        """
        Signal end of text input and wait for final audio from ElevenLabs.
        We do NOT close the socket ourselves; we wait for the server to close
        so we can receive all remaining audio chunks.
        """
        if not self.is_connected or not self.websocket:
            return
        try:
            # Send EOS (End of Stream)
            await self.websocket.send(json.dumps({"text": ""}))
            # Wait for server to close connection, or timeout after 10 s
            try:
                await asyncio.wait_for(self.websocket.wait_closed(), timeout=10.0)
            except asyncio.TimeoutError:
                logging.warning("Timed out waiting for ElevenLabs to finish streaming audio")
                await self.websocket.close()
            self.is_connected = False
            logging.info("ElevenLabs WebSocket streaming finished (server closed connection)")
        except Exception as e:
            logging.error(f"Error finishing stream: {e}")
            
    async def _listen_for_audio(self):
        """
        Listen for incoming audio JSON chunks from ElevenLabs and forward to callback
        """
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                except (TypeError, json.JSONDecodeError):
                    logging.debug("Received non-JSON message from ElevenLabs; ignoring")
                    continue
                
                if "audio" in data:
                    # Decode base64 audio string
                    try:
                        audio_bytes = base64.b64decode(data["audio"])
                        if self.audio_callback:
                            self.audio_callback(audio_bytes)
                        logging.debug(f"Received audio chunk: {len(audio_bytes)} bytes (isFinal={data.get('isFinal')})")
                    except Exception as e:
                        logging.error(f"Failed to decode audio chunk: {e}")
                elif data.get("message_type") == "error":
                    logging.error(f"ElevenLabs error: {data}")
                else:
                    logging.debug(f"ElevenLabs metadata: {data}")
        except Exception as e:
            logging.error(f"Error listening for audio: {e}")
        finally:
            self.is_connected = False 