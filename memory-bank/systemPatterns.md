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

## Modular Streaming Pipeline
- Uses LangGraph StateGraph for modular, async node orchestration (STT, LLM, TTS)
- Each node streams status, tokens, and audio via WebSocket
- Robust error handling and logging at each node

## Persona Agent Pattern
- PersonalityAgent class encapsulates persona config and response formatting
- System prompt and output formatting are persona-driven (e.g., mindfulness coach)
- Easily extensible for new personalities or response styles

## Real-Time WebSocket Streaming
- WebSocket protocol supports status, token, and audio streaming
- Frontend displays real-time progress, metrics, and audio playback

## Extensibility
- New nodes or personalities can be added with minimal changes to the pipeline

### Pattern: Memory Enhancement Pre-processing
- **Context**: The primary memory store's LLM (Mem0) may reject generic or simple conversational turns as "not containing new facts," leading to memory gaps.
- **Solution**: An intermediary service, `MemoryContextEnhancer`, uses a fast, cost-effective LLM to pre-process the conversation before storage. It enriches the text with context markers (e.g., `[RELATIONSHIP_CONCERN]`) and extracts explicit `MEMORY_FACTS` using a **structured JSON schema**.
- **Result**: Dramatically increases the likelihood of successful, meaningful storage in the main memory system and provides rich, queryable metadata.

### Pattern: Consolidated Psychological Search
- **Context**: Background analysis requires understanding multiple complex facets of the user's relationship with the AI. Making numerous, narrow, specific embedding searches is slow, expensive, and misses the bigger picture.
- **Solution**: Instead of searching for individual emotions or concepts (e.g., "joy," "trust," "pain"), group them into larger, psychologically-relevant themes. Our `PersistentSubconsciousProcessor` uses three core searches: **Attachment, Vulnerability, and Growth**.
- **Result**: Drastically reduces API calls (by 62% in our case) and processing time while providing a more holistic and contextually rich dataset for analysis.

### Pattern: Streaming Input Deduplication
- **Context**: Real-time STT services often emit multiple "final" transcript events for a single utterance, which can trigger duplicate processing and multiple AI replies.
- **Solution**: A simple deduplication cache (`last_processed_transcript` in `voice_assistant.py`) tracks the most recently processed final transcript for each client. Subsequent identical or empty final transcripts are ignored.
- **Result**: Guarantees that the AI pipeline is triggered exactly once per unique user utterance.

### Pattern: Database Connection Resilience (Supabase + pgvector)
- **Context**: Direct database connections, especially in containerized or serverless environments, can be unreliable due to DNS resolution issues (e.g., `nodename nor servname provided, or not known`). Furthermore, some libraries have strict configuration parsers that fail on complex connection strings.
- **Solution**: A two-part fix to ensure stable database connectivity for the `mem0` service.
  - **1. Use a Connection Pooler**: Switch from the direct database connection string to the **Transaction Pooler** string provided by Supabase. This resolves network-level DNS issues by providing a stable, proxied endpoint.
  - **2. Use the `pgvector` Provider**: The `mem0` library's `supabase` provider has a rigid configuration schema that does not allow for separate connection components. By switching the provider to `pgvector`, we can supply the connection details (user, password, host, port, dbname) as individual components. This bypasses faulty URL parsers in underlying libraries that are confused by the pooler's connection string format.
- **Result**: A highly resilient database connection that is robust to both network environment issues and library-specific configuration bugs.

### Pattern: Defensive Data Handling for External Libraries
- **Context**: An external library (`mem0`) was found to have an undocumented inconsistency, sometimes returning a single dictionary object instead of the documented list of objects, causing `KeyError` or `TypeError` exceptions.
- **Solution**: Instead of trusting the library's output implicitly, program defensively. Before processing the data, add a type check. If the data is in the unexpected format (a `dict`), manually wrap it in a `list` to normalize it to the expected format.
- **Result**: The application is now resilient to this specific library bug. This pattern of validating and normalizing the "shape" of data from external services prevents crashes and makes the system more robust.

## Recent System Patterns

### Supabase Authentication Integration
- **Context**: Need for secure, scalable user authentication and session management.
- **Solution**: Integrated Supabase Auth for user sign-up, sign-in, and JWT verification, with async FastAPI endpoints and middleware for token validation.
- **Result**: Robust, scalable authentication for all real-time and REST endpoints.

### Chat History Service
- **Context**: Users require persistent, session-based chat history across devices.
- **Solution**: Added `chat_service.py` to store/retrieve chats in Supabase, with endpoints for chat history and session management. Integrated with memory coordinator for parallel storage.
- **Result**: Reliable, scalable chat history with session grouping and metadata.

### Frontend Streaming Deduplication
- **Context**: Real-time streaming can create duplicate or empty AI chat bubbles if not carefully managed.
- **Solution**: Patched frontend to remove placeholder AI bubble creation; now the first `token_stream` event creates the AI bubble, ensuring no duplicates or empties.
- **Result**: Clean, modern chat UI with robust deduplication and streaming.

### Robust user_id Handling
- **Context**: Foreign key errors and data integrity issues can arise if user_id is not consistently passed through the stack.
- **Solution**: WebSocket and REST endpoints now authenticate and pass user_id throughout the pipeline, ensuring correct chat storage and retrieval.
- **Result**: Data integrity and correct user-specific chat/memory operations.

## 2024-06: System Pattern — True Streaming LLM-to-TTS

- **Pattern**: As soon as the LLM emits a token, it is buffered and sent to ElevenLabs WebSocket TTS. ElevenLabs streams back audio chunks, which are sent to the frontend and played immediately.
- **Key Components**:
  - `services/elevenlabs_websocket_service.py`: Handles WebSocket connection, text chunking, and audio chunk decoding.
  - `services/streaming_text_buffer.py`: Buffers and flushes LLM tokens at natural language boundaries.
  - `agents/langgraph_orchestrator.py`: The `llm_tts_streaming_node` streams both text and audio in real time.
  - `chat.html`: Plays audio chunks as soon as they arrive, using the Web Audio API.
- **No Duplicate Playback**: The backend omits the full audio in the final result message, so only streamed chunks are played.
- **Protocol**: All WebSocket messages and handshake steps follow the [official ElevenLabs API reference](https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input).
- **Error Handling**: The backend waits for the server to close the WebSocket, ensuring all audio is received before cleanup.

### Pattern: Voice Pipeline Resiliency
- **Context**: Real-time voice applications are highly susceptible to race conditions and network instability, especially during interruptions. A collection of boolean flags for state management is too brittle and often leads to hung states or corrupted sessions.
- **Solution**: A multi-layered approach to enforce stability.
  - **1. Frontend State Machine (`chat.html`)**: The entire voice UI is controlled by a single, formal state machine (`IDLE`, `RECORDING`, `WAITING`, `AI_SPEAKING`). All actions (user clicks, WebSocket messages) are simple transitions between these states. This eliminates entire classes of bugs related to out-of-sync boolean flags.
  - **2. Session-Based Audio Playback (`chat.html`)**: Each time the AI speaks, a new "playback session" object is created in JavaScript. This session manages its own audio context and buffer. Callbacks from audio events (like `onended`) will only affect the UI if their parent session is still the active one. This prevents events from old, interrupted sessions from corrupting a new, active session.
  - **3. Idempotent Backend Cleanup (`voice_assistant.py`)**: A single, robust `_cleanup_client_session` function is responsible for tearing down all of a user's resources (STT, TTS, etc.). It's designed to be safely callable from anywhere, at any time, without causing errors even if some resources are already gone. It is called at every critical boundary (interrupt, disconnect, new stream).
  - **4. Aggressive Timeouts (`voice_assistant.py`)**: All potentially hanging network calls within the session cleanup logic (e.g., waiting for a service to close a connection) are wrapped in an `asyncio.wait_for` with a short timeout. This guarantees that the backend can never get stuck on an unresponsive service, ensuring the user's session always remains active.
- **Result**: A highly reliable, responsive, and seamless voice conversation experience that can gracefully handle rapid, repeated user interruptions without freezing or requiring a page refresh.

### Pattern: Active Conversation Gating
- **Context**: A long-running background task (like the `PersistentSubconsciousProcessor`) can compete for CPU, network, and API resources with the main, user-facing real-time conversation loop. This resource contention was a primary cause of high latency on initial user interactions.
- **Solution**: Implement a centralized, global state to track active users.
  - **1. Shared State**: A new `shared_state.py` module holds a global `active_conversations: Set[str]`.
  - **2. Active/Inactive Marking**: The main WebSocket handler in `voice_assistant.py` adds a `user_id` to this set when a conversation's processing begins and removes it in a `finally` block, ensuring it is always cleaned up, even on error.
  - **3. Background Gating**: The `PersistentSubconsciousProcessor` checks if the `user_id` it is about to process is in the `active_conversations` set. If it is, the processor skips the current cycle and sleeps, effectively yielding to the real-time loop.
- **Result**: Eliminates resource competition between background and real-time processes, drastically reducing latency for the user-facing loop and ensuring a smooth conversational experience.

### Pattern: Time-Scoped In-Memory Caching
- **Context**: During a single, rapid conversational turn, multiple internal components might request the same data (e.g., memory search results for the current user message), leading to redundant and expensive API calls.
- **Solution**: Implement a simple, time-bound in-memory cache within the relevant service.
  - **Implementation**: The `MemoryContextBuilder` now holds a `search_cache` dictionary and a `cache_ttl` (Time-To-Live) of 30 seconds.
  - **Logic**: Before performing a memory search, it constructs a cache key from the `user_id` and the message content. If a valid (non-expired) entry exists in the cache, it returns the cached data immediately. Otherwise, it performs the search and stores the result in the cache with a timestamp.
- **Result**: Reduces API calls within a single conversational turn to one, significantly lowering both cost and latency. The short TTL ensures that context from the next conversational turn will trigger a fresh search.

### Pattern: Time-Windowed Deduplication Hashing
- **Context**: Simple content-based hashing for deduplication can be either too aggressive (preventing legitimate, similar conversations over time) or not aggressive enough (allowing rapid-fire duplicates from a buggy client or race condition).
- **Solution**: Enhance the content hash to include a time window.
  - **Implementation**: The `_generate_content_hash` method in `MemoryCoordinator` now includes `user_id` and a one-hour time window (`int(time.time() // 3600)`) in the string that gets hashed.
  - **Logic**: This creates a unique hash for the same conversation if it occurs in a different hour. A secondary check then ensures that even if the hash is identical, it's only rejected if it occurred within the last 10 minutes.
- **Result**: A more nuanced deduplication strategy that prevents transient duplicate writes without blocking legitimate user behavior over the long term.

### Pattern: Hybrid Vector + Graph Memory
- **Context**: Vector similarity provides topical relevance but misses relational context (trust, emotional cascades).
- **Solution**: Use Mem0 v1.1 hybrid mode with a **pgvector** vector store *and* a **Neo4j** graph store. Vector search retrieves content, graph traversal supplies relationship intelligence.
- **Implementation**: `mem0_async_service.py` config includes `graph_store`. `GraphQueryService` reads, `GraphRelationshipBuilder` writes relationships. Background processor populates graph asynchronously to avoid latency on the real-time loop.
- **Benefit**: The AI can reason over emotional relationships, trust progression, and support patterns while preserving fast semantic recall.

### Pattern: Deepgram Final-Transcript Filtering (June 2025)
- **Context**: Deepgram occasionally emits a second `is_final` transcript event with an **empty** `transcript` field right after the real final message, causing `_process_pending_events` to see two transcripts and triggering duplicate downstream processing.
- **Solution**: `DeepgramStreamingService.handle_transcript_event()` now drops empty finals and consecutive duplicates before adding them to the pending queue.
- **Result**: Exactly one meaningful transcript per utterance; eliminates duplicate AI replies and reduces log noise. 