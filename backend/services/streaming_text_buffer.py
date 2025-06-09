import asyncio
import re
from typing import Callable, Optional
import logging

class StreamingTextBuffer:
    """
    Manages text buffering for streaming TTS to optimize for natural speech boundaries
    """
    
    def __init__(self, min_chunk_size: int = 20, max_chunk_size: int = 150):
        self.buffer = ""
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.text_callback = None
        
    def set_text_callback(self, callback: Callable[[str], None]):
        """Set callback for when text chunks are ready to send"""
        self.text_callback = callback
        
    async def add_token(self, token: str):
        """
        Add a new token and check if we should flush a chunk
        """
        self.buffer += token
        
        # Check for natural break points
        if self._should_flush_buffer():
            await self._flush_buffer()
            
    async def finish(self):
        """
        Flush any remaining buffer content
        """
        if self.buffer.strip():
            await self._flush_buffer()
            
    def _should_flush_buffer(self) -> bool:
        """
        Determine if buffer should be flushed based on content and size
        """
        # Force flush if buffer is too large
        if len(self.buffer) >= self.max_chunk_size:
            return True
            
        # Don't flush if buffer is too small
        if len(self.buffer) < self.min_chunk_size:
            return False
            
        # Look for natural break points
        natural_breaks = ['.', '!', '?', ',', ';', ':', '\n']
        
        # Check if buffer ends with a natural break
        if any(self.buffer.strip().endswith(break_char) for break_char in natural_breaks):
            return True
            
        # Check for mid-sentence natural pauses
        pause_patterns = [r'\s+(and|but|or|so|yet|because|since|although|while)\s+']
        for pattern in pause_patterns:
            if re.search(pattern, self.buffer[-30:], re.IGNORECASE):
                return True
                
        return False
        
    async def _flush_buffer(self):
        """
        Send buffered text to callback and reset buffer
        """
        if self.text_callback and self.buffer.strip():
            chunk = self.buffer.strip()
            self.buffer = ""
            
            # Send chunk asynchronously
            try:
                if asyncio.iscoroutinefunction(self.text_callback):
                    await self.text_callback(chunk)
                else:
                    self.text_callback(chunk)
                    
                logging.debug(f"Flushed text chunk: {chunk}")
                
            except Exception as e:
                logging.error(f"Error in text callback: {e}") 