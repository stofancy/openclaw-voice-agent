#!/usr/bin/env python3
"""
STT API 单元测试
"""

import sys
import os
import tempfile
import struct
import asyncio

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 激活虚拟环境
import site
site.addsitedir('venv/lib/python3.14/site-packages')

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback

class TestSTTCallback(RecognitionCallback):
    """测试用 STT 回调"""
    def __init__(self):
        self.result = ""
        
    def on_event(self, result):
        if hasattr(result, 'text'):
            self.result = result.text

def create_test_wav(duration_sec=1.0, sample_rate=16000):
    """创建测试 WAV 文件（静音）"""
    samples = int(duration_sec * sample_rate)
    audio_data = struct.pack('<' + 'h' * samples, *[0] * samples)
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        # WAV 头
        byte_rate = sample_rate * 1 * 2
        block_align = 1 * 2
        data_len = len(audio_data)
        
        header = struct.pack('<4sI4s', b'RIFF', 36 + data_len, b'WAVE')
        header += struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, sample_rate, byte_rate, block_align, 16)
        header += struct.pack('<4sI', b'data', data_len)
        
        f.write(header.encode() if isinstance(header, str) else header)
        f.write(audio_data)
        return f.name

def test_stt_api():
    """测试 STT API 调用"""
    print("="*60)
    print("🧪 STT API 单元测试")
    print("="*60)
    
    # 测试 1: Recognition 初始化
    print("\n[测试 1] Recognition 初始化...")
    try:
        callback = TestSTTCallback()
        recognition = Recognition(
            model='paraformer-v2',
            callback=callback,
            format='wav',
            sample_rate=16000,
        )
        print("✅ Recognition 初始化成功")
    except Exception as e:
        print(f"❌ Recognition 初始化失败：{e}")
        return False
    
    # 测试 2: 创建测试音频文件
    print("\n[测试 2] 创建测试音频文件...")
    try:
        test_file = create_test_wav(1.0)
        print(f"✅ 测试文件创建成功：{test_file}")
    except Exception as e:
        print(f"❌ 测试文件创建失败：{e}")
        return False
    
    # 测试 3: 调用 STT API
    print("\n[测试 3] 调用 STT API...")
    try:
        dashscope.api_key = os.getenv('ALI_BAILIAN_API_KEY', 'sk-93ae8c64a4774293bbe5669e858b5718')
        result = recognition.call(test_file)
        
        if result.status_code == 200:
            print(f"✅ STT API 调用成功 (status={result.status_code})")
            text = result.get('output', {}).get('text', '')
            print(f"   识别结果：'{text}'")
        else:
            print(f"⚠️  STT API 返回错误：{result.message}")
    except Exception as e:
        print(f"❌ STT API 调用失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file)
        except:
            pass
    
    print("\n" + "="*60)
    print("✅ STT 单元测试完成")
    print("="*60)
    return True

if __name__ == '__main__':
    success = test_stt_api()
    sys.exit(0 if success else 1)
