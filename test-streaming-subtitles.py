#!/usr/bin/env python3
"""
流式字幕功能测试脚本
测试 WebSocket 字幕推送功能
"""

import asyncio
import json
import websockets
import sys

async def test_streaming_subtitles():
    """测试流式字幕推送"""
    print("=" * 60)
    print("🧪 流式字幕功能测试")
    print("=" * 60)
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            print("\n✅ WebSocket 连接成功")
            
            # 发送连接测试
            await ws.send(json.dumps({"type": "connect"}))
            response = await ws.recv()
            data = json.loads(response)
            print(f"📥 收到：{data.get('type')}")
            
            # 测试 1: 模拟用户字幕（流式）
            print("\n📝 测试 1: 用户流式字幕")
            user_text = "你好，我想查询一下去北京的机票"
            for i in range(1, len(user_text) + 1, 3):
                partial = user_text[:i]
                await ws.send(json.dumps({
                    "type": "subtitle",
                    "role": "user",
                    "text": partial,
                    "is_final": False
                }))
                print(f"  发送：{partial}")
                await asyncio.sleep(0.1)
            
            # 发送最终结果
            await ws.send(json.dumps({
                "type": "subtitle",
                "role": "user",
                "text": user_text,
                "is_final": True
            }))
            print(f"  ✅ 最终：{user_text}")
            
            # 等待并接收消息
            print("\n📥 等待网关响应...")
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=3.0)
                    data = json.loads(response)
                    msg_type = data.get('type')
                    print(f"  收到：{msg_type}")
                    
                    if msg_type == 'subtitle':
                        role = data.get('role')
                        text = data.get('text', '')
                        is_final = data.get('is_final', False)
                        print(f"    [{role}] {text[:50]}... (final={is_final})")
                    
                    if msg_type == 'reply':
                        print(f"    AI 回复：{data.get('text', '')[:50]}...")
                        
            except asyncio.TimeoutError:
                print("  ⏱️ 无更多响应")
            
            print("\n✅ 测试完成")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streaming_subtitles())
    sys.exit(0 if success else 1)
