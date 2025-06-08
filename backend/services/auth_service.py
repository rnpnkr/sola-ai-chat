from supabase import create_client, Client
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import logging
from config import SUPABASE_CONFIG

logger = logging.getLogger(__name__)

class SupabaseAuthService:
    def __init__(self):
        supabase_url = SUPABASE_CONFIG.get("url")
        supabase_key = SUPABASE_CONFIG.get("anon_key")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in SUPABASE_CONFIG")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            response = self.supabase.auth.get_user(token)
            if response.user:
                return {
                    "user_id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata
                }
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Register new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return {
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            logger.error(f"Sign up failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with better error handling"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if sign-in was successful
            if response.user and response.session:
                return {
                    "user": response.user,
                    "session": response.session
                }
            elif response.user and not response.session:
                # User exists but email not confirmed
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not confirmed. Please check your email and click the confirmation link."
                )
            else:
                # Authentication failed
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Sign in failed: {error_message}")
            
            # Handle specific Supabase auth errors
            if "Invalid login credentials" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            elif "Email not confirmed" in error_message:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not confirmed. Please check your email and click the confirmation link."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )

    async def create_confirmed_user(self, email: str, password: str) -> Dict[str, Any]:
        """Create a user with email pre-confirmed (for development)"""
        try:
            # First create the user
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Then confirm their email using service role key
            if response.user:
                # This would require service role key and admin methods
                # For now, manually update in dashboard or use SQL
                pass
            
            return {
                "user": response.user,
                "session": response.session,
                "message": "User created. Email confirmation may be required."
            }
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

# Global instance
auth_service = SupabaseAuthService() 