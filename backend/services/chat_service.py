from typing import List, Dict, Optional
from supabase import create_client, Client
import logging
from datetime import datetime
from config import SUPABASE_CONFIG

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        supabase_url = SUPABASE_CONFIG.get("url")
        service_role_key = SUPABASE_CONFIG.get("service_role_key")
        
        if not supabase_url or not service_role_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in SUPABASE_CONFIG")
        
        self.supabase: Client = create_client(supabase_url, service_role_key)
    
    async def store_chat(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        ai_response: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Store a chat exchange"""
        try:
            chat_data = {
                "user_id": user_id,
                "session_id": session_id,
                "user_message": user_message,
                "ai_response": ai_response,
                "metadata": metadata or {},
                "title": self._generate_title(user_message)  # Auto-generate title
            }
            
            response = self.supabase.table("chats").insert(chat_data).execute()
            return response.data[0]
        except Exception as e:
            logger.error(f"Failed to store chat: {e}")
            raise
    
    async def get_user_chats(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get user's chat history"""
        try:
            response = (
                self.supabase.table("chats")
                .select("*")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get user chats: {e}")
            return []
    
    async def get_chat_sessions(self, user_id: str) -> List[Dict]:
        """Get unique chat sessions for a user"""
        try:
            response = (
                self.supabase.table("chats")
                .select("session_id, title, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
            
            # Group by session_id and get the latest chat for each session
            sessions = {}
            for chat in response.data:
                session_id = chat["session_id"]
                if session_id not in sessions:
                    sessions[session_id] = chat
            
            return list(sessions.values())
        except Exception as e:
            logger.error(f"Failed to get chat sessions: {e}")
            return []
    
    async def get_session_chats(
        self,
        user_id: str,
        session_id: str
    ) -> List[Dict]:
        """Get all chats from a specific session"""
        try:
            response = (
                self.supabase.table("chats")
                .select("*")
                .eq("user_id", user_id)
                .eq("session_id", session_id)
                .order("created_at", asc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to get session chats: {e}")
            return []
    
    def _generate_title(self, user_message: str) -> str:
        """Generate a title from the first user message"""
        # Take first 50 characters and clean up
        title = user_message[:50].strip()
        if len(user_message) > 50:
            title += "..."
        return title

# Global instance
chat_service = ChatService() 