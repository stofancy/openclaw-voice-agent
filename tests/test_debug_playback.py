#!/usr/bin/env python3
import pytest
"""
调试播放问题
捕获所有日志和错误
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_debug():
    """调试播放"""
    print("="*80)
    print("🔍 调试播放问题")
    print("="*80)
    
    async with async_playwright() as p:
        # 尝试连接到已有 Chrome 浏览器
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("✅ 连接到已有 Chrome 浏览器")
        except Exception as e:
            print(f"⚠️  无法连接到已有 Chrome: {e}")
            print("   尝试启动新浏览器...")
            
            # 启动新浏览器（无头模式，适合CI环境）
            try:
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
                print("✅ 启动新 Chrome 浏览器成功")
            except Exception as e2:
                print(f"❌ 无法启动浏览器：{e2}")
                return
        
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        # 捕获所有日志
        all_logs = []
        errors = []
        
        def handle_console(msg):
            text = msg.text
            all_logs.append(text)
            
            # 打印所有日志
            print(f"[{msg.type}] {text}")
            
            if msg.type == 'error':
                errors.append(text)
        
        page.on('console', handle_console)
        page.on('pageerror', lambda e: errors.append(str(e)))
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:5173/")
        
        # 创建 gateway
        print("\n[2] 创建 gateway...")
        await page.evaluate("""
            () => new Promise((resolve) => {
                window.gateway = new VoiceGateway({
                    url: 'ws://localhost:8765',
                    autoPlayAudio: true,
                    onConnected: () => resolve(true),
                    onError: (e) => { console.error('Gateway 错误:', e); resolve(false); }
                });
                window.gateway.connect();
                setTimeout(() => resolve(false), 5000);
            })
        """)
        
        await asyncio.sleep(1)
        
        # 播放 3 次
        print("\n[3] 播放 3 次...")
        for i in range(3):
            print(f"\n  第 {i+1} 次播放...")
            
            await page.evaluate("""
                async (i) => {
                    console.log(`[测试] 第${i}次播放开始`);
                    
                    const samples = new Float32Array(24000);
                    const bytes = new Uint8Array(samples.length * 2);
                    const dataView = new DataView(bytes.buffer);
                    for (let j = 0; j < samples.length; j++) {
                        const int16 = Math.max(-32768, Math.min(32767, samples[j] * 32768));
                        dataView.setInt16(j * 2, int16, true);
                    }
                    const base64Audio = btoa(String.fromCharCode.apply(null, bytes));
                    
                    console.log(`[测试] 第${i}次：queue 长度=`, window.gateway.audioQueue.length);
                    console.log(`[测试] 第${i}次：isPlaying=`, window.gateway.isPlaying);
                    
                    if (window.gateway.playAudio) {
                        window.gateway.playAudio(base64Audio);
                        console.log(`[测试] 第${i}次：playAudio 调用完成`);
                    }
                    
                    await new Promise(r => setTimeout(r, 2000));
                    
                    console.log(`[测试] 第${i}次：queue 长度=`, window.gateway.audioQueue.length);
                    console.log(`[测试] 第${i}次：isPlaying=`, window.gateway.isPlaying);
                }
            """, i + 1)
            
            await asyncio.sleep(0.5)
        
        # 等待
        print("\n[4] 等待完成...")
        await asyncio.sleep(5)
        
        # 分析
        print("\n" + "="*80)
        print("📊 分析结果")
        print("="*80)
        
        print(f"\n总日志数：{len(all_logs)}")
        print(f"错误数：{len(errors)}")
        
        if errors:
            print("\n❌ 错误日志:")
            for err in errors:
                print(f"  {err}")
        
        # 检查播放状态
        play_start_count = sum(1 for log in all_logs if '▶️ 开始播放' in log)
        play_complete_count = sum(1 for log in all_logs if '✅ 播放完成' in log)
        
        print(f"\n播放开始：{play_start_count}")
        print(f"播放完成：{play_complete_count}")
        
        # 检查队列状态
        queue_logs = [log for log in all_logs if 'queue' in log.lower() or '队列' in log]
        if queue_logs:
            print(f"\n队列相关日志（最后 5 条）:")
            for log in queue_logs[-5:]:
                print(f"  {log}")
        
        await browser.close()
        
        if errors:
            print("\n❌ 发现错误，请检查上方错误日志")
            return 1
        elif play_start_count != play_complete_count:
            print(f"\n⚠️  播放次数不匹配：开始={play_start_count}, 完成={play_complete_count}")
            return 1
        else:
            print("\n✅ 测试通过")
            return 0

if __name__ == "__main__":
    exit_code = asyncio.run(test_debug())
    sys.exit(exit_code)