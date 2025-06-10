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
        Establish WebSocket connection for streaming TTS with optimized settings
        """
        self.audio_callback = audio_callback
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_turbo_v2_5"
        try:
            self.websocket = await ws_connect(uri)
            self.is_connected = True
            config_message = {
                "xi_api_key": self.api_key,
                "text": " ",  # Must be single space, not empty string
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
            asyncio.create_task(self._listen_for_audio())
            logging.info("ElevenLabs WebSocket connected and configured with optimized settings")
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
        if not self.is_connected or not self.websocket:
            return
        try:
            flush_message = {"text": "", "flush": True}
            await self.websocket.send(json.dumps(flush_message))
            logging.debug("Sent flush message to ElevenLabs")
            await asyncio.sleep(0.5)
            await self.finish_streaming()
        except Exception as e:
            logging.error(f"Error during flush and finish: {e}")
            self.is_connected = False

    async def _listen_for_audio(self):
        try:
            while self.is_connected and self.websocket:
                msg = await self.websocket.recv()
                data = json.loads(msg)
                if "audio" in data:
                    is_final = data.get("isFinal", False)
                    audio_data = data["audio"]
                    if is_final:
                        logging.info(f"Received final message (audio generation complete)")
                        break  # Exit the while loop gracefully
                    elif audio_data is not None and audio_data != "":
                        try:
                            audio_bytes = base64.b64decode(audio_data)
                            if len(audio_bytes) > 0 and self.audio_callback:
                                self.audio_callback(audio_bytes)
                                logging.debug(f"Received audio chunk: {len(audio_bytes)} bytes")
                        except Exception as e:
                            logging.error(f"Failed to decode audio chunk: {e}")
                    else:
                        logging.debug(f"Received empty audio data (not final)")
        except Exception as e:
            logging.error(f"Error listening for audio: {e}")
            logging.error(f"Last received data: {json.dumps(data) if 'data' in locals() else 'No data'}")
        finally:
            self.is_connected = False 