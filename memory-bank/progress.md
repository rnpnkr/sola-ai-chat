# Progress

## What works
- Core backend and frontend structure for real-time state communication and basic waveform visualization is established.
- FastAPI backend streams raw audio data and conversation state to frontend via WebSocket.
- ElevenLabs conversation logic with timer-based state tracking is functional.
- Initial React frontend with waveform visualization and WebSocket integration is working.
- Project brief, product context, and system patterns updated for new vision.

## What's left to build
- Phase 1: Foundation
  - LangGraph orchestrator setup
  - Basic personality agent framework
  - Mem0 service integration
  - Enhanced WebSocket message handling (personality, memory, crisis)
- Phase 2: Personality & Memory
  - 4 distinct agent personalities
  - Persistent memory across sessions (Mem0)
  - User profile management
  - Personality selection/switching
- Phase 3: Self-RAG Integration
  - Supabase therapeutic knowledge base
  - Self-RAG service implementation
  - Adaptive retrieval logic and citation tracking
- Phase 4: Safety & Crisis Management
  - Crisis detection system and risk assessment
  - Escalation protocols and safety dashboard
- Phase 5: Optimization & Testing
  - Latency optimization (<150ms personality, <800ms RAG)
  - Comprehensive testing suite and performance monitoring
  - Production deployment

## Current status
- Project is transitioning from foundational setup to Self-RAG + LangGraph + Mem0 architecture.
- Immediate focus is on backend restructuring, dependency setup, and initial agent/memory modules.
- Documentation and planning updated to align with new PRD.

## Known issues
- State tracking for SPEAKING/IDLE relies on timer-based estimation (legacy workaround).
- WebSocket session management is basic; needs robust multi-session support.
- No persistent memory or RAG yet; to be implemented in upcoming phases.
- No crisis detection or escalation logic yet.
- Frontend waveform visualization is not yet based on actual ElevenLabs audio stream.
- Error handling and compliance (HIPAA, privacy) need to be enforced in new modules.

## Next steps
- Add new dependencies and environment variables for Mem0, LangGraph, Supabase, etc.
- Create backend/agents, backend/memory, backend/rag modules and stubs.
- Implement initial LangGraph orchestrator and Mem0 service integration.
- Update WebSocket handling for new message types.
- Begin basic agent personality implementation.
- Continue phased rollout as per PRD. 