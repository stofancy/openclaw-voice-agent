"""
Main entry point for Voice Gateway.
"""
import asyncio
import sys
import os
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