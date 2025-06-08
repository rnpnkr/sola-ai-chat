from fastapi import HTTPException, status, Query
from typing import Optional
import asyncio

async def get_current_user_async(token: str) -> dict:
    """Extract and verify user from JWT token"""
    from services.auth_service import auth_service
    user_data = await auth_service.verify_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return user_data 