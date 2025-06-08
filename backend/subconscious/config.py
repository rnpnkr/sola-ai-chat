import os
from dataclasses import dataclass

@dataclass
class SubconsciousConfig:
    """Configuration for subconscious processing"""
    
    # Background processing intervals
    update_interval: int = int(os.getenv("SUBCONSCIOUS_UPDATE_INTERVAL", "180"))  # 3 minutes
    cache_ttl: int = int(os.getenv("INTIMACY_CACHE_TTL", "300"))  # 5 minutes
    
    # Analysis settings
    emotional_analysis_depth: str = os.getenv("EMOTIONAL_ANALYSIS_DEPTH", "deep")
    relationship_memory_window: int = int(os.getenv("RELATIONSHIP_MEMORY_WINDOW", "30"))  # days
    
    # Performance limits
    max_concurrent_processors: int = int(os.getenv("MAX_CONCURRENT_PROCESSORS", "50"))
    max_vulnerability_memories: int = 15
    max_joy_memories: int = 15
    max_pain_memories: int = 15
    
    # Memory search limits
    memory_search_limit: int = 20
    trust_memory_limit: int = 20
    communication_memory_limit: int = 25
    
    # Analysis thresholds
    high_vulnerability_threshold: int = 2
    medium_vulnerability_threshold: int = 1
    deep_trust_threshold: int = 2
    established_trust_threshold: int = 3

    # Intimacy scaffold settings
    scaffold_cache_ttl: int = int(os.getenv("SCAFFOLD_CACHE_TTL", "300"))  # 5 minutes
    scaffold_retrieval_timeout: int = int(os.getenv("SCAFFOLD_RETRIEVAL_TIMEOUT", "150"))  # 150ms
    max_cached_scaffolds: int = int(os.getenv("MAX_CACHED_SCAFFOLDS", "100"))

    # Anticipatory engine settings
    connection_opportunity_limit: int = 5
    support_prediction_limit: int = 3
    emotional_readiness_timeout: int = 100  # ms

# Global configuration instance
subconscious_config = SubconsciousConfig() 