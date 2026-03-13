"""
Agent service client for Voice Gateway.
"""
import asyncio
from typing import Optional, Dict, Any

class AgentClient:
    """Agent service client."""
    
    def __init__(self, config):
        self.config = config
        
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process message with agent."""
        # Placeholder implementation
        return f"Processed: {message}"