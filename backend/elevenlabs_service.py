import os
import signal
import json
import asyncio
import time
import re
from threading import Timer
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Load environment variables once
load_dotenv()

# --- ConversationStateManager class ---
class ConversationStateManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.current_state = "IDLE"
        self.websocket = None
        self.loop = loop
        self.last_agent_response_time = None
        self.last_user_speech_time = None
        self.speaking_timer: Timer | None = None
        self.thinking_timer: Timer | None = None
        self.thinking_timeout = 2.0  # seconds after user speech before THINKING
        print("🔄 State: IDLE - Waiting for conversation start")

    async def set_websocket(self, websocket):
        """Sets the active websocket connection and sends initial state."""
        self.websocket = websocket
        await self.send_state_update()

    async def send_state_update(self):
        """Sends the current state over the websocket if available."""
        if self.websocket:
            try:
                await self.websocket.send_text(json.dumps({"state": self.current_state}))
            except Exception as e:
                print(f"Error sending state over websocket: {e}")
                self.websocket = None

    def _schedule_state_update(self):
        """Helper to schedule async state update from synchronous context."""
        if self.loop and self.loop.is_running() and self.websocket:
            try:
                asyncio.run_coroutine_threadsafe(self.send_state_update(), self.loop)
            except Exception as e:
                print(f"Error scheduling state update: {e}")

    def _cancel_timers(self):
        """Cancel any active timers"""
        if self.speaking_timer and self.speaking_timer.is_alive():
            self.speaking_timer.cancel()
            self.speaking_timer = None
        if self.thinking_timer and self.thinking_timer.is_alive():
            self.thinking_timer.cancel()
            self.thinking_timer = None

    def _estimate_speaking_duration(self, text: str) -> float:
        """Estimate how long it takes to speak the given text"""
        words = len(re.findall(r'\b\w+\b', text))
        # Average speaking rate: ~150 words per minute (2.5 words per second)
        # Add buffer for processing and pauses
        estimated_duration = (words / 2.5) + 0.5  # Reduced buffer
        # Minimum duration of 1 second, maximum of 20 seconds
        return max(1.0, min(estimated_duration, 20.0))

    def _transition_to_idle(self):
        """Called when estimated speaking time is over"""
        if self.current_state == "SPEAKING":
            self.current_state = "IDLE"
            print("🔄 State: IDLE - Agent finished speaking")
            self._schedule_state_update()

    def _transition_to_thinking(self):
        """Called after user speech timeout"""
        if self.current_state == "LISTENING":
            self.current_state = "THINKING"
            print("🧠 State: THINKING - Processing user input")
            self._schedule_state_update()

    def on_agent_response(self, response):
        """Called when agent starts responding with text"""
        self._cancel_timers()

        self.current_state = "SPEAKING"
        self.last_agent_response_time = time.time()
        print("🗣️  State: SPEAKING - Agent responding")
        self._schedule_state_update()
        print(f"Agent: {response}")

        speaking_duration = self._estimate_speaking_duration(response)
        print(f"📏 Estimated speaking duration: {speaking_duration:.1f}s")

        self.speaking_timer = Timer(speaking_duration, self._transition_to_idle)
        self.speaking_timer.daemon = True
        self.speaking_timer.start()

    def on_agent_response_correction(self, original, corrected):
        """Called when agent corrects its response"""
        print(f"Agent: {original} -> {corrected}")
        if self.speaking_timer and self.speaking_timer.is_alive():
            self.speaking_timer.cancel()

        speaking_duration = self._estimate_speaking_duration(corrected)
        print(f"📏 Estimated speaking duration (corrected): {speaking_duration:.1f}s")
        self.speaking_timer = Timer(speaking_duration, self._transition_to_idle)
        self.speaking_timer.daemon = True
        self.speaking_timer.start()

    def on_user_transcript(self, transcript):
        """Called when user speech is detected and transcribed"""
        self._cancel_timers()

        self.current_state = "LISTENING"
        self.last_user_speech_time = time.time()
        print("👂 State: LISTENING - User speech detected")
        self._schedule_state_update()
        print(f"User: {transcript}")

        self.thinking_timer = Timer(self.thinking_timeout, self._transition_to_thinking)
        self.thinking_timer.daemon = True
        self.thinking_timer.start()

    def on_latency_measurement(self, latency):
        """Called for latency measurements - not used for state tracking"""
        pass

    def on_session_end(self):
        """Called when conversation session ends"""
        self._cancel_timers()
        self.current_state = "IDLE"
        print("🔄 State: IDLE - Conversation session ended")
        self._schedule_state_update()

# --- Function to initialize ElevenLabs components ---
def create_conversation_components(loop: asyncio.AbstractEventLoop):
    agent_id = os.getenv("AGENT_ID")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not agent_id:
        print("Error: AGENT_ID environment variable not set.")
        return None, None, None

    elevenlabs_client = ElevenLabs(api_key=api_key)
    state_manager = ConversationStateManager(loop=loop)

    # Use DefaultAudioInterface to restore audio functionality
    audio_interface = DefaultAudioInterface()

    # The callbacks are set to the methods in the state_manager instance
    # State transitions are now managed by the ConversationStateManager's timer logic
    conversation_instance = Conversation(
        elevenlabs_client,
        agent_id,
        requires_auth=bool(api_key),
        audio_interface=audio_interface,
        callback_agent_response=state_manager.on_agent_response,
        callback_agent_response_correction=state_manager.on_agent_response_correction,
        callback_user_transcript=state_manager.on_user_transcript,
        callback_latency_measurement=state_manager.on_latency_measurement,
    )

    return elevenlabs_client, state_manager, conversation_instance

# Removed the direct script execution part