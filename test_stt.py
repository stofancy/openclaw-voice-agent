#!/usr/bin/env python3
"""
Test STT service - 调用阿里百炼 ASR
"""
import os
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

print(f"API Key: {os.environ.get('ALI_BAILIAN_API_KEY', 'NOT SET')[:10]}...")

# 尝试不同的模型名称
models_to_try = [
    "qwen3-asr-flash-realtime-2026-02-10",
    "paraformer-realtime",
    "paraformer-v2",
]

import json
import base64
import websocket as ws_client
from threading import Thread
from queue import Queue

def test_stt_with_model(model_name):
    print(f"\n=== Testing model: {model_name} ===")
    api_key = os.environ.get("ALI_BAILIAN_API_KEY", "")
    ws_url = f"wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model={model_name}"
    
    result_queue = Queue()
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            print(f"STT received: {data.get('type')}")
            
            # Check for transcript
            if data.get("type") == "response.audio_transcript.done":
                transcript = data.get("transcript", {}).get("text", "")
                result_queue.put(("final", transcript))
            elif "transcript" in data:
                transcript = data.get("transcript", {}).get("text", "")
                if transcript:
                    result_queue.put(("partial", transcript))
        except Exception as e:
            print(f"STT parse error: {e}")
    
    def on_error(ws, error):
        print(f"STT WebSocket error: {error}")
        result_queue.put(("error", str(error)))
    
    def on_close(ws, close_status_code, close_msg):
        print(f"STT closed: {close_status_code} - {close_msg}")
    
    def on_open(ws):
        print("STT WebSocket opened")
        
        # Send session update with VAD
        session_event = {
            "event_id": "event_session_001",
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "input_audio_format": "pcm",
                "sample_rate": 16000,
                "input_audio_transcription": {
                    "language": "zh"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.2,
                    "silence_duration_ms": 800
                }
            }
        }
        ws.send(json.dumps(session_event))
        
        # Read test audio file and send
        try:
            with open("test_output.pcm", "rb") as f:
                audio_data = f.read()
            
            # Send in chunks (3200 bytes = 100ms at 16kHz)
            chunk_size = 3200
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                encoded = base64.b64encode(chunk).decode('utf-8')
                
                audio_event = {
                    "event_id": f"event_audio_{i}",
                    "type": "input_audio_buffer.append",
                    "audio": encoded
                }
                ws.send(json.dumps(audio_event))
            
            # Commit the audio buffer
            commit_event = {
                "event_id": "event_commit_001",
                "type": "input_audio_buffer.commit"
            }
            ws.send(json.dumps(commit_event))
            print(f"Sent {len(audio_data)} bytes of audio")
            
        except Exception as e:
            print(f"Error sending audio: {e}")
    
    # Create WebSocket app
    ws = ws_client.WebSocketApp(
        ws_url,
        header=[
            f"Authorization: Bearer {api_key}",
            "OpenAI-Beta: realtime=v1"
        ],
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Run in background thread
    def run_ws():
        ws.run_forever()
    
    thread = Thread(target=run_ws, daemon=True)
    thread.start()
    
    # Wait for result with timeout
    try:
        result = result_queue.get(timeout=30)
        if result[0] == "final" or result[0] == "partial":
            print(f"Transcription: {result[1]}")
            return True
        else:
            print(f"Error: {result[1]}")
            return False
    except:
        print("STT timeout")
        return False

if __name__ == "__main__":
    for model in models_to_try:
        success = test_stt_with_model(model)
        if success:
            print(f"✓ Model {model} works!")
            break
