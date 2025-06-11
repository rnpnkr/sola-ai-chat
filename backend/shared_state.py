from typing import Set

# Global set tracking user_ids currently engaged in an active real-time conversation.
# Background services (e.g., PersistentSubconsciousProcessor) consult this set to avoid
# running heavy analysis during a live session.
active_conversations: Set[str] = set() 