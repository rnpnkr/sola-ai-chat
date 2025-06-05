# TASK.md

## Development Roadmap Tasks

### Phase 1 - Foundation (Self-RAG + LangGraph + Mem0)
- [ ] Set up enhanced backend directory structure (agents, memory, rag)
- [ ] Add new dependencies (langgraph, mem0ai, supabase, etc.)
- [ ] Add new environment variables (.env.example)
- [ ] Implement LangGraph orchestrator (stub)
- [ ] Implement Mem0 service (stub)
- [ ] Implement basic agent personality framework (stub)
- [ ] Update WebSocket message handling for new types (personality_select, memory_query, crisis_alert)

### Phase 2 - Personality & Memory
- [ ] Implement 4 distinct agent personalities
- [ ] Integrate persistent memory across sessions (Mem0)
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
- [ ] Optimize latency (<150ms personality, <800ms RAG)
- [ ] Build comprehensive testing suite and performance monitoring
- [ ] Deploy to production

## Discovered During Work
- [ ] Refine frontend state handling for all conversation states (LISTENING, THINKING, IDLE)
- [ ] Implement real-time audio streaming from backend to frontend for accurate waveform visualization
- [ ] Improve WebSocket error handling and session management
- [ ] Implement user interface for conversation input and output 
- [ ] Enforce privacy, encryption, and compliance in all new modules

## Phase: Mobile VUI

### Required Components
- [ ] `VoiceAIVisualizer.tsx` - Main visualization component
- [ ] `ParticleSystem.tsx` - Particle effects manager
- [ ] `WaveformRenderer.tsx` - 3D waveform rendering (simulated 3D)
- [ ] `StateTransitionManager.tsx` - Animation orchestrator
- [ ] `DebugControls.tsx` - Development state switcher

### Required Hooks
- [ ] `useAudioAnalyzer` - Process audio input/output
- [ ] `useStateTransition` - Manage state animations
- [ ] `usePerformanceMonitor` - Track FPS and metrics

### Testing Requirements
- [ ] Create test scenarios for rapid state changes
- [ ] Create test scenarios for low-end device performance
- [ ] Create test scenarios for extended usage (memory leaks)
- [ ] Create test scenarios for state transition interruptions
- [ ] Create test scenarios for background/foreground transitions

### Implementation Phases (Based on PRD Priority)
- [x] Phase 1: Basic state visualization with simple transitions
- [ ] Phase 2: Particle system and 3D waveform (simulated)
- [ ] Phase 3: Advanced animations and performance optimization
- [ ] Phase 4: Polish, micro-interactions, and accessibility 