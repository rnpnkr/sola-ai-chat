import os
from typing import Callable, AsyncGenerator
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import asyncio

class ElevenLabsStreamingService:
    """
    Service for streaming text-to-speech audio from ElevenLabs using their SDK.
    """
    def __init__(self, api_key: str = None, voice_id: str = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "bIHbv24MWmeRgasZH58o")
        self.elevenlabs = ElevenLabs(api_key=self.api_key)

    async def stream_tts(self, text: str, audio_callback: Callable[[bytes], None],
                        output_format: str = "mp3_22050_32", model_id: str = "eleven_turbo_v2_5"):
        """
        Streams TTS audio for the given text, calling audio_callback for each audio chunk.
        Args:
            text (str): The text to convert to speech.
            audio_callback (Callable[[bytes], None]): Function to call with each audio chunk.
            output_format (str): Audio output format (default mp3_22050_32).
            model_id (str): ElevenLabs model to use (default turbo).
        """
        # ElevenLabs SDK is sync, so run in thread executor
        def _stream():
            response = self.elevenlabs.text_to_speech.stream(
                voice_id=self.voice_id,
                output_format=output_format,
                text=text,
                model_id=model_id,
                voice_settings=VoiceSettings(
                    stability=0.0,
                    similarity_boost=1.0,
                    style=0.0,
                    use_speaker_boost=True,
                    speed=1.0,
                ),
            )
            for chunk in response:
                if chunk:
                    audio_callback(chunk)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _stream) 