#!/usr/bin/env python3
"""
测试多轮对话场景
模拟：一次拨号，多次 Agent 回复
验证队列是否正确清理
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

async def test_multi_turn():
    """测试多轮对话"""
    print("="*80)
    print("🧪 多轮对话测试 - 一次拨号，多次回复")
    print("="*80)
    
    async with async_playwright() as p:
        # 连接到已有 Chrome
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 连接到 Chrome")
        except:
            browser = await p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--remote-debugging-port=9222']
            )
            print("✅ 启动 Chrome")
        
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 捕获 Console 日志
        all_logs = []
        
        def handle_console(msg):
            text = msg.text
            all_logs.append(text)
            
            # 打印关键日志
            if any(kw in text for kw in ['▶️', '✅', '❌', 'queue', '队列', 'AudioContext']):
                print(text)
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:8080/test-pages/pro-call.html", wait_until='networkidle')
        print("✅ 页面加载成功")
        
        # 创建 gateway（模拟拨号）
        print("\n[2] 创建 gateway（模拟拨号）...")
        connected = await page.evaluate("""
            () => new Promise((resolve) => {
                window.gateway = new VoiceGateway({
                    url: 'ws://localhost:8765',
                    autoPlayAudio: true,
                    onConnected: () => resolve(true),
                    onError: () => resolve(false)
                });
                window.gateway.connect();
                setTimeout(() => resolve(false), 5000);
            })
        """)
        print(f"Gateway: {'✅ 已连接' if connected else '❌ 未连接'}")
        
        if not connected:
            print("❌ Gateway 连接失败")
            await browser.close()
            return 1
        
        await asyncio.sleep(1)
        
        # 模拟多轮对话（3 轮）
        print("\n[3] 模拟 3 轮对话...")
        
        for i in range(3):
            print(f"\n  第 {i+1} 轮对话...")
            
            # 发送 TTS 音频（模拟 Agent 回复）
            result = await page.evaluate("""
                async (round) => {
                    const logs = [];
                    
                    // 创建音频数据（模拟 TTS）
                    const samples = new Float32Array(24000); // 1 秒
                    const bytes = new Uint8Array(samples.length * 2);
                    const dataView = new DataView(bytes.buffer);
                    
                    for (let j = 0; j < samples.length; j++) {
                        const int16 = Math.max(-32768, Math.min(32767, samples[j] * 32768));
                        dataView.setInt16(j * 2, int16, true);
                    }
                    
                    const base64Audio = btoa(String.fromCharCode.apply(null, bytes));
                    
                    logs.log = function(msg) { console.log(msg); };
                    logs.log(`[第${round}轮] 准备播放 TTS...`);
                    
                    if (window.gateway && window.gateway.playAudio) {
                        window.gateway.playAudio(base64Audio);
                        logs.log(`[第${round}轮] 播放开始`);
                    }
                    
                    // 等待播放
                    await new Promise(r => setTimeout(r, 1500));
                    
                    // 检查队列状态
                    const queueLength = window.gateway ? window.gateway.audioQueue.length : -1;
                    const isPlaying = window.gateway ? window.gateway.isPlaying : -1;
                    logs.log(`[第${round}轮] 队列长度：${queueLength}, isPlaying: ${isPlaying}`);
                    
                    return { round, success: true, queueLength, isPlaying };
                }
            """, i + 1)
            
            print(f"  结果：{result}")
            await asyncio.sleep(0.5)
        
        # 等待所有播放完成
        print("\n[4] 等待所有播放完成 (5 秒)...")
        await asyncio.sleep(5)
        
        # 分析日志
        print("\n" + "="*80)
        print("📊 日志分析")
        print("="*80)
        
        play_start = sum(1 for log in all_logs if '▶️ 开始播放' in log)
        play_complete = sum(1 for log in all_logs if '✅ 播放完成' in log)
        errors = sum(1 for log in all_logs if '❌' in log)
        queue_logs = [log for log in all_logs if 'queue' in log.lower() or '队列' in log]
        
        print(f"\n播放开始：{play_start}")
        print(f"播放完成：{play_complete}")
        print(f"错误：{errors}")
        if queue_logs:
            print(f"队列日志：{len(queue_logs)}")
            for log in queue_logs[-5:]:
                print(f"  {log}")
        
        # 判断
        print("\n" + "="*80)
        if play_start == 3 and play_complete == 3 and errors == 0:
            print("✅ 多轮对话测试通过 - 每次播放一次，没有叠加")
            await browser.close()
            return 0
        elif errors > 0:
            print("❌ 多轮对话测试失败 - 有错误")
            print("\n错误日志:")
            for log in all_logs:
                if '❌' in log:
                    print(f"  {log}")
            await browser.close()
            return 1
        else:
            print(f"⚠️  播放次数不匹配：开始={play_start}, 完成={play_complete}")
            print("   可能原因：队列没有清空，导致叠加播放")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_multi_turn())
    sys.exit(exit_code)
