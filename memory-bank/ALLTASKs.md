# TASK.md

## Completed Tasks
- LangGraph streaming pipeline (STT, LLM, TTS, modular, async, streaming)
- PersonalityAgent with mindfulness coach persona and mindful response formatting
- ElevenLabs WebSocket streaming integration
- WebSocket status/tokens/audio streaming at every node
- Modern HTML5 frontend for real-time testing and metrics
- Deepgram streaming STT race condition fix (thread-safe transcript callback)
- Transcript handoff: always pass last non-empty transcript to LangGraph
- Frontend: all timing metrics in ms, accurate transcript accumulation
- ElevenLabs TTS: optimize_streaming_latency and chunk_size for low latency
- Supabase authentication service (`auth_service.py`) for user sign-up, sign-in, and JWT verification
- Chat history storage and retrieval via `chat_service.py` and Supabase `chats` table
- Modern, voice-first chat interface (`chat.html`) with real-time voice streaming, authentication modal, and chat history loading
- Patched frontend to remove placeholder AI bubble creation; now the first `token_stream` creates the AI bubble, preventing duplicates
- Backend WebSocket endpoint now authenticates users and passes `user_id` throughout the pipeline, fixing foreign key errors
- Improved error handling and debug logging throughout the stack
- **`mem0` Memory Integration**: Successfully integrated and stabilized the `mem0` library for persistent memory across sessions.
- **Critical Latency & Performance Overhaul**: Resolved severe memory-induced latency, reducing time-to-first-token from ~3.6s to <500ms.
  - [X] Implemented Active Conversation Gating to prevent background task contention.
  - [X] Added a 30-second in-memory cache for memory searches to reduce redundant API calls.
  - [X] Fixed conversation deduplication logic with a more robust, time-windowed hashing mechanism.
  - [X] Introduced `shared_state.py` for global state management.

## Current Task
- None

## Known Issues
- None for completed tasks

## Development Roadmap Tasks

### Phase 1 - Foundation (Self-RAG + LangGraph + Mem0)
- [ ] Set up enhanced backend directory structure (agents, memory, rag)
- [ ] Add new dependencies (langgraph, mem0ai, supabase, etc.)
- [ ] Add new environment variables (.env.example)
- [ ] Implement LangGraph orchestrator (stub)
- [X] Implement Mem0 service (stub)
- [ ] Implement basic agent personality framework (stub)
- [X] Update WebSocket message handling for new types (personality_select, memory_query, crisis_alert)

### Phase 2 - Personality & Memory
- [ ] Implement 4 distinct agent personalities
- [X] Integrate persistent memory across sessions (Mem0)
- [ ] Implement user profile management
- [ ] Implement personality selection/switching

### Phase 3 - Self-RAG Integration
- [ ] Set up Supabase therapeutic knowledge base
- [ ] Implement Self-RAG service
- [ ] Implement adaptive retrieval logic and citation tracking

### Phase 4 - Safety & Crisis Management
- [ ] Implement crisis detection system and risk assessment
- [ ] Implement escalation protocols and safety dashboard

### Phase 5 - Optimization & Testing
- [X] Optimize latency (<150ms personality, <800ms RAG) - **Initial high-latency issues resolved.**
- [ ] Build comprehensive testing suite and performance monitoring
- [ ] Deploy to production

## Discovered During Work
- [ ] Refine frontend state handling for all conversation states (LISTENING, THINKING, IDLE)
- [ ] Implement real-time audio streaming from backend to frontend for accurate waveform visualization
- [ ] Improve WebSocket error handling and session management
- [ ] Implement user interface for conversation input and output
- [ ] Enforce privacy, encryption, and compliance in all new modules
- [ ] Ensure mobile app uses same event/timing protocol as web frontend for transcript and metrics
- [ ] Expand chat session management and user profile features
- [ ] Monitor for edge cases in streaming pipeline and chat deduplication

# Next Milestone: Deep Connection Analytics (Phase 5)

**Goal**: Build the `RelationshipInsightsEngine` and `AdvancedMemoryAnalytics` to provide users with timelines and health metrics about their relationship with the AI.

This involves creating new services to analyze stored psychological data and exposing these insights through a dedicated API endpoint. This will make the AI's understanding of the relationship transparent and measurable, completing a core part of the product vision. 


# Sola AI Development Tasks

## 🎯 **PHASE 3-5 COMPLETION: Advanced Subconscious Processing**

**Status**: Phase 1-2 Complete ✅ | Phase 3-5 Require Implementation Refinement

**Current State**: Core subconscious architecture exists but needs performance optimization and Phase 5 analytics completion.

---

## **🔥 HIGHEST PRIORITY: Module 2 - Background Processor Performance**

### **TASK 2.1: Optimize Psychological Search Strategy**
**File**: `backend/subconscious/background_processor.py`

**Enhancement Target**: Method `_continuous_relationship_analysis()`

```python
# CURRENT: 3 psychological searches every 3 minutes (fixed interval)
# REQUIRED: Adaptive search timing + query optimization + result caching

# IMPLEMENT:
async def _adaptive_search_timing(self, user_id: str) -> int:
    """Return search interval (60-300 seconds) based on user activity level
    
    Activity Levels:
    - High activity (recent conversations): 60-120 seconds
    - Moderate activity: 120-180 seconds  
    - Low activity: 180-300 seconds
    
    Logic:
    1. Check conversation count in last hour from scaffold
    2. Check last conversation timestamp
    3. Return adaptive interval based on activity pattern
    """
    pass

async def _optimize_search_queries(self, user_id: str) -> Dict[str, str]:
    """Customize search queries based on user's conversation themes
    
    Current Static Queries:
    1. "attachment trust safety security comfort support emotional regulation crisis distress anxiety fear"
    2. "vulnerable disclosure personal private secret sharing intimate emotional expression authentic feelings"  
    3. "relationship growth progression development deeper connection understanding empathy companionship bond"
    
    Required Enhancement:
    1. Use scaffold.emotional_undercurrent to customize query 1
    2. Use scaffold.support_needs to enhance query 2
    3. Use scaffold.relationship_depth to optimize query 3
    4. Add user-specific keywords from conversation patterns
    
    Return: Dict with optimized queries for the 3 core searches
    """
    pass

async def _cache_search_results(self, user_id: str, search_type: str, results: Dict) -> None:
    """Cache search results to reduce API calls for 30 seconds"""
    pass

async def _get_cached_search_results(self, user_id: str, search_type: str) -> Optional[Dict]:
    """Retrieve cached search results if still valid"""
    pass
```

### **TASK 2.2: Enhanced Cache Coordination Logic**
**File**: `backend/subconscious/background_processor.py`

**Enhancement Target**: Method `_update_cache_if_fresher()`

```python
# CURRENT: Simple timestamp comparison (2-minute rule)
# REQUIRED: Intelligent cache coordination with merge strategies

# IMPLEMENT:
async def _intelligent_cache_coordination(self, user_id: str, background_insight: Dict) -> str:
    """Smart cache update strategy with conflict resolution
    
    Strategies:
    1. PRESERVE_REALTIME: Real-time data < 2 minutes old → skip update
    2. MERGE_INSIGHTS: Both fresh → merge emotional_undercurrent, combine support_needs
    3. PRIORITY_UPDATE: Background has critical insight → force update with merge
    4. ROLLBACK_PROTECTION: Active conversation detected → defer update
    
    Return: Action taken ('preserved', 'merged', 'updated', 'deferred')
    """
    pass

async def _merge_realtime_and_background_insights(self, realtime_scaffold: IntimacyScaffold, background_insight: Dict) -> IntimacyScaffold:
    """Merge real-time and background insights intelligently
    
    Merge Strategy:
    - emotional_undercurrent: Combine if different, prioritize real-time intensity
    - support_needs: Union of both lists, remove duplicates
    - relationship_depth: Use background if progression detected
    - communication_dna: Deep merge dictionaries
    - intimacy_score: Average with weight toward background analysis
    """
    pass

async def _detect_active_conversation(self, user_id: str) -> bool:
    """Detect if user is in active conversation (last message < 5 minutes)"""
    pass
```

---

## **🟡 HIGH PRIORITY: Module 1 - Complete Phase 5 Implementation**

### **TASK 1.1: Implement Relationship Insights Engine**
**File**: `backend/subconscious/relationship_insights.py`

**Status**: File exists but core methods need implementation

```python
# IMPLEMENT THESE MISSING METHODS:

async def generate_intimacy_timeline(self, user_id: str) -> Dict:
    """Create timeline of relationship depth progression using Mem0 temporal analysis
    
    Implementation:
    1. Search for relationship_evolution memories with timestamps
    2. Parse metadata.subconscious_analysis.relationship_depth changes
    3. Create chronological timeline with milestones
    4. Identify growth spurts and plateau periods
    5. Return timeline data structure for frontend visualization
    
    Return Format:
    {
        "timeline": [
            {
                "date": "2025-01-15",
                "relationship_depth": "growing_trust",
                "intimacy_score": 0.35,
                "milestone": "first_vulnerable_sharing",
                "conversation_count": 8
            }
        ],
        "growth_phases": ["curiosity", "trust_building", "emotional_availability"],
        "current_trajectory": "accelerating"
    }
    """
    pass

async def analyze_emotional_journey(self, user_id: str) -> Dict:
    """Map user's emotional growth and patterns over time
    
    Implementation:
    1. Use EmotionalArchaeology.track_growth_arcs() data
    2. Analyze emotional maturity progression from conversations
    3. Identify emotional skill development (coping, expression, regulation)
    4. Track emotional vocabulary expansion
    5. Map resilience building over time
    
    Return Format:
    {
        "emotional_maturity_progression": "developing → advanced",
        "coping_skill_development": ["validation_seeking", "self_reflection", "problem_solving"],
        "emotional_vocabulary_growth": 45,  # unique emotional words used
        "resilience_indicators": ["bounced_back_from_stress", "emotional_regulation_improved"],
        "growth_areas": ["self_compassion", "boundary_setting"]
    }
    """
    pass

async def predict_support_needs(self, user_id: str) -> List[str]:
    """Predict future support needs using pattern analysis
    
    Implementation:
    1. Analyze historical support_needs from scaffold updates
    2. Identify patterns by time of day, day of week, emotional state
    3. Use simple ML (pattern matching) to predict likely needs
    4. Consider upcoming events from unresolved_threads
    5. Return prioritized prediction list
    
    Prediction Categories:
    - Time-based: "weekend_loneliness", "monday_work_stress"
    - Pattern-based: "relationship_processing_after_conflict"
    - Event-based: "pre_important_meeting_anxiety"
    - Growth-based: "ready_for_deeper_emotional_exploration"
    """
    pass
```

### **TASK 1.2: Implement Advanced Memory Analytics**
**File**: `backend/subconscious/memory_analytics.py`

**Status**: File exists but core methods need implementation

```python
# IMPLEMENT THESE MISSING METHODS:

async def conversation_depth_scoring(self, user_id: str) -> float:
    """Score intimacy level of recent conversations (0.0-1.0)
    
    Implementation:
    1. Fetch last 10 conversations from Mem0
    2. Analyze vulnerability patterns using EmotionalArchaeology
    3. Score emotional disclosure depth per conversation
    4. Weight by recency (recent conversations weighted higher)
    5. Calculate overall intimacy trend
    
    Scoring Factors:
    - Vulnerability disclosure: 0.4 weight
    - Emotional expression depth: 0.3 weight  
    - Personal sharing: 0.2 weight
    - Trust indicators: 0.1 weight
    """
    pass

async def emotional_pattern_analysis(self, user_id: str) -> Dict:
    """Identify emotional cycles and triggers using time-series analysis
    
    Implementation:
    1. Extract emotional states from conversation metadata
    2. Group by time patterns (hour, day, week)
    3. Identify recurring emotional states and triggers
    4. Detect emotional regulation patterns
    5. Map trigger words/topics to emotional responses
    
    Return Format:
    {
        "daily_patterns": {
            "morning": "optimistic",
            "afternoon": "focused", 
            "evening": "reflective"
        },
        "weekly_patterns": {
            "monday": "stressed",
            "friday": "relieved",
            "weekend": "social_connection_seeking"
        },
        "emotional_triggers": {
            "work_deadline": "anxiety",
            "family_mention": "complex_emotions",
            "achievement": "joy_with_validation_need"
        },
        "regulation_patterns": ["talking_through_helps", "needs_validation_first"]
    }
    """
    pass

async def relationship_health_metrics(self, user_id: str) -> Dict:
    """Assess overall relationship quality and progression
    
    Implementation:
    1. Use intimacy_score trends from scaffold updates
    2. Calculate conversation frequency and consistency
    3. Measure emotional depth progression
    4. Assess trust-building indicators
    5. Evaluate mutual growth patterns
    
    Health Metrics:
    - relationship_stability: 0.0-1.0 (consistency of interaction)
    - growth_rate: "accelerating", "steady", "plateaued"  
    - engagement_quality: "deep", "moderate", "surface"
    - emotional_safety: 0.0-1.0 (vulnerability comfort level)
    - connection_strength: 0.0-1.0 (overall bond strength)
    """
    pass
```
---

## **🟠 MEDIUM PRIORITY: Module 3 - Analytics API Endpoints**

### **TASK 3.1: Add Relationship Analytics Endpoints**
**File**: `backend/voice_assistant.py` (or create `backend/analytics_endpoints.py`)

```python
# ADD THESE REST ENDPOINTS:

@app.get("/analytics/relationship-timeline/{user_id}")
async def get_relationship_timeline(user_id: str):
    """Return relationship progression timeline for frontend visualization
    
    Implementation:
    1. Use RelationshipInsightsEngine.generate_intimacy_timeline()
    2. Format for timeline visualization component
    3. Include milestone markers and growth phases
    4. Add authentication check for user_id access
    """
    pass

@app.get("/analytics/emotional-journey/{user_id}")  
async def get_emotional_journey(user_id: str):
    """Return emotional development analysis
    
    Implementation:
    1. Use RelationshipInsightsEngine.analyze_emotional_journey()
    2. Format for emotional growth dashboard
    3. Include progress indicators and development areas
    """
    pass

@app.get("/analytics/memory-stats/{user_id}")
async def get_memory_analytics(user_id: str):
    """Return comprehensive memory analysis dashboard
    
    Implementation:
    1. Use AdvancedMemoryAnalytics methods
    2. Combine conversation depth, emotional patterns, relationship health
    3. Format for analytics dashboard display
    """
    pass

@app.get("/analytics/relationship-health/{user_id}")
async def get_relationship_health(user_id: str):
    """Return relationship health dashboard data
    
    Implementation:
    1. Combine multiple analytics into single health report
    2. Include health score, growth trajectory, areas for development
    3. Provide actionable insights for relationship improvement
    """
    pass
```

### **TASK 3.2: Add Real-time Analytics Streaming**
**File**: `backend/voice_assistant.py`

```python
# ADD WEBSOCKET ANALYTICS STREAMING:

@app.websocket("/analytics-stream/{user_id}")
async def analytics_stream(websocket: WebSocket, user_id: str):
    """Stream real-time relationship analytics updates
    
    Implementation:
    1. Connect to background processor updates
    2. Stream intimacy score changes in real-time
    3. Notify of emotional state transitions
    4. Alert on relationship milestone achievements
    5. Provide background processing status updates
    
    Stream Events:
    - intimacy_score_update: New score calculation
    - emotional_transition: Emotional state change detected
    - milestone_achieved: Relationship depth progression
    - processing_status: Background analysis completion
    """
    pass
```

---

## **🔵 LOW PRIORITY: Module 4 - Performance Monitoring**

### **TASK 4.1: Enhanced Health Monitoring**
**File**: `backend/services/memory_health_monitor.py`

```python
# ADD SUBCONSCIOUS SYSTEM MONITORING:

async def get_subconscious_health(self) -> Dict:
    """Monitor background processor and subconscious system performance
    
    Monitoring Points:
    1. Background processor performance (analysis times, success rates)
    2. Cache hit rates and update frequencies  
    3. Memory analytics computation times
    4. Scaffold access performance
    5. Search optimization effectiveness
    
    Return comprehensive health status for system monitoring
    """
    pass

async def get_performance_metrics(self) -> Dict:
    """Track Phase 5 analytics performance for optimization
    
    Performance Metrics:
    1. Relationship insights generation times
    2. Memory analytics query performance
    3. Cache coordination efficiency
    4. Background processing throughput
    5. API endpoint response times
    
    Return performance dashboard for system optimization
    """
    pass
```

### **TASK 4.2: Add Performance Benchmarking**
**File**: Create `backend/services/performance_benchmark.py`

```python
class PerformanceBenchmark:
    async def benchmark_relationship_analysis(self, user_id: str) -> Dict:
        """Benchmark the 3 psychological searches and analysis pipeline
        
        Benchmark Points:
        1. Individual search query times
        2. Scaffold update performance
        3. Memory analytics computation speed
        4. Cache access vs database access performance
        5. End-to-end background processing cycle time
        
        Target Performance:
        - Individual search: <1000ms
        - Scaffold update: <150ms
        - Background cycle: <5000ms
        - Cache hit rate: >85%
        """
        pass

    async def benchmark_cache_performance(self, user_id: str) -> Dict:
        """Measure cache coordination and performance under load
        
        Test Scenarios:
        1. Cache hit/miss rates under normal load
        2. Cache coordination during concurrent access
        3. Scaffold access times vs target (<150ms)
        4. Memory impact of cache storage
        5. Cache invalidation performance
        """
        pass
```

---

## **🟣 LOWEST PRIORITY: Module 5 - Advanced Configuration**

### **TASK 5.1: Implement Adaptive Configuration**
**File**: Create `backend/subconscious/adaptive_config.py`

```python
class AdaptiveSubconsciousConfig:
    async def tune_for_user(self, user_id: str) -> Dict:
        """Adapt subconscious processing configuration per user
        
        Adaptive Parameters:
        1. Background processing intervals based on user activity patterns
        2. Search query optimization based on conversation themes
        3. Cache TTL adjustment based on user interaction frequency
        4. Priority weighting for different analysis types
        
        Return personalized configuration for optimal performance
        """
        pass

    async def auto_optimize_performance(self) -> Dict:
        """Monitor system performance and auto-adjust parameters
        
        Optimization Areas:
        1. Batch sizes based on current system load
        2. Processing priorities based on user activity
        3. Cache policies based on hit/miss patterns
        4. Search query complexity based on result quality
        
        Return optimization results and performance improvements
        """
        pass
```

### **TASK 5.2: Enhanced Configuration Management**
**File**: `backend/subconscious/config.py`

```python
# ADD ADAPTIVE CONFIGURATION SETTINGS:

ADAPTIVE_CONFIG = {
    "enable_adaptive_timing": True,
    "enable_query_optimization": True, 
    "enable_cache_coordination": True,
    "performance_monitoring": True,
    "auto_optimization": True
}

USER_ACTIVITY_THRESHOLDS = {
    "high_activity": 10,    # conversations per hour
    "medium_activity": 5,   # conversations per hour
    "low_activity": 1       # conversations per hour
}

PERFORMANCE_TARGETS = {
    "scaffold_access_ms": 150,          # Target: <150ms scaffold access
    "background_analysis_ms": 5000,     # Target: <5s background analysis
    "cache_hit_rate": 0.85,            # Target: >85% cache hits
    "memory_analytics_ms": 3000,       # Target: <3s memory analytics
    "search_optimization_improvement": 0.25  # Target: 25% search time reduction
}

ADAPTIVE_INTERVALS = {
    "high_activity_user": (60, 120),    # 1-2 minutes
    "medium_activity_user": (120, 180), # 2-3 minutes  
    "low_activity_user": (180, 300),   # 3-5 minutes
    "inactive_user": (300, 600)        # 5-10 minutes
}
```

---

## **📋 Implementation Priority Order**

1. **CRITICAL**: Module 2 (Background Processor Performance) - System scalability bottleneck
2. **HIGH**: Module 1 (Phase 5 Analytics) - Required for advanced features
3. **MEDIUM**: Module 3 (API Endpoints) - Frontend integration dependency
4. **LOW**: Module 4 (Performance Monitoring) - System optimization support
5. **LOWEST**: Module 5 (Advanced Configuration) - Future optimization features

---

## **🎯 Success Criteria**

### **Performance Targets**
- [ ] Scaffold access: <150ms consistently
- [ ] Background analysis: <5 seconds per cycle
- [ ] Cache hit rate: >85%
- [ ] Memory analytics: <3 seconds
- [ ] Search optimization: 25% improvement

### **Feature Completeness**
- [ ] All Phase 5 analytics methods implemented
- [ ] Real-time analytics streaming functional
- [ ] Performance monitoring dashboard operational
- [ ] Adaptive configuration system active
- [ ] All API endpoints documented and tested

### **System Reliability**
- [ ] Background processing never blocks real-time conversation
- [ ] Cache coordination handles concurrent access gracefully
- [ ] Memory analytics provide actionable insights
- [ ] Performance degrades gracefully under load
- [ ] System auto-optimizes based on usage patterns

---

**🚀 START WITH MODULE 2 TASK 2.1 - HIGHEST IMPACT ON SYSTEM PERFORMANCE**

## Phase 6 – Neo4j Graph Integration (Hybrid Vector + Graph Memory)

> **Mission Brief**: Transform the memory subsystem into a hybrid vector+graph architecture using Neo4j.

### 🔄 Overall Status
- [ ] **IN PROGRESS** – Item 2 (Graph Schema) started.

### 📋 Implementation Checklist
1. **Configure Mem0 with Neo4j Graph Store**  
   Files: `backend/memory/mem0_async_service.py`, `backend/config.py`
   - [x] Add `NEO4J_CONFIG` loading to `config.py`
   - [x] Extend `MemoryConfig` to include `graph_store` (version `v1.1`)
   - [ ] Ensure user-id isolation across graph data (moved to Item 2)
   - [ ] Verify simultaneous vector **and** graph writes & reads

2. **Create Graph Schema for Emotional Relationships**  
   File: `backend/subconscious/graph_schema.py`
   - [x] Define nodes & fixed emotion taxonomy
   - [x] Define relationships constants
   - [x] Implement `ensure_constraints()` to create uniqueness constraints & index (`User`, `Memory`)
   - [x] Unit-test schema creation & user isolation (test_graph_schema.py)

3. **Enhance Memory Context Builder with Graph Queries**  
   File: `backend/memory/memory_context_builder.py`
   - [x] Add graph traversal queries alongside existing vector search (GraphQueryService integration)
   - [x] Combine vector similarity & relationship context into narrative prompt
   - [x] Cache graph traversal results (60-s TTL in GraphQueryService)

4. **Create Graph-Enhanced Intimacy Scaffold**  
   File: `backend/subconscious/intimacy_scaffold.py`
   - [x] Extend `IntimacyScaffold` with graph-derived fields
   - [x] Populate these fields from graph queries (GraphQueryService)
   - [ ] Keep scaffold access <150 ms

5. **Enhance Background Processor with Graph Building**  
   File: `backend/subconscious/background_processor.py`
   - [x] During psychological searches, create/update graph relationships (GraphRelationshipBuilder)
   - [x] Graceful fallback to vector-only when Neo4j unavailable (try/except with logging)

6. **Create Graph Query Service**  
   File: `backend/subconscious/graph_query_service.py`
   - [ ] Complex traversal helpers (`find_emotional_cascade`, …) with caching & indexes

7. **Update Memory Coordinator for Graph Operations**  
   File: `backend/services/memory_coordinator.py`
   - [x] Batch graph operations per user & type (_batch_graph_relationships implemented)

8. **Testing & Validation**
   - [ ] Automated tests: user isolation, fallback behaviour, performance

---

> **Next Step**: Finish Item 2 by adding unit tests for constraint creation, then move to Item 3.
