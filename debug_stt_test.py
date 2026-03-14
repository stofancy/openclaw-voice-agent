#!/usr/bin/env python3
"""
独立 STT 调试测试脚本
用于直接测试 STT 服务，绕过前端和 WebSocket
"""
import os
import sys
import asyncio
import base64

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.stt_service import STTService

async def test_stt_with_mock_audio():
    """使用模拟音频数据测试 STT"""
    print("🔍 开始 STT 独立测试...")
    
    # 从 .env 加载 API Key
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
    
    if not api_key or api_key == 'sk-93ae8c64a4774293bbe5669e858b5718':
        print("⚠️  使用默认 API Key (可能已失效)")
    
    # 创建 STT 服务实例
    stt_service = STTService(api_key)
    
    # 创建模拟的 WebM 音频数据 (base64 编码)
    # 这里使用一个简单的 PCM 数据作为测试
    mock_pcm_data = bytes([0] * 3200)  # 100ms 的静音 PCM 数据
    mock_audio_b64 = base64.b64encode(mock_pcm_data).decode('utf-8')
    
    print(f"📡 发送模拟音频数据到 STT 服务...")
    print(f"   音频长度: {len(mock_pcm_data)} 字节")
    print(f"   Base64 长度: {len(mock_audio_b64)} 字符")
    
    try:
        # 测试 STT 转录
        result = await stt_service.transcribe(mock_audio_b64)
        
        if result is not None:
            print(f"✅ STT 成功! 结果: '{result}'")
            return True
        else:
            print("❌ STT 失败: 返回 None")
            return False
            
    except Exception as e:
        print(f"💥 STT 异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_stt_conversion():
    """测试 WebM 到 PCM 的转换功能"""
    print("\n🔍 测试 WebM 到 PCM 转换...")
    
    # 创建 STT 服务实例 (API Key 可以为 None，因为只测试转换)
    stt_service = STTService("dummy-key")
    
    # 创建模拟的 WebM 数据
    mock_webm_data = "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDEAAAAIZnJlZQAAAgBtZGF0AAACrwYF"
    # 这是一个简短的 WebM header 的 base64
    
    try:
        pcm_result = stt_service._convert_webm_to_pcm(mock_webm_data)
        if pcm_result:
            print("✅ WebM 到 PCM 转换成功")
            return True
        else:
            print("⚠️  WebM 到 PCM 转换失败 (可能缺少 ffmpeg 或无效数据)")
            return False
    except Exception as e:
        print(f"💥 WebM 转换异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("STT 独立调试测试")
    print("=" * 60)
    
    # 检查 ffmpeg 是否可用
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ ffmpeg 可用")
        else:
            print("❌ ffmpeg 不可用")
    except Exception as e:
        print(f"❌ ffmpeg 检查失败: {e}")
    
    print()
    
    # 运行测试
    async def run_tests():
        conversion_ok = await test_stt_conversion()
        stt_ok = await test_stt_with_mock_audio()
        
        print("\n" + "=" * 60)
        print("测试结果总结:")
        print(f"  WebM→PCM 转换: {'✅' if conversion_ok else '❌'}")
        print(f"  STT 服务调用: {'✅' if stt_ok else '❌'}")
        print("=" * 60)
    
    asyncio.run(run_tests())