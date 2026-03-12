#!/usr/bin/env python3
"""
简单 TTS 测试 - 直接播放测试音频
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

async def test_simple_tts():
    """简单 TTS 测试"""
    print("="*80)
    print("🧪 简单 TTS 测试 - 直接播放")
    print("="*80)
    
    async with async_playwright() as p:
        # 连接到已有 Chrome
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 连接到 Chrome")
        except Exception as e:
            print(f"⚠️  无法连接，启动新浏览器：{e}")
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
            
            # 打印 TTS 相关日志
            if any(kw in text for kw in ['🎵', '▶️', '✅', '❌', '[TTS', '[播放', 'playAudio']):
                print(text)
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('#btnCall')
        print("✅ 页面加载成功")
        
        # 创建 gateway
        print("\n[2] 创建 gateway...")
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
        
        # 直接播放测试音频
        print("\n[3] 播放测试音频...")
        result = await page.evaluate("""
            () => {
                // 创建测试音频数据（静音 PCM 数据）
                const samples = new Float32Array(24000); // 1 秒静音
                const bytes = new Uint8Array(samples.length * 2);
                const dataView = new DataView(bytes.buffer);
                
                for (let i = 0; i < samples.length; i++) {
                    const int16 = Math.max(-32768, Math.min(32767, samples[i] * 32768));
                    dataView.setInt16(i * 2, int16, true);
                }
                
                const base64Audio = btoa(String.fromCharCode.apply(null, bytes));
                
                console.log('准备播放测试音频，长度:', base64Audio.length, 'bytes');
                
                if (window.gateway && window.gateway.playAudio) {
                    window.gateway.playAudio(base64Audio);
                    return { success: true, audioLength: base64Audio.length };
                }
                return { success: false, error: 'playAudio 不存在' };
            }
        """)
        print(f"播放结果：{result}")
        
        # 等待播放
        print("\n[4] 等待播放完成 (5 秒)...")
        await asyncio.sleep(5)
        
        # 分析日志
        print("\n" + "="*80)
        print("📊 日志分析")
        print("="*80)
        
        play_start = sum(1 for log in all_logs if '▶️ 开始播放' in log)
        play_complete = sum(1 for log in all_logs if '✅ 播放完成' in log)
        errors = sum(1 for log in all_logs if '❌' in log and '播放' in log)
        
        print(f"\n播放开始：{play_start}")
        print(f"播放完成：{play_complete}")
        print(f"播放错误：{errors}")
        
        # 判断
        print("\n" + "="*80)
        if play_start > 0 and play_complete > 0 and errors == 0:
            print("✅ 测试通过 - TTS 播放正常")
            await browser.close()
            return 0
        else:
            print("❌ 测试失败")
            if errors > 0:
                print("\n错误日志:")
                for log in all_logs:
                    if '❌' in log:
                        print(f"  {log}")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_simple_tts())
    sys.exit(exit_code)
