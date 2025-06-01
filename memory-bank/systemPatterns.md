# System Patterns

## System Architecture
- Client-server architecture with a React frontend and a FastAPI Python backend.

## Key Technical Decisions
- Voice-first interaction design.
- Use of advanced memory management (`mem0`) (planned).
- Integration of multiple LLMs (`OpenAI/Anthropic`) (planned).
- Vector database for RAG (`Pinecone/Weaviate`) (planned).
- **Real-time conversation state communication via WebSockets.**

## Design Patterns in Use
- **State Management:** Backend (`ConversationStateManager`) tracks conversation state (IDLE, SPEAKING, LISTENING, THINKING) and sends updates to the frontend via WebSocket.
- **Timer-based State Inference:** A workaround pattern in the backend to estimate states (especially SPEAKING duration) due to ElevenLabs Python SDK limitations.
- Asynchronous communication patterns (using `asyncio` and `threading` to bridge synchronous SDK callbacks with the async web server).
- Component patterns in frontend for audio analysis and visualization (`AudioVisualizer`, `AudioAnalyzer`, `WaveformCanvas`).

## Component Relationships
- Frontend (React) communicates with Backend (FastAPI).
- **WebSocket connection (`/ws`) is used for real-time state updates from Backend to Frontend.**
- Backend integrates Eleven Labs (voice), and will integrate mem0, Supabase, LLMs, Vector DBs (planned).
- Frontend includes components for audio visualization driven by backend state.
- Additional services like RevenueCat, Sentry, Analytics are integrated with frontend/backend as needed (planned). 