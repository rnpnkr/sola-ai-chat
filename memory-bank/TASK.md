

> **Next Step**: Finish Item 2 by adding unit tests for constraint creation, then move to Item 3.

### Memory Latency Optimizations and Scalability

Checklist of optimisation phases (derived from CURRENTTASK.md roadmap):

- [x] **Phase 0 – Scaffolding**: Create `ServiceRegistry` skeleton & startup hook
- [x] **Phase 1 – Memory Service Singleton**: Convert `IntimateMemoryService` to process-wide singleton, eager initialisation at startup
- [x] **Phase 2 – Service Registry Adoption**: Replace all remaining direct service instantiations with registry getters; add shutdown cleanup
- [x] **Phase 3 – Neo4j Connection Pool**: Singleton Neo4j driver, pooled connections, graceful fallback
- [x] **Phase 4 – Relationship Migration & Validation**: One-time migration for missing relationships + health checks  *(in progress)*
- [x] **Phase 5 – User-Isolated Caching**: Per-user locks, cleanup on disconnect, cache validation
- [x] **Phase 6 – Background Service Optimisation**: Ensure processors reuse shared services; add health endpoint

---