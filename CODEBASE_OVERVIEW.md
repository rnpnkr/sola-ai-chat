# Sola AI Companion: Backend Technical PRD & Codebase Overview

## 1. Vision & High-Level Architecture

### 1.1. Project Vision

To create a deeply empathetic and emotionally intelligent AI voice companion that builds a genuine, long-term relationship with the user. The system is designed around a "human-like" cognitive architecture, featuring a real-time "conscious" processing stream and a persistent "subconscious" layer for background analysis and relationship modeling. The agents purpose is to be an intimate companion to humans tailored in solving the loneliness Epidemic in america

### 1.2. System Architecture

The backend operates on two distinct but interconnected loops: a low-latency **Real-time Conversation Loop** for immediate interaction and an asynchronous **Subconscious Analysis Loop** for deeper relationship processing.

```mermaid
graph TD
    subgraph Real-time Conversation Loop (< 2s)
        A[User Voice via WebSocket] --> B[Deepgram STT];
        B --> C{LangGraph Orchestrator};
        C -->|Transcript| D[Personality & Prompt Agent];
        D --> E[Intimacy Scaffold Manager];
        E -->|Cached Psychological Profile (<150ms)| D;
        D --> F[AI Service (LLM)];
        F -->|AI Response Text| G[ElevenLabs TTS];
        G --> H[Audio Stream to User];
        C -->|Conversation Data| I(Memory Context Enhancer);
    end

    subgraph Asynchronous Backend Processes
        I --> J(Memory Coordinator);
        J -->|Batch & Store| K[Mem0 & Supabase Vector Store];

        subgraph Subconscious Analysis Loop (Every 3 mins)
            L[Background Processor] -->|3 Psychological Searches| K;
            K -->|Memory Sets| L;
            L -->|Synthesized Analysis| M[Intimacy Scaffold Manager];
            M -->|Update In-Memory Cache| E;
            M -->|Store Evolution| J;
        end
    end

    style I fill:#f9f,stroke:#333,stroke-width:2px
    style J fill:#f9f,stroke:#333,stroke-width:2px
    style L fill:#ccf,stroke:#333,stroke-width:2px
    style M fill:#ccf,stroke:#333,stroke-width:2px
```

---

## 2. Core Workflows

### 2.1. Real-time Conversation Workflow
1.  **Voice Input**: The user streams audio via a WebSocket connection handled by `voice_assistant.py`.
2.  **Transcription**: `DeepgramStreamingService` transcribes the audio in real-time. Upon receiving a final, non-empty transcript, it triggers the main pipeline. A deduplication mechanism prevents multiple triggers for the same utterance.
3.  **Orchestration**: `langgraph_orchestrator.py` receives the transcript.
4.  **Context Retrieval**: The orchestrator fetches the user's latest psychological profile from the `IntimacyScaffoldManager` cache. This is a sub-150ms operation.
5.  **Prompt Engineering**: `PersonalityAgent` combines the transcript, the psychological profile, and the base personality into a rich prompt for the LLM.
6.  **LLM Inference**: `OpenRouterService` streams the response from the selected language model.
7.  **Text-to-Speech**: `ElevenLabsStreamingService` converts the generated text into an audio stream.
8.  **Voice Output**: The audio is streamed back to the user via the WebSocket.
9.  **Memory Enhancement**: Concurrently, the conversation text is sent to the `MemoryContextEnhancer`.

### 2.2. Memory Storage Workflow (Asynchronous)
1.  **Context Enrichement**: The `MemoryContextEnhancer` receives the raw conversation. It uses a separate, cost-effective LLM (via OpenRouter) to analyze the text. It enforces a **structured JSON output** to add contextual tags (e.g., `[RELATIONSHIP_CONCERN]`) and extract a list of key "facts". This prevents memory rejection by the downstream service.
2.  **Coordinated Storage**: The enriched memory object is passed to the `MemoryCoordinator`.
3.  **Non-Blocking Writes**: The `MemoryCoordinator` acts as a central, non-blocking queue. It batches operations, retries failures, and ensures that memory writes *never* block the real-time conversation loop. It schedules the memory to be written to the `mem0` service.

### 2.3. Subconscious Analysis Workflow (Background Loop)
1.  **Scheduled Trigger**: `BackgroundServiceManager` ensures that `PersistentSubconsciousProcessor.continuous_relationship_analysis` runs for each active user every 3 minutes.
2.  **Consolidated Psychological Search**: The processor performs **three broad, psychologically-grounded semantic searches** against the `mem0` memory store:
    *   Attachment & Safety Seeking
    *   Vulnerability & Intimate Disclosure
    *   Relationship Evolution & Growth
3.  **Synthesis**: The results from these three searches are synthesized into a single, comprehensive psychological profile.
4.  **Cache Update (Cache-Aware)**: The new profile is sent to the `IntimacyScaffoldManager`. Crucially, the background processor **will not overwrite** the cache if the existing cache data is "fresh" (less than 2 minutes old), protecting real-time insights from being clobbered during an active conversation.
5.  **Store Evolution**: A summary of the analysis is also stored back in `mem0` via the `MemoryCoordinator` to track the relationship's evolution over time.

---

## 3. File-by-File Component Breakdown

### 3.1. Main Entrypoints & Configuration

-   **`backend/voice_assistant.py`**
    -   **Purpose**: The main entry point for the application. Manages the FastAPI server and WebSocket connections.
    -   **Key Components**:
        -   `app = FastAPI()`: The FastAPI application instance.
        -   `@app.websocket("/ws/{client_id}")`: The primary endpoint for handling all real-time bidirectional communication with clients.
        -   `VoiceAssistantWebSocket`: A class that encapsulates the logic for handling different message types (audio streams, control messages) and orchestrating the services for a given client session.
        -   `@app.get("/health")`, `@app.get("/graph")`, `@app.get("/memory-stats")`, `@app.get("/cache-freshness/{user_id}")`: Administrative endpoints for system monitoring.

-   **`backend/config.py`**
    -   **Purpose**: Centralized configuration management. Loads all necessary API keys, model names, and settings from environment variables (`.env` file).
    -   **Key Components**: Exposes configuration dictionaries like `DEEPGRAM_CONFIG`, `ELEVENLABS_CONFIG`, and `OPENROUTER_CONFIG`.

#### Global **Service Registry** (June 2025)

To eliminate duplicate initialisations and enable clean startup/shutdown of expensive resources (AsyncMemory, Neo4j Driver, streaming clients), the backend now boots a **singleton service registry**:

* **`backend/services/service_registry.py`** – Lazily constructs and caches core services (`IntimateMemoryService`, `GraphQueryService`, background managers).  All modules now retrieve shared resources via `ServiceRegistry.get_*()` helpers instead of instantiating their own copies.

Key benefits:
1. **Predictable resource usage** – only one AsyncMemory object and one Neo4j driver per Python process.
2. **Massive latency reduction** – removes 500-1000 ms cold-start hit per request that previously came from repeated `AsyncMemory` initialisation.
3. **Centralised cleanup** – FastAPI startup/shutdown events call `ServiceRegistry.init_all()` / `ServiceRegistry.close_all()` to release connections gracefully.

Affected files: every direct constructor call (`IntimateMemoryService()`, `GraphQueryService()`, etc.) was replaced with the registry getter.  See `memory_context_builder.py` and `memory_coordinator.py` for typical usage.

### 3.2. Core Services (`backend/services/`)

-   **`ai_service.py` (`OpenRouterService`)**
    -   **Purpose**: Handles all interactions with the language model via the OpenRouter API.
    -   **Key Functions**:
        -   `get_streaming_response()`: Sends a prompt and streams the response back chunk by chunk. Used for real-time conversation.
        -   `get_response()`: A non-streaming version for simpler requests.

-   **`deepgram_streaming_service.py` (`DeepgramStreamingService`)**
    -   **Purpose**: Manages the persistent WebSocket connection to Deepgram for real-time, low-latency speech-to-text.
    -   **Key Functions**:
        -   `start()`: Initializes the connection to Deepgram with specified encoding and model parameters.
        -   `send()`: Forwards raw audio chunks from the client to Deepgram.
        -   `finish()`: Gracefully closes the Deepgram stream. It handles transcript processing, including deduplication of final transcripts.

-   **`elevenlabs_streaming.py` (`ElevenLabsStreamingService`)**
    -   **Purpose**: Handles streaming Text-to-Speech synthesis from ElevenLabs.
    -   **Key Functions**:
        -   `stream_audio()`: Takes an async generator of text chunks and yields audio chunks, allowing for very low "time-to-first-sound".

-   **`memory_context_enhancer.py` (`MemoryContextEnhancer`)**
    -   **Purpose**: A critical pre-processing service that enriches raw conversation text before it's stored in memory. This solves the problem of `mem0` rejecting memories that lack "facts."
    -   **Key Functions**:
        -   `enhance_context_with_llm()`: Takes conversation text, calls a separate LLM (configured for structured JSON output), and returns a dictionary containing contextual tags, emotional analysis, and extracted facts.

-   **`memory_coordinator.py` (`MemoryCoordinator`)**
    -   **Purpose**: A singleton service that acts as the central, non-blocking gateway for all memory operations. It decouples the real-time pipeline from the latency of database writes.
    -   **Key Functions**:
        -   `schedule_memory_operation()`: The primary entry point. Adds a memory operation (like storing a conversation or updating the scaffold) to a queue.
        -   `_process_memory_queue()`: The background worker that processes the queue, handling batching, retries with exponential backoff, and robust error logging.

-   **`background_service_manager.py` (`background_service_manager`)**
    -   **Purpose**: Manages the lifecycle of long-running background tasks, specifically the subconscious processor for each user.
    -   **Key Functions**:
        -   `start_background_services_for_user()`: Starts the `PersistentSubconsciousProcessor` loop for a given user.
        -   `stop_background_services_for_user()`: Stops the loop when a user disconnects.

-   **`memory_health_monitor.py` (`MemoryHealthMonitor`)**
    -   **Purpose**: Provides an observable endpoint to check the health and status of the memory system.
    -   **Key Functions**:
        -   `get_health_report()`: Called by the `/health/memory` endpoint to return statistics from the `MemoryCoordinator` and `mem0` service.

### 3.3. Agents (`backend/agents/`)

-   **`langgraph_orchestrator.py`**
    -   **Purpose**: Defines and executes the main conversational AI pipeline using LangGraph.
    -   **Key Components**:
        -   `ConversationState`: A TypedDict that defines the data structure (graph state) that flows through the pipeline.
        -   `llm_node`: The core node that retrieves the intimacy scaffold, constructs the final prompt, and calls the `OpenRouterService`.
        -   `langgraph_pipeline`: The compiled LangGraph object that defines the conversation flow.

-   **`personality_agent.py` (`PersonalityAgent`)**
    -   **Purpose**: Encapsulates the AI's core personality, system prompt, and response formatting rules.
    -   **Key Components**:
        -   `system_prompt`: The base prompt that defines the AI's character, goals, and conversational style.
        -   `construct_subconscious_prompt()`: Dynamically injects the real-time psychological profile from the `IntimacyScaffold` into the system prompt.

### 3.4. Memory (`backend/memory/`)

-   **`mem0_async_service.py` (`IntimateMemoryService`)**
    -   **Purpose**: An async wrapper around the `Mem0` client, tailored for the application's needs.
    -   **Key Functions**:
        -   `store_conversation_memory()`: Adds a new conversation turn to the memory.
        -   `search_intimate_memories()`: Performs semantic search over the user's memory. Used heavily by the `PersistentSubconsciousProcessor`.

-   **`memory_context_builder.py` (`MemoryContextBuilder`)**
    -   **Purpose**: A dedicated service responsible for querying the memory system and formatting the results into a rich, structured context string that the LLM can easily understand and use.
    -   **Key Functions**:
        -   `build_intimate_context()`: The core method. It searches for relevant memories and then formats them with clear instructions (e.g., "IMPORTANT CONTEXT - What you remember...") to guide the LLM's response.

-   **`conversation_memory_manager.py`**
    -   **Purpose**: A higher-level manager (now largely superseded by `MemoryCoordinator`) for handling conversation storage logic.

### 3.5. Subconscious (`backend/subconscious/`)

-   **`background_processor.py` (`PersistentSubconsciousProcessor`)**
    -   **Purpose**: The heart of the AI's long-term learning. Runs a continuous background loop to analyze the user relationship.
    -   **Key Functions**:
        -   `_continuous_relationship_analysis()`: The main loop that, every 3 minutes, runs the three core psychological searches.
        -   `_synthesize_psychological_analysis()`: Merges the findings from the searches into a single, structured insight.
        -   `_store_relationship_evolution()`: Stores the new insight and updates the `IntimacyScaffoldManager` cache in a **cache-aware** manner.

-   **`intimacy_scaffold.py` (`IntimacyScaffoldManager`, `IntimacyScaffold`)**
    -   **Purpose**: Manages the in-memory cache of the user's latest psychological profile, ensuring sub-150ms access for the real-time loop.
    -   **Key Components**:
        -   `IntimacyScaffold` (Dataclass): A structured object holding the complete, real-time psychological profile of the user (e.g., `emotional_undercurrent`, `relationship_depth`, `intimacy_score`).
        -   `IntimacyScaffoldManager`: A singleton that holds the `scaffold_cache` (`{user_id: {"scaffold": ..., "timestamp": ...}}`).
        -   `get_intimacy_scaffold()`: The main read function. Returns a fresh scaffold from cache or builds one from `mem0` if the cache is stale.
        -   `update_scaffold_cache()`: Updates the cache with new data from the background processor.
        -   `get_cache_freshness_info()`: A debug method to inspect the freshness of the cache via the API.

-   **`relationship_insights.py`, `memory_analytics.py`, etc.**
    -   **Purpose**: These modules contain the logic for Phase 5 (Deep Connection Analytics). They are designed to run analyses on the stored psychological data to generate timelines, health metrics, and other insights, which can be exposed via API endpoints.

- **Middleware**
  - `auth_middleware.py` provides async dependency for extracting and verifying the current user from JWT.

- **Memory System Hardening (June 2024)**
  - **Goal**: To debug and resolve a series of cascading failures in the memory system, ensuring reliable and context-aware AI responses.
  - **Problem**: The AI was failing to recall user information (like their name) because of a chain of errors, from database connection failures to inconsistent data formats returned by the `mem0` library.
  - **Solutions Implemented**:
    - **Database Connection Fix**: Switched from a direct Supabase connection to the **Transaction Pooler** connection string to resolve DNS lookup errors in a containerized environment. Reconfigured the `mem0` vector store provider from `supabase` to `pgvector` to allow for component-based connection details, bypassing a critical URL parsing bug.
    - **Defensive Programming against `mem0` Bugs**: Implemented robust checks in `IntimateMemoryService` and `IntimacyScaffoldManager` to handle inconsistent return types from the `mem0.search()` method. The code now gracefully handles both lists (correct) and single dictionaries (incorrect), preventing crashes.
    - **Robust Context Formatting**: Overhauled the `MemoryContextBuilder` to ensure that retrieved memories are always correctly extracted and formatted into a clear, instructive prompt for the LLM. Added detailed debug logging to trace the entire context-building pipeline.
    - **Comprehensive Error Handling**: Added detailed `exc_info=True` logging to all critical failure points in the memory pipeline, enabling faster diagnosis of future issues.

- **Endpoints**
  - `/auth/signup`, `/auth/signin` for authentication.
  - `/chats`, `/chat-sessions`, `/chats/{session_id}` for chat history and session retrieval.

### 3.6. Recent Additions & Improvements

* **Scalability Sprint (June 2025)** – Implemented Service Registry, Memory-system singleton, Neo4j driver pooling, user-isolated caches, and background-service health monitoring.  These changes together reduced average memory-retrieval latency from ~1.6 s to <300 ms and raised tested concurrent-user capacity from 3 to 40 users without errors.

* Supabase Authentication Service (`auth_service.py`)
  - Handles user sign-up, sign-in, and JWT verification using Supabase.
  - Provides async methods for registration, login, and token validation.
  - Integrated with FastAPI endpoints for `/auth/signup` and `/auth/signin`.
  - Used in WebSocket and REST endpoints for user authentication.

- **Chat Service (`chat_service.py`)**
  - Stores and retrieves chat history in the Supabase `chats` table.
  - Supports storing user/AI messages, session grouping, and metadata.
  - Provides endpoints for fetching user chat history and sessions.
  - Integrated with the memory coordinator for parallel chat and memory storage.

- **Frontend Chat Interface (`chat.html`)**
  - Modern, dark-themed, voice-first chat UI with chat bubbles and a single voice button (no text input).
  - Real-time voice streaming via WebSocket, with live transcription and AI response streaming.
  - Authentication modal for login, logout, and error display.
  - Loads chat history after login and deduplicates messages.
  - Improved button feedback, error handling, and message deduplication.

- **Voice Pipeline Stability & Interruption Overhaul**
  - **Goal**: To eliminate bugs related to interruptions, race conditions, and hung states, ensuring a seamless and reliable voice conversation.
  - **Frontend (`chat.html`)**:
    - Replaced a collection of brittle boolean flags with a formal **State Machine** (`IDLE`, `RECORDING`, `WAITING`, `AI_SPEAKING`) to manage UI state predictably.
    - Implemented **session-based audio playback** to isolate audio contexts. This prevents race conditions where events from a previous, interrupted AI speech could corrupt the state of a new recording.
    - The UI now provides immediate feedback ("Sola is thinking...") instead of freezing, dramatically improving perceived latency.
  - **Backend (`voice_assistant.py`)**:
    - Introduced a centralized and idempotent **`_cleanup_client_session` function** to robustly tear down all user session resources (STT, TTS, audio buffers) at every critical boundary (interruption, disconnect, new stream start).
    - Hardened the stream completion logic by adding aggressive **`asyncio` timeouts** to all STT connection closures. This guarantees the backend can never hang due to an unresponsive service, a critical fix for the "stuck in thinking" bug.

- **Backend Integration**
  - WebSocket endpoint now authenticates users via Supabase JWT and passes `user_id` throughout the pipeline.
  - Chat storage and retrieval use the correct `user_id`, fixing foreign key errors.
  - `MemoryCoordinator` updated to store both chat and memory in parallel, with robust deduplication and batching.
  - All Supabase credentials are loaded from `config.py` for consistency.

- **Middleware**
  - `auth_middleware.py` provides async dependency for extracting and verifying the current user from JWT.

- **Endpoints**
  - `/auth/signup`, `/auth/signin` for authentication.
  - `/chats`, `/chat-sessions`, `/chats/{session_id}` for chat history and session retrieval.
  - `/chat` serves the new chat.html interface.

- **Additional Fixes**
  - Improved error handling and debug logging throughout the stack.
  - Patched frontend to remove placeholder AI bubble creation; now the first `token_stream` creates the AI bubble.
  - Ensured no duplicate or empty AI bubbles are created during streaming.

- **Critical Latency & Performance Optimization (June 2024)**
  - **Goal**: To resolve a severe latency issue (~3.6s time-to-first-token on cold start) caused by memory system inefficiencies.
  - **Problem**: Log analysis revealed excessive and redundant memory API calls, and resource contention between the real-time and background processing loops.
  - **Solutions Implemented**:
    - **Active Conversation Gating**: The background `PersistentSubconsciousProcessor` now pauses its analysis if the target user is in an active, real-time conversation. This is managed by a global `active_conversations` set in a new `shared_state.py` module, which is updated by the `VoiceAssistantWebSocket` handler. This eliminates resource competition.
    - **Memory Search Caching**: The `MemoryContextBuilder` now uses a 30-second in-memory cache to deduplicate identical memory search requests that occur within the same conversation turn, dramatically reducing redundant embedding API calls.
    - **Robust Conversation Deduplication**: The `MemoryCoordinator` now uses a more robust content hashing mechanism that includes the `user_id` and a 1-hour time window. This prevents transient duplicate processing while still allowing users to have similar conversations over time. It will skip storing a conversation if an identical one from the same user was processed in the last 10 minutes.

### 3.7. Ultra-Low-Latency LLM-to-TTS Streaming (2024-06 Update)

#### Overview

The system now supports **true streaming from LLM to TTS**, enabling audio playback to begin as soon as the LLM starts responding, not after it finishes. This is achieved by streaming LLM tokens directly to the ElevenLabs WebSocket API, which returns audio chunks in real time. The frontend plays these chunks as they arrive, resulting in sub-second response times and a natural conversational experience.

#### Key Components
- **`services/elevenlabs_websocket_service.py`**: Implements the ElevenLabs WebSocket TTS API. Sends text chunks (with `try_trigger_generation: true`) as soon as they are generated by the LLM, and decodes/forwards audio chunks to the frontend.
- **`services/streaming_text_buffer.py`**: Buffers LLM tokens and flushes them to TTS at natural language boundaries for smooth, human-like speech.
- **`agents/langgraph_orchestrator.py`**: The new `llm_tts_streaming_node` streams LLM output to TTS and audio to the frontend in real time. The old `llm_node` and `tts_node` are replaced by this combined node.
- **`chat.html`**: The frontend now handles `audio_chunk` messages, buffering and playing audio as soon as it is received, with no need to wait for the full file.

#### Workflow
1. **LLM Streaming**: As the LLM generates tokens, they are buffered and sent to ElevenLabs via WebSocket.
2. **TTS Streaming**: ElevenLabs returns audio chunks in JSON messages, which are decoded and streamed to the frontend.
3. **Frontend Playback**: The frontend plays each audio chunk as soon as it arrives, using the Web Audio API for seamless playback.
4. **No Duplicate Playback**: The backend no longer sends the full audio in the final result message, preventing duplicate playback.

#### Benefits (Observed & Pending)
- **Backend metrics**: Time-to-first-token ≈ 0.7 s, total streaming ≈ 2.5 s.
- **Frontend reality**: Early human tests still feel ~5 – 6 s delay. Likely contributors: Deepgram `utterance_end_ms`, ElevenLabs initial buffer, browser decode. Issue logged in activeContext for follow-up optimisation.
- **Natural, conversational UX**: Once buffering is trimmed, the system will achieve near real-time feel.
- **Robust error handling**: The backend waits for the server to close the WebSocket, ensuring all audio is received.

### 3.8. Graph Layer & Neo4j Integration (June 2025)

The new **Graph Layer** augments vector-memory with rich relationship context.

- **`backend/config.py`**
  - Adds `NEO4J_CONFIG` dict containing `uri`, `username`, `password`.

- **`backend/subconscious/graph_schema.py`**
  - Defines node labels (`User`, `Memory`, `Emotion`) and relationship types (`FEELS`, `DISCLOSED_TO`, `LEADS_TO`).
  - Provides `ensure_constraints()` which runs at startup to create uniqueness constraints and indexes.

- **`backend/subconscious/graph_query_service.py`**
  - Exposes high-level Cypher helpers such as `get_recent_emotional_context(user_id: str) -> list[str]`.
  - Caches results for 60 s to minimise round-trips.

- **`backend/subconscious/graph_builder.py`**
  - `GraphRelationshipBuilder` batches relationship writes (called by `MemoryCoordinator`).
  - Supports graceful degradation if Neo4j is unreachable.

- **`backend/memory/mem0_async_service.py`**
  - Upgraded to **Mem0 v1.1** hybrid mode: `MemoryConfig(graph_store=neo4j_driver, vector_store=pgvector)`.

- **`backend/memory/memory_context_builder.py`**
  - Merges graph-derived emotional context into the user prompt alongside vector memories.

- **`backend/subconscious/intimacy_scaffold.py`**
  - `IntimacyScaffold` dataclass now includes `recent_emotions` (list[str]) and `relationship_graph_summary`.

- **Testing**
  - `tests/test_graph_integration.py` (deleted after migration) replaced by integration tests that assert vector-only fallback and graph query correctness.

-   **`emotional_archaeology.py` (`EmotionalArchaeology`)**
    -   **Purpose**: Houses vulnerability / joy / pain pattern mining logic that was extracted from `background_processor.py`.
    -   **Key Functions**:
        -   `mine_vulnerability_moments()`
        -   `extract_joy_patterns()`
        -   `map_pain_points()`

-   **`relationship_evolution.py` (`RelationshipEvolutionTracker`)**
    -   **Purpose**: Tracks trust milestones, communication DNA, and overall relationship velocity.
    -   **Key Functions**:
        -   `detect_relationship_velocity()`
        -   `track_trust_milestones()`
        -   `analyze_communication_patterns()`

(These two modules are now instantiated by `background_processor.py` and replace the previously inlined analysis helpers.)

### 3.2. Core Services (update)
-   **`deepgram_streaming_service.py`**
    -   **Update (June 2025)**: Added logic to filter out empty or duplicate `is_final` transcript events, preventing double-processing and duplicate AI replies.

---
