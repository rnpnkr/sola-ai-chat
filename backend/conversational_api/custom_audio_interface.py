from typing import Callable
import queue
import threading
import json
import base64
import asyncio
import time

import pyaudio # Assuming pyaudio is available in the environment

from elevenlabs.conversational_ai.conversation import AudioInterface

# Import the ConversationStateManager (will be defined in elevenlabs_service.py)
# from .elevenlabs_service import ConversationStateManager # This import will be added later if needed directly


class WaveformAudioInterface(AudioInterface):
    INPUT_FRAMES_PER_BUFFER = 4000  # 250ms @ 16kHz
    OUTPUT_FRAMES_PER_BUFFER = 1000  # 62.5ms @ 16kHz
    
    def __init__(self, state_manager=None):
        # Initialize exactly like DefaultAudioInterface 
        try:
            import pyaudio
        except ImportError:
            raise ImportError("To use WaveformAudioInterface you must install pyaudio.")
        self.pyaudio = pyaudio
        
        # + Store reference to state_manager for WebSocket access
        self.state_manager = state_manager

    def start(self, input_callback: Callable[[bytes], None]):
        # Audio input is using callbacks from pyaudio which we simply pass through.
        self.input_callback = input_callback

        # Audio output is buffered so we can handle interruptions.
        # Start a separate thread to handle writing to the output stream.
        self.output_queue: queue.Queue[bytes] = queue.Queue()
        self.should_stop = threading.Event()
        self.output_thread = threading.Thread(target=self._output_thread)

        self.p = self.pyaudio.PyAudio()
        self.in_stream = self.p.open(
            format=self.pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            stream_callback=self._in_callback,
            frames_per_buffer=self.INPUT_FRAMES_PER_BUFFER,
            start=True,
        )
        self.out_stream = self.p.open(
            format=self.pyaudio.paInt16,
            channels=1,
            rate=16000,
            output=True,
            frames_per_buffer=self.OUTPUT_FRAMES_PER_BUFFER,
            start=True,
        )

        self.output_thread.start()

    def stop(self):
        self.should_stop.set()
        self.output_thread.join()
        self.in_stream.stop_stream()
        self.in_stream.close()
        self.out_stream.close()
        self.p.terminate()

    def output(self, audio: bytes):
        # EXISTING: Add to queue for speaker playback (keep this!)
        self.output_queue.put(audio)

        # NEW: Also send audio data to frontend via WebSocket
        self._send_audio_to_frontend(audio)

    def interrupt(self):
        # Clear the output queue to stop any audio that is currently playing.
        # Note: We can't atomically clear the whole queue, but we are doing
        # it from the message handling thread so no new audio will be added
        # while we are clearing.
        try:
            while True:
                _ = self.output_queue.get(block=False)
        except queue.Empty:
            pass

    def _output_thread(self):
        while not self.should_stop.is_set():
            try:
                audio = self.output_queue.get(timeout=0.1)
                self.out_stream.write(audio)
            except queue.Empty:
                pass

    def _in_callback(self, in_data, frame_count, time_info, status):
        if self.input_callback:
            self.input_callback(in_data)
        return (None, self.pyaudio.paContinue)

    def _send_audio_to_frontend(self, audio_bytes: bytes):
        # Send via state_manager's send_audio_data method
        if self.state_manager and self.state_manager.websocket:
            try:
                asyncio.run_coroutine_threadsafe(
                    self.state_manager.send_audio_data(
                        audio_bytes,
                        {"sample_rate": 16000, "channels": 1, "bit_depth": 16}
                    ),
                    self.state_manager.loop
                )
            except Exception as e:
                # Handle WebSocket errors gracefully (don't break audio playback)
                print(f"Error sending audio data over websocket: {e}")
        # If no state_manager or websocket, silently fail (graceful degradation) 