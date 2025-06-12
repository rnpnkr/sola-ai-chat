# Active System Context

### **1. Memory System (Now Stable & Performant)**
- The `mem0` memory pipeline is stable and has undergone significant performance optimization.
- **Connection**: The system uses the Supabase **Transaction Pooler** via the `pgvector` provider for robust database connectivity.
- **Data Handling**: The application is hardened against `mem0` library bugs. It defensively checks and normalizes inconsistent data formats returned from `mem0.search()`, preventing crashes.
- **Context Formatting**: The `MemoryContextBuilder` correctly extracts and formats memories, providing clear and effective context to the LLM.

### **2. Background Subconscious Analysis (Now Conversation-Aware)**
- The `PersistentSubconsciousProcessor` runs a background analysis loop.
- **CRITICAL FIX**: It now **pauses** automatically if the user is in an active real-time conversation, preventing resource contention and eliminating a major source of latency. This is achieved via a global `active_conversations` set.
- It performs **3 consolidated, psychologically-grounded semantic searches** against the memory store: Attachment, Vulnerability, and Growth.

### **3. Core Services & Performance Optimizations**
- **`MemoryCoordinator`**: The central hub for all memory operations. Now features **robust conversation deduplication** using a contextual content hash to prevent storing duplicate memories within a 10-minute window.
- **`MemoryContextBuilder`**: Now includes a **30-second in-memory cache** for memory search results. This dramatically reduces redundant API calls during a single conversation turn.
- **`IntimacyScaffoldManager`**: Provides fast, in-memory access to the latest psychological profile of the user.

### **4. Graph Memory Integration (June 2025)**
- Neo4j hybrid memory layer is partially integrated and running in *vector-only fallback* mode when graph store is unreachable.
- Core services added: `graph_schema.py`, `GraphQueryService`, `GraphRelationshipBuilder`.
- Background processor now persists basic relationships (FEELS, DISCLOSED_TO, LEADS_TO).
- MemoryCoordinator batching extended to `graph_relationship` operations.

## Current Focus

1. **Priority-4: Neo4j Relationship Migration** – The only outstanding item from the scalability roadmap is to finish the one-time data migration that adds the missing `FEELS` and `TRIGGERED_BY` relationship types.  The current warnings are benign but prevent full graph-memory enrichment.
2. **Perceived Latency Investigation** – Human UX still reports a 5-6 s gap between speech end and first audio despite backend TTF-token ≈0.8 s.  Suspected contributors: Deepgram endpointing, ElevenLabs initial buffer, browser decode.  Will profile with WebRTC timestamps after graph warnings are cleared.
3. **Product-Feature Work** – With priorities 1-3, 5-6 complete, engineering can resume roadmap features (Self-RAG, advanced emotional analytics).  Any new feature work must go through the Service Registry.

Completed since last update:
• **Priority-1** (AsyncMemory singleton), **Priority-2** (Service Registry), **Priority-3** (Neo4j driver pooling), **Priority-5** (User-isolated caches), **Priority-6** (Background-service optimisation) are all live in production and verified by logs.

Next engineering step: implement `GraphRelationshipBuilder.migrate_missing_relationships()` enhancements and adjust Cypher queries to use `MERGE` so the warnings disappear, then re-run graph health check.

## Recent Changes
- **Critical Latency & Performance Overhaul**: Completed a targeted sprint to resolve severe memory-induced latency.
  - **Implemented Active Conversation Gating**: The background processor now yields to the real-time loop.
  - **Added Memory Search Caching**: `MemoryContextBuilder` now caches search results to prevent redundant API calls.
  - **Fixed Deduplication Logic**: `MemoryCoordinator` now uses a more intelligent hashing mechanism to avoid unnecessary database writes for duplicate conversations.
  - **Added Global State Management**: Introduced `shared_state.py` to manage the `active_conversations` set.
- **Phase 3 Modularisation (June 2025)**: Extracted emotional-analysis logic into two dedicated modules – `subconscious/emotional_archaeology.py` and `subconscious/relationship_evolution.py` – and refactored `background_processor.py` to delegate to them. Improves readability and enables future reuse by analytics APIs.
- **Deepgram Duplicate-Final Transcript Filter**: Patched `DeepgramStreamingService.handle_transcript_event()` so empty or duplicate *final* events are discarded. Prevents double-processing and "processing 2 transcripts" log spam, eliminating occasional duplicate AI replies.

## Next Steps
- Review `TASK.md` to identify and begin work on the next highest-priority feature, now that the memory system is performant and stable.
- Continue to document any new system patterns or technical learnings in `systemPatterns.md`.
- **Finish traversal helpers in `GraphQueryService` and wire into scaffold**:
- **Add graph health monitoring to `/health` dashboard**:
- **Write isolation tests ensuring cross-user query safety**:

## Active Decisions and Considerations
- All new features should be built with an awareness of the new performance patterns (caching, background task yielding).
- Continue to program defensively when interacting with the `mem0` library. 