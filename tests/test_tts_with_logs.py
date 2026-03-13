#!/usr/bin/env python3
import pytest
"""
TTS 播放测试 - 带详细日志
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_tts():
    """测试 TTS 播放"""
    print("="*80)
    print("🧪 TTS 播放测试 - 详细日志")
    print("="*80)
    
    async with async_playwright() as p:
        # 尝试连接到已有 Chrome 浏览器
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 连接到 Chrome")
        except Exception as e:
            print(f"⚠️  无法连接，启动新浏览器：{e}")
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--autoplay-policy=no-user-gesture-required',
                    '--remote-debugging-port=9222'
                ]
            )
            print("✅ 启动 Chrome")
        
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        await context.grant_permissions(['microphone'])
        
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        # 捕获所有 Console 日志
        all_logs = []
        
        def handle_console(msg):
            text = msg.text
            all_logs.append(text)
            
            # 只打印 TTS 相关日志
            if any(kw in text for kw in ['🎵', '▶️', '✅', '❌', '[TTS', '[播放', 'playAudio']):
                print(text)
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:5173/", wait_until='networkidle')
        
        # 创建 gateway
        print("\n[2] 创建 gateway...")
        result = await page.evaluate("""
            () => new Promise((resolve) => {
                window.ttsLogs = [];
                const originalLog = console.log;
                console.log = function(...args) {
                    originalLog.apply(console, args);
                    window.ttsLogs.push(args.join(' '));
                };
                
                window.gateway = new VoiceGateway({
                    url: 'ws://localhost:8765',
                    autoPlayAudio: true,
                    onConnected: () => resolve(true),
                    onError: (e) => resolve(false)
                });
                
                window.gateway.connect();
                setTimeout(() => resolve(false), 5000);
            })
        """)
        print(f"Gateway 连接：{'✅ 成功' if result else '❌ 失败'}")
        
        if not result:
            print("❌ Gateway 连接失败")
            await browser.close()
            return 1
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 发送 TTS 音频
        print("\n[3] 发送 TTS 音频...")
        result = await page.evaluate("""
            () => {
                // 模拟 3 个音频块（模拟真实 TTS 数据）
                const testAudio1 = new Uint8Array(1024);
                const testAudio2 = new Uint8Array(1024);
                const testAudio3 = new Uint8Array(512);
                
                const base64Audio1 = btoa(String.fromCharCode.apply(null, testAudio1));
                const base64Audio2 = btoa(String.fromCharCode.apply(null, testAudio2));
                const base64Audio3 = btoa(String.fromCharCode.apply(null, testAudio3));
                
                const logs = [];
                
                // 发送 3 个音频块
                if (window.gateway && window.gateway.playAudio) {
                    logs.push('发送音频块 1');
                    window.gateway.playAudio(base64Audio1);
                    
                    setTimeout(() => {
                        logs.push('发送音频块 2');
                        window.gateway.playAudio(base64Audio2);
                    }, 100);
                    
                    setTimeout(() => {
                        logs.push('发送音频块 3');
                        window.gateway.playAudio(base64Audio3);
                    }, 200);
                }
                
                return logs;
            }
        """)
        print(f"发送结果：{result}")
        
        # 等待播放完成
        print("\n[4] 等待播放完成 (10 秒)...")
        await asyncio.sleep(10)
        
        # 获取日志
        tts_logs = await page.evaluate("() => window.ttsLogs || []")
        
        # 分析日志
        print("\n" + "="*80)
        print("📊 日志分析")
        print("="*80)
        
        play_count = sum(1 for log in tts_logs if '▶️ 开始播放' in log)
        complete_count = sum(1 for log in tts_logs if '✅ 播放完成' in log)
        error_count = sum(1 for log in tts_logs if '❌' in log)
        
        print(f"\n播放开始次数：{play_count}")
        print(f"播放完成次数：{complete_count}")
        print(f"错误次数：{error_count}")
        print(f"总日志数：{len(tts_logs)}")
        
        # 判断
        print("\n" + "="*80)
        if play_count > 0 and error_count == 0:
            print("✅ 测试通过 - 有播放且无错误")
            await browser.close()
            return 0
        elif error_count > 0:
            print("❌ 测试失败 - 有错误发生")
            print("\n错误日志:")
            for log in tts_logs:
                if '❌' in log:
                    print(f"  {log}")
            await browser.close()
            return 1
        else:
            print("❌ 测试失败 - 没有播放")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_tts())
    sys.exit(exit_code)