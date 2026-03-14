#!/usr/bin/env python3
"""
使用真实音频文件测试 STT 服务
"""
import os
import sys
import asyncio
import base64

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.stt_service import STTService

async def create_test_audio():
    """创建一个真实的测试音频文件 (1秒静音 + 语音)"""
    import subprocess
    import tempfile
    
    # 创建 2 秒的静音音频 (16kHz, mono, PCM)
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        output_path = f.name
    
    try:
        # 使用 ffmpeg 生成测试音频
        result = subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
            '-ar', '16000', '-ac', '1', '-y', output_path
        ], capture_output=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ 音频生成失败: {result.stderr.decode()}")
            return None
            
        # 读取音频文件并转换为 base64
        with open(output_path, 'rb') as f:
            audio_data = f.read()
            
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"✅ 测试音频创建成功: {len(audio_data)} 字节")
        return audio_b64
        
    finally:
        # 清理临时文件
        if os.path.exists(output_path):
            os.unlink(output_path)

async def test_stt_with_real_audio():
    """使用真实音频测试 STT"""
    print("🔍 开始真实音频 STT 测试...")
    
    # 加载 API Key
    api_key = None
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('ALI_BAILIAN_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    except FileNotFoundError:
        print("❌ 未找到 .env 文件")
        return False
    
    if not api_key:
        print("❌ 未找到有效的 API Key")
        return False
    
    # 创建测试音频
    audio_b64 = await create_test_audio()
    if not audio_b64:
        return False
    
    # 创建 STT 服务
    stt_service = STTService(api_key)
    
    print(f"📡 发送真实音频到 STT 服务...")
    print(f"   Base64 长度: {len(audio_b64)} 字符")
    
    try:
        # 增加超时时间到 60 秒
        import asyncio
        result = await asyncio.wait_for(stt_service.transcribe(audio_b64), timeout=60.0)
        
        if result is not None:
            print(f"✅ STT 成功! 结果: '{result}'")
            return True
        else:
            print("❌ STT 失败: 返回 None")
            return False
            
    except asyncio.TimeoutError:
        print("⏰ STT 超时 (60秒)")
        return False
    except Exception as e:
        print(f"💥 STT 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("真实音频 STT 调试测试")
    print("=" * 60)
    
    asyncio.run(test_stt_with_real_audio())