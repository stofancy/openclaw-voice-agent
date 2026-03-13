"""
Agent service client - calls OpenClaw travel-agency agent
"""
import aiohttp
import json
from typing import Optional, Dict, Any


class AgentClient:
    """OpenClaw Agent service client"""
    
    def __init__(self, agent_url: str = "http://localhost:7777"):
        self.agent_url = agent_url
        
    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process message with travel-agency agent
        
        Args:
            message: User message text
            
        Returns:
            Agent response text
        """
        if not message:
            return "我没有听清楚，请再说一次。"
            
        try:
            # Call OpenClaw agent via HTTP
            # The agent API endpoint depends on OpenClaw's configuration
            payload = {
                "message": message,
                "agent_id": "travel-agency",
                "context": context or {}
            }
            
            async with aiohttp.ClientSession() as session:
                # Try the OpenClaw agent API
                async with session.post(
                    f"{self.agent_url}/api/agent/travel-agency",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'response' in result:
                            return result['response']
                        elif 'message' in result:
                            return result['message']
                    else:
                        print(f"Agent API error: {response.status}")
                        
            # Fallback: simple echo with prompt
            return "抱歉，我现在比较忙。请稍后再试。"
            
        except Exception as e:
            print(f"Agent error: {e}")
            return "抱歉，服务暂时不可用。"
