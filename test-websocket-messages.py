#!/usr/bin/env python3
"""
WebSocket 消息格式测试
验证新消息类型：stt_partial, stt_final, llm_token, llm_complete
"""

import asyncio
import json
import websockets
import sys

async def test_message_types():
    """测试新消息类型"""
    print("=" * 60)
    print("🧪 WebSocket 消息格式测试")
    print("=" * 60)
    
    try:
        async with websockets.connect("ws://localhost:8765") as ws:
            print("\n✅ WebSocket 连接成功")
            
            # 发送连接测试
            await ws.send(json.dumps({"type": "connect"}))
            response = await ws.recv()
            data = json.loads(response)
            print(f"📥 收到：{data.get('type')}")
            
            # 测试发送 stt_partial（模拟）
            print("\n📝 测试：发送 stt_partial（模拟用户说话）")
            test_text = "你好"
            await ws.send(json.dumps({
                "type": "test_stt_partial",
                "text": test_text
            }))
            print(f"  发送：stt_partial = {test_text}")
            
            # 接收并验证消息
            print("\n📥 接收消息验证...")
            received_types = []
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(response)
                    msg_type = data.get('type')
                    received_types.append(msg_type)
                    print(f"  收到：{msg_type}")
                    
                    if msg_type == 'stt_partial':
                        print(f"    ✅ text: {data.get('text')}")
                    elif msg_type == 'stt_final':
                        print(f"    ✅ text: {data.get('text')}")
                    elif msg_type == 'llm_token':
                        print(f"    ✅ text: {data.get('text')}")
                    elif msg_type == 'llm_complete':
                        print(f"    ✅ text: {data.get('text')[:50]}...")
                        
            except asyncio.TimeoutError:
                print("  ⏱️ 无更多响应")
            
            # 验证收到的消息类型
            print("\n📊 验证结果:")
            expected_types = ['stt_partial', 'stt_final', 'llm_complete']
            for expected in expected_types:
                if expected in received_types:
                    print(f"  ✅ {expected} - 收到")
                else:
                    print(f"  ❌ {expected} - 未收到")
            
            print("\n✅ 测试完成")
            return True
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_message_types())
    sys.exit(0 if success else 1)
