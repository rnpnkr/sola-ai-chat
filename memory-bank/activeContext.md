# Active Context

## Current Work Focus
- Implementing backend-frontend communication for conversation state and waveform visualization.

## Recent Changes
- Refactored `backend/elevenlabs_service.py` to be importable and added timer-based state tracking logic.
- Introduced FastAPI (`backend/main.py`) to serve as a web server and manage WebSocket connections.
- Implemented a WebSocket endpoint (`/ws`) in the backend to send conversation state updates.
- Created an initial React frontend application structure in the `frontend/` directory.
- Moved frontend waveform visualization components (`AudioAnalyzer.js`, `WaveformCanvas.jsx`, `AudioVisualizer.jsx`) to `frontend/src/components/`.
- Modified `frontend/src/App.js` to connect to the backend WebSocket and update the `isAgentSpeaking` state based on received messages.
- Addressed backend import errors and ensured the ElevenLabs conversation runs in a separate thread within FastAPI.
- Implemented a custom audio interface (`backend/custom_audio_interface.py - WaveformAudioInterface`) to stream raw audio data from the ElevenLabs output to the frontend via WebSocket.

## Next Steps
- Refine frontend state handling to utilize all conversation states (LISTENING, THINKING, IDLE).
- Potentially implement audio streaming from the backend to the frontend for real-time waveform visualization based on actual audio data.
- Continue working on frontend implementation of real-time waveform visualization using the streamed audio data.
- Continue building other features outlined in `TASK.md`.

## Active Decisions and Considerations
- Using FastAPI and WebSockets for backend-frontend communication.
- Employing timer-based state estimation in the backend (`ConversationStateManager`) as a workaround due to the ElevenLabs Python SDK lacking a direct `onModeChange` callback.
- Running the potentially blocking ElevenLabs conversation session in a separate thread within the FastAPI application to avoid blocking the main event loop.
- Current frontend waveform visualization uses a placeholder audio element and is triggered by the backend's estimated SPEAKING state.
- Implemented `WaveformAudioInterface` to intercept ElevenLabs audio output and send it to the frontend for visualization.
- Backend streams raw 16-bit 16kHz mono PCM audio data, Base64 encoded, over WebSocket during the SPEAKING state. 