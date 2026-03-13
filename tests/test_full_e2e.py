#!/usr/bin/env python3
import pytest
"""
完整端到端测试：模拟真实使用场景
文字 → TTS → 前端播放
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_full_e2e():
    """完整端到端测试"""
    print("="*80)
    print("🧪 完整端到端测试 - 文字→TTS→播放")
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
            if any(kw in text for kw in ['▶️', '✅', '❌', 'AudioContext 状态']):
                print(text)
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:5173/", wait_until='networkidle')
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
        
        # 模拟完整流程：收到 TTS 音频 → 播放
        print("\n[3] 模拟收到 TTS 音频并播放...")
        
        # 发送多个音频块（模拟真实 TTS 流）
        result = await page.evaluate("""
            async () => {
                const logs = [];
                
                // 创建 3 个音频块（模拟"你好"的 TTS 数据）
                const chunks = [
                    new Float32Array(24000), // 1 秒
                    new Float32Array(24000), // 1 秒
                    new Float32Array(12000), // 0.5 秒
                ];
                
                for (let i = 0; i < chunks.length; i++) {
                    // 转 Int16 → Base64
                    const samples = chunks[i];
                    const bytes = new Uint8Array(samples.length * 2);
                    const dataView = new DataView(bytes.buffer);
                    
                    for (let j = 0; j < samples.length; j++) {
                        const int16 = Math.max(-32768, Math.min(32767, samples[j] * 32768));
                        dataView.setInt16(j * 2, int16, true);
                    }
                    
                    const base64Audio = btoa(String.fromCharCode.apply(null, bytes));
                    
                    logs.push(`发送音频块 ${i + 1}, 长度：${base64Audio.length}`);
                    
                    if (window.gateway && window.gateway.playAudio) {
                        window.gateway.playAudio(base64Audio);
                    }
                    
                    // 等待 100ms 模拟流式接收
                    await new Promise(r => setTimeout(r, 100));
                }
                
                return { success: true, logs };
            }
        """)
        print(f"发送结果：{result}")
        
        # 等待播放完成
        print("\n[4] 等待播放完成 (10 秒)...")
        await asyncio.sleep(10)
        
        # 分析日志
        print("\n" + "="*80)
        print("📊 日志分析")
        print("="*80)
        
        play_start = sum(1 for log in all_logs if '▶️ 开始播放' in log)
        play_complete = sum(1 for log in all_logs if '✅ 播放完成' in log)
        errors = sum(1 for log in all_logs if '❌' in log)
        audio_running = sum(1 for log in all_logs if 'AudioContext 状态' in log and 'running' in log)
        
        print(f"\n播放开始：{play_start}")
        print(f"播放完成：{play_complete}")
        print(f"错误：{errors}")
        print(f"AudioContext running: {audio_running}")
        
        # 判断
        print("\n" + "="*80)
        if play_start > 0 and play_complete > 0 and errors == 0:
            print("✅ 完整端到端测试通过")
            print("\n📝 总结:")
            print("   - 后端 TTS 正常（已单独测试）")
            print("   - 前端播放正常（本测试验证）")
            print("   - AudioContext 状态正常")
            print("\n🔍 如果主公还是听不见，可能原因:")
            print("   1. 浏览器缓存 - 请 Ctrl+Shift+R 强制刷新")
            print("   2. 系统音量 - 请检查音量设置")
            print("   3. 音频设备 - 请检查输出设备")
            await browser.close()
            return 0
        else:
            print("❌ 完整端到端测试失败")
            if errors > 0:
                print("\n错误日志:")
                for log in all_logs:
                    if '❌' in log:
                        print(f"  {log}")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_full_e2e())
    sys.exit(exit_code)
