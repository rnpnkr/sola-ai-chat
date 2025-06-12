# Tech Context

# Very Important Don't Remove 
Command to start backend: uvicorn voice_assistant:app --reload

## Technologies Used
- Python 3.11+
- Frontend/Mobile: React Native (planned), React (for web prototype), HTML5 Canvas (for visualization)
- Backend/AI: FastAPI (web server), WebSockets (via FastAPI/uvicorn), Deepgram (STT), ElevenLabs (TTS), LangGraph (agent orchestration), Mem0 (memory), Supabase (vector DB for RAG), OpenRouter/OpenAI/Anthropic (LLMs), PyAudio (legacy audio interface)
- Additional Services: RevenueCat (planned), Sentry (planned), Analytics (planned)
- LangGraph (modular async pipeline)
- LangChain (LLM integration)
- ElevenLabs (WebSocket TTS streaming)
- Deepgram (STT)
- Modern HTML5/JS frontend

## Key Architectural Notes
- Modular pipeline: STT → LLM → TTS, each as async LangGraph node
- PersonalityAgent for persona-driven system prompt and response formatting
- Real-time WebSocket streaming for status, tokens, and audio
- Frontend supports real-time metrics, streaming text, and audio playback

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
- Backend: `fastapi`, `uvicorn`, `python-multipart`, `python-dotenv`, `pyaudio`, `elevenlabs`, `deepgram-sdk`, `langgraph`, `mem0ai`, `supabase`, `langchain`, `langchain-openai`, `pydantic`, `fastapi-utils`, `asyncpg`, `hashlib`, `time`
- Frontend: `react`, `react-dom`, `react-scripts`, Web Audio API (for visualization on web)
- langgraph>=0.2.0
- langchain>=0.3.0
- langchain-openai>=0.2.0
- pydantic>=2.0.0

## Recent Technical Updates (May 2024)
- Deepgram streaming STT: fixed race conditions by ensuring transcript callbacks are always executed using event-loop thread-safe scheduling (asyncio.run_coroutine_threadsafe).
- Transcript handoff: always pass last non-empty transcript to LangGraph; file-based STT fallback eliminated.
- ElevenLabs TTS: enabled optimize_streaming_latency=4 and chunk_size=512 for faster audio start, reducing TTS latency to <1s.
- Frontend: all timing metrics (STT, LLM, TTS, Total) now measured and displayed in ms, not seconds; timers reset per session.
- Backend: sends 'stt_processing' status at correct time for both streaming and file-based STT, ensuring frontend always measures STT time.
- WebSocket protocol: clarified event order for accurate frontend metrics.

## Recent Technical Updates (June 2024) - Performance & Stability
- **Resolved Critical Latency**: Implemented multiple fixes to reduce cold-start time-to-first-token from ~3.6s to <500ms.
  - **Active Conversation Gating**: The background subconscious processor now pauses when a user is in an active conversation, preventing resource contention. This is managed via a new `shared_state.py` module.
  - **Memory Search Caching**: Added a 30-second in-memory cache to `MemoryContextBuilder` to eliminate redundant memory API calls during a single turn.
  - **Intelligent Deduplication**: Enhanced the `MemoryCoordinator`'s hashing logic to include user and time-window context, preventing duplicate writes more effectively.
- Added Supabase authentication service (`auth_service.py`) for user sign-up, sign-in, and JWT verification.
- Integrated chat history storage and retrieval via `chat_service.py` and Supabase `chats` table.
- Launched modern, voice-first chat interface (`chat.html`) with real-time voice streaming, authentication modal, and chat history loading.
- Patched frontend to remove placeholder AI bubble creation; now the first `token_stream` creates the AI bubble, preventing duplicates.
- Backend WebSocket endpoint now authenticates users and passes `user_id` throughout the pipeline, fixing foreign key errors.
- Improved error handling and debug logging throughout the stack.

## Key Architectural Decisions & Learnings

### **1. Use Structured JSON for Inter-Service LLM Communication**
- **Problem**: Relying on prompt-based text parsing for communication between two services that both use LLMs (e.g., our `MemoryContextEnhancer` and Mem0's internal analysis) is fragile and error-prone.
- **Solution**: Enforce a strict JSON schema using the `response_format` parameter in the LLM call. The `MemoryContextEnhancer` now requests a specific JSON object, guaranteeing reliable, structured data for the downstream `MemoryCoordinator` and Mem0.
- **Principle**: When an LLM's output is machine-read, always use structured formats (JSON) over natural language.

### **2. Consolidate Semantic Searches for Efficiency and Quality**
- **Problem**: Performing many narrow, individual semantic searches (e.g., one for "joy," one for "pain," one for "trust") is slow, expensive, and misses overlapping context.
- **Solution**: We refactored our 8 separate background searches into 3 broad, psychologically-grounded queries: **Attachment, Vulnerability, and Growth**.
- **Result**: This reduced API calls by 62% and improved the quality of insights by capturing a richer, more holistic set of related memories in each search.

### **3. Decouple All Memory Writes from the Audio Pipeline**
- **Principle**: The user-facing audio experience should *never* be blocked by database or memory operations.
- **Implementation**: All memory storage operations (`conversation`, `scaffold_update`, `relationship_evolution`) are scheduled via the `MemoryCoordinator` as fire-and-forget async tasks. The coordinator handles batching, deduplication, and retries in the background. This ensures that even slow memory writes do not impact TTS latency.

### **4. Debounce and Deduplicate Streaming Inputs**
- **Problem**: Streaming STT services like Deepgram can emit multiple `is_final=true` or `speech_final=true` events for a single user utterance, causing duplicate AI responses.
- **Solution**: Implemented a simple deduplication cache (`last_processed_transcript`) in `voice_assistant.py`. The system now only processes a final transcript if it is non-empty and different from the last one processed for that client.
- **Result**: Guarantees a single AI reply per user utterance.

### **5. Guaranteeing Pipeline Resilience and State Integrity**
- **Principle**: A real-time voice application's state is its most vulnerable asset. It must be protected from race conditions and network instability at all costs.
- **Implementation**: We implemented a multi-layered defense to ensure stability:
  - **JS State Machine**: The frontend UI in `chat.html` is governed by a strict state machine (`IDLE`, `RECORDING`, `WAITING`, etc.). This eliminates an entire class of bugs caused by managing multiple, independent boolean flags.
  - **JS Playback Sessions**: To prevent audio events from an old, interrupted AI speech from corrupting a new recording session, each playback instance is a self-contained JavaScript object. "Orphaned" events from old sessions are automatically ignored.
  - **Python Idempotent Cleanup**: The backend `voice_assistant.py` features a centralized `_cleanup_client_session` function that can be called safely at any time. It robustly tears down all of a client's resources.
  - **Python Aggressive Timeouts**: To prevent the entire application from hanging on an unresponsive service, all potentially blocking network calls in the cleanup path (e.g., closing a WebSocket) are wrapped in an `asyncio.wait_for` with a short timeout, guaranteeing forward progress.
- **Result**: A highly stable, responsive conversational experience that does not require page refreshes, even after repeated, rapid interruptions.

## 2024-06: Ultra-Low-Latency LLM-to-TTS Streaming Upgrade

- **ElevenLabs WebSocket Streaming**: Now using the official ElevenLabs WebSocket API for TTS, sending LLM tokens as soon as they are generated. Each text chunk includes `try_trigger_generation: true` to force immediate audio generation.
- **Streaming Text Buffer**: LLM tokens are buffered and flushed to TTS at natural language boundaries for smooth, human-like speech.
- **Frontend Audio Chunk Handling**: The frontend now plays audio as soon as a chunk is received, using the Web Audio API. No need to wait for the full audio file.
- **No Duplicate Playback**: The backend no longer sends the full audio in the final result message; only streamed chunks are played.
- **Protocol Compliance**: The WebSocket handshake and message formats strictly follow the [official ElevenLabs documentation](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input).
- **Error Handling**: The backend waits for the server to close the WebSocket, ensuring all audio is received before cleanup.

## Mem0 & Supabase Integration Learnings
- **Database Connection**: Do not use the direct Supabase connection string. Use the **Transaction Pooler** connection string to avoid DNS resolution errors (`nodename nor servname provided, or not known`).
- **`mem0` Provider**: Do not use the `supabase` provider in the `mem0` config. It has a rigid schema. Instead, use the `pgvector` provider. This allows you to pass the database credentials (user, password, host, port, dbname) as separate components, which is necessary to correctly parse the Transaction Pooler connection string.
- **`mem0` Data Inconsistencies**: The `mem0.search()` method is not stable. It may return a list of strings, a list of dictionaries (correct), a single dictionary, or an empty list. The code must be written defensively to handle all of these cases to prevent `TypeError` and `KeyError` crashes. Always check the type of the result and normalize it into a list of dictionaries before processing.
- **`mem0` Configuration**: The `mem0.AsyncMemory` constructor requires a `MemoryConfig` object, not a plain dictionary. Failure to provide this results in a `pydantic_core.ValidationError`.

## Neo4j Graph Store (added June 2025)
- **Driver**: `neo4j-python-driver` pinned at `neo4j==5.20.0`.
- **Connection**: Bolt URI + basic auth loaded from `config.NEO4J_CONFIG`.
- **Schema Management**: `backend/subconscious/graph_schema.py` runs at startup to ensure uniqueness constraints on `User(id)` and `Memory(id)` and composite index on `(:User)-[:FEELS]->(:Emotion)`.
- **Usage**:
  - **Write**: `GraphRelationshipBuilder` creates `FEELS`, `DISCLOSED_TO`, `LEADS_TO` relationships asynchronously.
  - **Read**: `GraphQueryService` exposes `get_recent_emotional_context(user_id)` plus **TODO**: traversal helpers.
- **Fallback**: If Neo4j is unreachable the hybrid Mem0 config downgrades to vector-only mode; this is verified by integration tests.
- **Why Not Supabase Graph?**: Supabase Postgres lacks native graph traversal; we chose Neo4j for mature Cypher and scalability.
