"""
Main entry point for Voice Gateway.
"""
import asyncio
import sys
import os
from pathlib import Path

# Load .env file (project root)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    print(f"Loading .env from {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value
    print(f"Loaded API key: {os.environ.get('ALI_BAILIAN_API_KEY', 'NOT SET')[:10]}...")

from .config import Config
from .webrtc_server import WebRTCServer

async def main():
    """Main application entry point."""
    config = Config()
    
    # Initialize WebRTC server
    webrtc_server = WebRTCServer(config)
    
    try:
        await webrtc_server.start()
        print("Voice Gateway started successfully!")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        await webrtc_server.stop()
        print("Voice Gateway stopped.")
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)