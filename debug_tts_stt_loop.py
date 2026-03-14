#!/usr/bin/env python3
"""
TTS → STT 闭环测试
1. 使用 TTS 生成中文语音
2. 保存为 PCM 文件
3. 使用 STT 识别该 PCM 文件
4. 对比输入和输出
"""
import os
import sys
import asyncio
import base64

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from voice_gateway.tts_service import TTSService, add_wav_header
from voice_gateway.stt_service import STTService

# 测试文本
TEST_TEXT = "你好，请帮我查询北京的天气"

async def test_tts():
    """测试 TTS 服务并保存音频"""
    print("=" * 60)
    print("步骤 1: 测试 TTS 服务")
    print("=" * 60)
    
    # 加载 API Key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('ALI_BAILIAN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    if not api_key:
        print("❌ 未找到有效的 API Key")
        return None
    
    # 创建 TTS 服务
    tts_service = TTSService(api_key)
    
    print(f"📝 输入文本: {TEST_TEXT}")
    
    try:
        # 生成语音
        result = await tts_service.synthesize(TEST_TEXT, voice="Cherry")
        
        if result:
            # 解码 Base64
            audio_bytes = base64.b64decode(result)
            
            # 检查是否为 WAV 格式
            if audio_bytes[:4] == b'RIFF':
                print(f"✅ TTS 成功! 音频大小: {len(audio_bytes)} 字节 (WAV格式)")
                # 提取 PCM 数据 (跳过 WAV 头)
                pcm_data = audio_bytes[44:]
                print(f"   PCM 数据大小: {len(pcm_data)} 字节")
            else:
                print(f"⚠️  TTS 返回非 WAV 格式, 大小: {len(audio_bytes)} 字节")
                pcm_data = audio_bytes
            
            # 保存 PCM 文件
            pcm_path = "test_audio.pcm"
            with open(pcm_path, 'wb') as f:
                f.write(pcm_data)
            print(f"💾 已保存 PCM 到: {pcm_path}")
            
            return pcm_path
        else:
            print("❌ TTS 失败: 返回 None")
            return None
            
    except Exception as e:
        print(f"💥 TTS 异常: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_stt(pcm_path):
    """测试 STT 服务"""
    print("\n" + "=" * 60)
    print("步骤 2: 测试 STT 服务")
    print("=" * 60)
    
    if not pcm_path or not os.path.exists(pcm_path):
        print("❌ PCM 文件不存在")
        return None
    
    # 加载 API Key
    api_key = None
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('ALI_BAILIAN_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    # 读取 PCM 文件并编码为 Base64
    with open(pcm_path, 'rb') as f:
        pcm_data = f.read()
    
    audio_b64 = base64.b64encode(pcm_data).decode('utf-8')
    print(f"📡 发送音频到 STT 服务...")
    print(f"   PCM 大小: {len(pcm_data)} 字节")
    print(f"   Base64 长度: {len(audio_b64)} 字符")
    
    # 创建 STT 服务
    stt_service = STTService(api_key)
    
    try:
        # 增加超时时间
        result = await asyncio.wait_for(stt_service.transcribe(audio_b64), timeout=60.0)
        
        if result:
            print(f"✅ STT 成功! 识别结果: '{result}'")
            return result
        else:
            print("❌ STT 失败: 返回 None")
            return None
            
    except asyncio.TimeoutError:
        print("⏰ STT 超时")
        return None
    except Exception as e:
        print(f"💥 STT 异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def compare_results(original_text, stt_result):
    """对比原始文本和 STT 识别结果"""
    print("\n" + "=" * 60)
    print("步骤 3: 结果对比")
    print("=" * 60)
    
    print(f"📝 原始文本 (TTS输入): {original_text}")
    print(f"🔍 识别结果 (STT输出): {stt_result}")
    
    # 简单对比
    if stt_result and original_text in stt_result:
        print("\n✅ 测试通过! STT 成功识别了 TTS 生成的语音")
        return True
    elif stt_result:
        print(f"\n⚠️ 部分匹配: 原始文本的 '{original_text}' vs 识别结果 '{stt_result}'")
        return False
    else:
        print("\n❌ 测试失败: STT 未返回有效结果")
        return False

async def main():
    print("=" * 60)
    print("TTS → STT 闭环测试")
    print("=" * 60)
    
    # 步骤 1: 测试 TTS
    pcm_path = await test_tts()
    if not pcm_path:
        print("\n❌ TTS 测试失败，终止流程")
        return
    
    # 步骤 2: 测试 STT
    stt_result = await test_stt(pcm_path)
    
    # 步骤 3: 对比结果
    if stt_result:
        compare_results(TEST_TEXT, stt_result)
    else:
        print("\n❌ STT 测试失败")

if __name__ == "__main__":
    asyncio.run(main())
