#!/usr/bin/env python3
"""
测试 gateway 实例不叠加
模拟多次创建 gateway，验证只有一个实例在工作
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

async def test_no_overlap():
    """测试 gateway 不叠加"""
    print("="*80)
    print("🧪 测试 gateway 实例不叠加")
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
            if '清理旧的 gateway' in text or 'VoiceGateway 已连接' in text:
                print(text)
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:8080/test-pages/pro-call.html", wait_until='networkidle')
        print("✅ 页面加载成功")
        
        # 模拟多次创建 gateway
        print("\n[2] 模拟 3 次创建 gateway...")
        
        for i in range(3):
            print(f"\n  第 {i+1} 次创建 gateway...")
            
            result = await page.evaluate("""
                async () => {
                    const logs = [];
                    
                    // 清理旧的
                    if (window.gateway) {
                        logs.log = function(msg) { console.log(msg); };
                        logs.log('🧹 清理旧的 gateway...');
                        if (window.gateway.stopAudio) {
                            window.gateway.stopAudio();
                        }
                        if (window.gateway.disconnect) {
                            window.gateway.disconnect();
                        }
                        window.gateway = null;
                    }
                    
                    // 创建新的
                    await new Promise((resolve) => {
                        window.gateway = new VoiceGateway({
                            url: 'ws://localhost:8765',
                            autoPlayAudio: true,
                            onConnected: () => {
                                logs.log('✅ VoiceGateway 已连接');
                                resolve(true);
                            },
                            onError: () => resolve(false)
                        });
                        window.gateway.connect();
                        setTimeout(() => resolve(false), 3000);
                    });
                    
                    // 播放测试音频
                    const samples = new Float32Array(24000);
                    const bytes = new Uint8Array(samples.length * 2);
                    const dataView = new DataView(bytes.buffer);
                    for (let j = 0; j < samples.length; j++) {
                        const int16 = Math.max(-32768, Math.min(32767, samples[j] * 32768));
                        dataView.setInt16(j * 2, int16, true);
                    }
                    const base64Audio = btoa(String.fromCharCode.apply(null, bytes));
                    
                    if (window.gateway && window.gateway.playAudio) {
                        window.gateway.playAudio(base64Audio);
                        logs.log('▶️ 播放测试音频');
                    }
                    
                    return logs;
                }
            """)
            
            await asyncio.sleep(1)
        
        # 等待播放完成
        print("\n[3] 等待播放完成 (5 秒)...")
        await asyncio.sleep(5)
        
        # 分析日志
        print("\n" + "="*80)
        print("📊 日志分析")
        print("="*80)
        
        cleanup_count = sum(1 for log in all_logs if '清理旧的 gateway' in log)
        connect_count = sum(1 for log in all_logs if 'VoiceGateway 已连接' in log)
        play_count = sum(1 for log in all_logs if '▶️ 开始播放' in log or '播放测试音频' in log)
        complete_count = sum(1 for log in all_logs if '✅ 播放完成' in log)
        
        print(f"\n清理旧 gateway: {cleanup_count}")
        print(f"连接成功：{connect_count}")
        print(f"播放开始：{play_count}")
        print(f"播放完成：{complete_count}")
        
        # 判断
        print("\n" + "="*80)
        if cleanup_count == 2 and connect_count == 3 and play_count <= 3:
            print("✅ 测试通过 - gateway 没有叠加")
            print("\n📝 说明:")
            print("   - 第 1 次创建：没有清理（正常）")
            print("   - 第 2 次创建：清理 1 个旧的（正常）")
            print("   - 第 3 次创建：清理 1 个旧的（正常）")
            print("   - 播放次数 <= 3（正常，没有叠加）")
            await browser.close()
            return 0
        else:
            print("❌ 测试失败 - gateway 可能叠加")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_no_overlap())
    sys.exit(exit_code)
