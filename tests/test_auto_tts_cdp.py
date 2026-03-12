#!/usr/bin/env python3
"""
TTS 播放自动化测试 - 使用 CDP 连接到已有 Chrome 浏览器
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

# 存储 Console 日志
console_logs = []
tts_audio_count = 0
play_count = 0

async def test_tts_no_overlap():
    """测试 TTS 播放不重叠"""
    global console_logs, tts_audio_count, play_count
    console_logs = []
    tts_audio_count = 0
    play_count = 0
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}🧪 TTS 播放不重叠自动化测试 (CDP 模式){Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    async with async_playwright() as p:
        # 尝试连接到已有 Chrome 浏览器
        try:
            # 使用 CDP 连接到 Chrome
            browser = await p.chromium.connect_over_cdp(
                "http://localhost:9222",
                timeout=5000
            )
            print(f"{Colors.GREEN}✅ 连接到已有 Chrome 浏览器{Colors.END}")
        except Exception as e:
            print(f"{Colors.YELLOW}⚠️  无法连接到已有 Chrome: {e}{Colors.END}")
            print(f"{Colors.YELLOW}   尝试启动新浏览器...{Colors.END}")
            
            # 启动新浏览器（有头模式）
            try:
                browser = await p.chromium.launch(
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--autoplay-policy=no-user-gesture-required',
                        '--remote-debugging-port=9222'
                    ]
                )
                print(f"{Colors.GREEN}✅ 启动新 Chrome 浏览器成功{Colors.END}")
            except Exception as e2:
                print(f"{Colors.RED}❌ 无法启动浏览器：{e2}{Colors.END}")
                return 1
        
        # 获取第一个上下文和页面，并授予麦克风权限
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        
        # 授予麦克风权限
        await context.grant_permissions(['microphone'])
        
        pages = context.pages
        page = pages[0] if pages else await context.new_page()
        
        # 捕获 Console 日志
        def handle_console(msg):
            global console_logs, tts_audio_count, play_count
            text = msg.text
            
            console_logs.append({
                'type': msg.type,
                'text': text
            })
            
            # 统计关键日志
            if '🔊 收到 TTS 音频数据' in text:
                tts_audio_count += 1
                print(f"{Colors.CYAN}[TTS #{tts_audio_count}] {text}{Colors.END}")
            elif '▶️ 开始播放 TTS' in text:
                play_count += 1
                print(f"{Colors.GREEN}[播放 #{play_count}] {text}{Colors.END}")
            elif '⚠️ TTS 正在播放，跳过' in text or '⚠️ 正在播放，拒绝新音频' in text:
                print(f"{Colors.YELLOW}[防重复] {text}{Colors.END}")
            elif '❌' in text or 'Error' in text:
                print(f"{Colors.RED}[错误] {text}{Colors.END}")
        
        page.on('console', handle_console)
        
        # 导航到页面
        print(f"\n{Colors.BLUE}[步骤 1] 打开页面...{Colors.END}")
        await page.goto("http://localhost:8080/test-pages/pro-call.html", wait_until='networkidle')
        await page.wait_for_selector('#btnCall')
        print(f"{Colors.GREEN}✅ 页面加载成功{Colors.END}")
        
        # 直接创建 gateway 实例（绕过麦克风权限）
        print(f"\n{Colors.BLUE}[步骤 2] 创建 gateway 实例...{Colors.END}")
        
        gateway_created = await page.evaluate("""
            () => {
                return new Promise((resolve) => {
                    // 直接创建 gateway 实例
                    window.gateway = new VoiceGateway({
                        url: 'ws://localhost:8765',
                        autoPlayAudio: true,
                        onConnected: () => {
                            console.log('✅ Gateway 已连接');
                            resolve(true);
                        },
                        onError: (error) => {
                            console.log('❌ Gateway 错误:', error);
                            resolve(false);
                        }
                    });
                    
                    window.gateway.connect();
                    
                    // 10 秒超时
                    setTimeout(() => resolve(false), 10000);
                });
            }
        """)
        
        if not gateway_created:
            print(f"{Colors.RED}❌ Gateway 创建失败{Colors.END}")
            await browser.close()
            return 1
        
        print(f"{Colors.GREEN}✅ Gateway 已创建并连接{Colors.END}")
        
        # 直接触发 TTS 播放
        print(f"\n{Colors.BLUE}[步骤 3] 触发 TTS 播放...{Colors.END}")
        
        # 模拟 TTS 音频数据并检查 Console 日志
        result = await page.evaluate("""
            () => {
                const testAudio = new Uint8Array(1024);
                const base64Audio = btoa(String.fromCharCode.apply(null, testAudio));
                
                const logs = [];
                const originalLog = console.log;
                console.log = function(...args) {
                    originalLog.apply(console, args);
                    logs.push(args.join(' '));
                };
                
                let success = false;
                if (window.gateway && window.gateway.playAudio) {
                    window.gateway.playAudio(base64Audio);
                    success = true;
                    logs.push('playAudio 调用成功');
                } else {
                    logs.push('playAudio 不存在');
                }
                
                // 等待一下看是否有日志
                return { success, logs };
            }
        """)
        print(f"播放结果：{result}")
        if result.get('logs'):
            print(f"Console 日志：{result['logs']}")
        
        # 等待 TTS 播放完成（最多 20 秒）
        print(f"\n{Colors.BLUE}[步骤 4] 等待 TTS 播放完成 (20 秒)...{Colors.END}")
        for i in range(20):
            await asyncio.sleep(1)
            # 检查是否有 TTS 日志
            if tts_audio_count > 0:
                print(f"{Colors.GREEN}✅ 收到 TTS 音频！{Colors.END}")
                break
        
        # 分析日志
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BLUE}📊 测试结果分析{Colors.END}")
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        
        print(f"\n收到 TTS 音频次数：{tts_audio_count}")
        print(f"开始播放次数：{play_count}")
        
        # 检查防重复机制
        overlap_detected = False
        skip_count = 0
        
        for log in console_logs:
            text = log['text']
            if '⚠️ TTS 正在播放，跳过' in text or '⚠️ 正在播放，拒绝新音频' in text:
                skip_count += 1
            if '已在播放，加入队列' in text:
                overlap_detected = True
                print(f"{Colors.RED}❌ 检测到重叠：{text}{Colors.END}")
        
        print(f"\n防重复触发次数：{skip_count}")
        
        # 最终判断
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
        
        # 首先检查是否收到 TTS 音频
        if tts_audio_count == 0:
            print(f"{Colors.RED}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.RED}║  ❌ 测试失败 - 没有收到 TTS 音频                                 ║{Colors.END}")
            print(f"{Colors.RED}║     说明：网关没有发送 TTS 或前端没有正确处理                   ║{Colors.END}")
            print(f"{Colors.RED}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            await browser.close()
            return 1
        
        if overlap_detected:
            print(f"{Colors.RED}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.RED}║  ❌ TTS 播放重叠检测成功 - 发现问题                              ║{Colors.END}")
            print(f"{Colors.RED}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            await browser.close()
            return 1
        elif play_count == 1:
            print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.GREEN}║  ✅ TTS 播放测试通过 - 收到音频且没有重叠                       ║{Colors.END}")
            print(f"{Colors.GREEN}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            await browser.close()
            return 0
        else:
            print(f"{Colors.YELLOW}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.YELLOW}║  ⚠️  TTS 播放 {play_count} 次 - 可能有多余播放                           ║{Colors.END}")
            print(f"{Colors.YELLOW}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            await browser.close()
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_tts_no_overlap())
    sys.exit(exit_code)
