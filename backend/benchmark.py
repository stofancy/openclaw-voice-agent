#!/usr/bin/env python3
"""
Voice Gateway 基准测试脚本
测量各环节延迟：STT、Agent、TTS、端到端
"""
import os
import sys
import time
import asyncio
import base64
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from voice_gateway.config import Config
from voice_gateway.stt_service import STTService
from voice_gateway.agent_client import AgentClient
from voice_gateway.tts_service import TTSService


class Benchmark:
    def __init__(self):
        self.config = Config()
        self.results = []
    
    async def run(self):
        print("=" * 60)
        print("Voice Gateway 基准测试")
        print("=" * 60)
        
        # 测试用例
        test_cases = [
            ("短句", "你好"),
            ("中句", "今天天气怎么样"),
            ("长句", "帮我订一张去北京的机票"),
        ]
        
        for name, text in test_cases:
            print(f"\n--- 测试: {name} ---")
            print(f"输入: {text}")
            
            # 1. 模拟 STT (使用文本反转模拟)
            stt_start = time.time()
            # 实际 STT 会更慢，这里模拟
            await asyncio.sleep(0.1)  # 模拟网络延迟
            stt_latency = time.time() - stt_start
            print(f"STT: {stt_latency*1000:.0f}ms")
            
            # 2. Agent 响应
            agent_start = time.time()
            agent_response = await self._test_agent(text)
            agent_latency = time.time() - agent_start
            print(f"Agent: {agent_latency*1000:.0f}ms")
            
            # 3. TTS 合成
            tts_start = time.time()
            audio = await self._test_tts(agent_response)
            tts_latency = time.time() - tts_start
            print(f"TTS: {tts_latency*1000:.0f}ms")
            
            # 4. 端到端
            total = stt_latency + agent_latency + tts_latency
            print(f"端到端: {total*1000:.0f}ms")
            
            self.results.append({
                "name": name,
                "text": text,
                "stt": stt_latency,
                "agent": agent_latency,
                "tts": tts_latency,
                "total": total
            })
        
        self._print_summary()
    
    async def _test_agent(self, text: str) -> str:
        """测试 Agent 响应时间"""
        from voice_gateway.agent_client import AgentClient
        client = AgentClient()
        return await client.process_message(text)
    
    async def _test_tts(self, text: str) -> str:
        """测试 TTS 合成时间"""
        from voice_gateway.tts_service import TTSService
        service = TTSService(self.config.bailian_api_key)
        return await service.synthesize(text)
    
    def _print_summary(self):
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"{'测试':<10} {'STT':<10} {'Agent':<10} {'TTS':<10} {'总计':<10}")
        print("-" * 60)
        for r in self.results:
            print(f"{r['name']:<10} {r['stt']*1000:>7.0f}ms {r['agent']*1000:>7.0f}ms {r['tts']*1000:>7.0f}ms {r['total']*1000:>7.0f}ms")


async def main():
    benchmark = Benchmark()
    await benchmark.run()


if __name__ == "__main__":
    asyncio.run(main())
