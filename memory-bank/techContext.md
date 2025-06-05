# Tech Context

## Technologies Used
- Frontend/Mobile: React Native (planned), React (for web prototype), HTML5 Canvas (for visualization)
- Backend/AI: FastAPI (web server), WebSockets (via FastAPI/uvicorn), Deepgram (STT), ElevenLabs (TTS), LangGraph (agent orchestration), Mem0 (memory), Supabase (vector DB for RAG), OpenRouter/OpenAI/Anthropic (LLMs), PyAudio (legacy audio interface)
- Additional Services: RevenueCat (planned), Sentry (planned), Analytics (planned)

## LangGraph Implementation Clarifications (Context7 MCP)
- Use `StateGraph` from `langgraph.graph` to define the pipeline state and nodes.
- Each node (STT, LLM, TTS) can be a function (sync or async) that receives the state and returns a dict with updated state keys.
- For streaming, use `stream_mode="messages"` to stream LLM tokens, `stream_mode="values"` for full state after each node, and `stream_mode="updates"` for incremental state changes.
- Use `graph.astream()` for async streaming (Python <3.11: pass `config` through node functions for context/callbacks).
- To stream custom data (e.g., audio chunks), use `get_stream_writer()` inside a node and emit data when `stream_mode="custom"` is set.
- Nodes can be chained sequentially or in parallel; edges define execution order.
- Integration with external services (Deepgram, ElevenLabs) is done inside node functions, which can be async and yield/emit data as needed.
- Metadata in streaming output includes the node name (`langgraph_node`) for filtering.
- Best practice: keep node return values as dicts matching the state schema; handle errors gracefully in each node.

## Development Setup
- Python backend dependencies managed with `pip` and `requirements.txt` (see PRD for new packages: langgraph, mem0ai, supabase, langchain, etc.).
- Node.js frontend dependencies managed with `npm` or `yarn`.
- Backend runs with `uvicorn`.
- Environment variables required for Mem0, Supabase, agent config, and RAG (see .env.example in PRD).
- Supabase database schema for therapeutic content and user sessions (see PRD).

## Technical Constraints
- Real-time, low-latency processing for voice and RAG (<150ms personality, <800ms RAG).
- Efficient, persistent memory management for multi-session context (Mem0 integration).
- Secure, encrypted storage and transmission of all user data (privacy and HIPAA compliance).
- Modular, testable backend structure (agents, memory, rag, crisis detection).
- WebSocket-based communication for all state, memory, and safety events.
- ElevenLabs Python SDK limitations for direct audio output tracking (legacy workaround, to be improved).

## Dependencies
- Backend: `fastapi`, `uvicorn`, `python-multipart`, `python-dotenv`, `pyaudio`, `elevenlabs`, `deepgram-sdk`, `langgraph`, `mem0ai`, `supabase`, `langchain`, `langchain-openai`, `pydantic`, `fastapi-utils`, `asyncpg`
- Frontend: `react`, `react-dom`, `react-scripts`, Web Audio API (for visualization on web)
