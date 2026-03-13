"""
Agent service client - calls OpenClaw travel-agency agent via CLI
"""
import subprocess
import json
from typing import Optional, Dict, Any


class AgentClient:
    """OpenClaw Agent service client"""
    
    def __init__(self, agent_id: str = "travel-agency"):
        self.agent_id = agent_id
        
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
            # Call OpenClaw agent via CLI
            result = subprocess.run(
                ["openclaw", "agent", "--agent", self.agent_id, "--message", message, "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Parse JSON output
                try:
                    response_data = json.loads(result.stdout)
                    if 'response' in response_data:
                        return response_data['response']
                    elif 'message' in response_data:
                        return response_data['message']
                    elif 'output' in response_data:
                        return response_data['output']
                except json.JSONDecodeError:
                    # If not JSON, return the raw output
                    return result.stdout.strip()
            else:
                print(f"Agent CLI error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("Agent timeout")
            return "抱歉，处理超时了。"
        except Exception as e:
            print(f"Agent error: {e}")
            return "抱歉，服务暂时不可用。"
        
        return "抱歉，我现在比较忙。请稍后再试。"
