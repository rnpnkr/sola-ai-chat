# Active Context

## Current Work Focus
- Laying the foundation for Self-RAG + LangGraph + Mem0 architecture.
- Setting up enhanced backend directory structure and new core modules (agents, memory, rag).
- Integrating Mem0 for persistent memory and LangGraph for orchestration.
- Implementing basic agent personality framework.
- Updating WebSocket message handling for new message types (personality, memory, crisis).

## Recent Changes
- Defined new backend architecture and directory structure per PRD.
- Added requirements for new dependencies and environment variables.
- Outlined agent personality system and memory categories.
- Planned for Supabase-based therapeutic knowledge base and Self-RAG integration.
- Updated project brief and product context to align with new vision.

## Next Steps
- Add new dependencies and environment variables for Mem0, LangGraph, Supabase, etc.
- Create backend/agents, backend/memory, backend/rag modules and stubs.
- Implement initial LangGraph orchestrator and Mem0 service integration.
- Update WebSocket handling for personality selection and memory queries.
- Begin basic agent personality implementation.

## Active Decisions and Considerations
- Phased rollout: Foundation → Personality/Memory → Self-RAG → Crisis/Safety → Optimization.
- Prioritize latency and memory efficiency in all new modules.
- Use Mem0 for all persistent memory and context retrieval.
- Use Supabase for therapeutic content and RAG.
- Ensure all new features are modular and testable.
- Maintain privacy, encryption, and compliance from the start. 