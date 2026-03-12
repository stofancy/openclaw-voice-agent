#!/usr/bin/env python3
"""测试 Agent 调用"""

import subprocess
import json
import sys

def test_agent_call():
    """测试调用 Architect Agent"""
    print("="*60)
    print("🧪 测试 Agent 调用")
    print("="*60)
    
    message = "[VOICE] 你好，请用一句话介绍你自己"
    
    print(f"\n📤 发送消息：{message}")
    print("⏳ 等待 Agent 回复...\n")
    
    try:
        # 方法 1: CLI 调用
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "architect", "--message", message, "--json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            reply = response.get('reply', '')
            print(f"✅ Agent 回复：{reply}")
            return True
        else:
            print(f"❌ CLI 调用失败：{result.stderr}")
            
        # 方法 2: 直接 Python 调用
        print("\n尝试方法 2: 直接 Python 调用...")
        from openclaw.cli.agent import run_agent
        # 这需要 OpenClaw 内部 API
        
    except subprocess.TimeoutExpired:
        print("⏱️  超时 (60s)")
        return False
    except Exception as e:
        print(f"❌ 错误：{e}")
        return False
    
    return False

if __name__ == "__main__":
    success = test_agent_call()
    sys.exit(0 if success else 1)
