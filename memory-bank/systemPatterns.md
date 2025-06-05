# System Patterns

## System Architecture
- Modular backend with agents (personalities), memory (Mem0), RAG (Self-RAG/Supabase), and crisis detection components.
- LangGraph orchestrator coordinates voice input, agent selection, memory retrieval, RAG, and crisis detection.
- Real-time, low-latency voice pipeline: Deepgram STT → LangGraph Agent → ElevenLabs TTS.
- Persistent memory and adaptive retrieval for multi-session continuity and therapeutic support.
- WebSocket-based real-time communication for state, memory, and safety events.

## Key Technical Decisions
- Use LangGraph for agent orchestration and workflow management.
- Integrate Mem0 for efficient, persistent memory and context retrieval.
- Use Supabase as the vector database for therapeutic knowledge and RAG.
- Implement agent personalities as modular classes with distinct traits and response logic.
- Add crisis detection and escalation as a core safety layer.
- Prioritize modularity, testability, and compliance in all new modules.

## Design Patterns in Use
- Orchestrator pattern (LangGraph) for managing multi-agent workflows.
- Strategy pattern for agent personality selection and response formatting.
- Adapter pattern for integrating Mem0 and Supabase with backend logic.
- Observer pattern for real-time WebSocket state and event updates.
- Asynchronous, event-driven communication throughout backend.
- Timer-based state inference for audio output (legacy, to be improved with new SDKs).

## Component Relationships
- Voice input (Deepgram) feeds into LangGraph orchestrator.
- Orchestrator selects agent personality, queries Mem0 for context, and triggers RAG if needed.
- Self-RAG retrieves therapeutic content from Supabase as required.
- Crisis detector monitors all messages and triggers escalation if risk detected.
- ElevenLabs TTS generates voice output for agent responses.
- WebSocket layer communicates all state, memory, and safety events to frontend clients. 