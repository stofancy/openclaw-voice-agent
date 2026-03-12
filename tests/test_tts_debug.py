#!/usr/bin/env python3
"""
TTS 播放调试测试 - 使用 Playwright 自动测试并捕获 Console 日志
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

async def test_tts_playback():
    """测试 TTS 播放完整流程"""
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}🧪 TTS 播放调试测试 - 自动捕获 Console 日志{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    async with async_playwright() as p:
        # 启动浏览器（headless 模式，但添加 WebSocket 支持参数）
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--websocket-port=9222'
            ]
        )
        
        # 创建新页面
        page = await browser.new_page()
        
        # 捕获 Console 日志
        def handle_console(msg):
            console_logs.append({
                'type': msg.type,
                'text': msg.text
            })
            # 打印彩色日志
            text = msg.text
            if '🔊' in text or '🎵' in text or '▶️' in text or '✅' in text:
                print(f"{Colors.CYAN}[Console] {text}{Colors.END}")
            elif '❌' in text or 'Error' in text:
                print(f"{Colors.RED}[Console] {text}{Colors.END}")
            elif '⚠️' in text or 'Warning' in text:
                print(f"{Colors.YELLOW}[Console] {text}{Colors.END}")
            else:
                print(f"[Console] {text}")
        
        page.on('console', handle_console)
        
        # 导航到页面
        print(f"\n{Colors.BLUE}[步骤 1] 打开页面...{Colors.END}")
        try:
            await page.goto("http://localhost:8080/test-pages/pro-call.html", wait_until='networkidle')
            await page.wait_for_selector('#btnCall')
            print(f"{Colors.GREEN}✅ 页面加载成功{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}❌ 页面加载失败：{e}{Colors.END}")
            # 继续测试，可能页面已加载
        
        # 点击拨号
        print(f"\n{Colors.BLUE}[步骤 2] 点击拨号...{Colors.END}")
        await page.click('#btnCall')
        await asyncio.sleep(1)
        
        # 创建新上下文并允许麦克风
        context = await browser.new_context()
        page = await context.new_page()
        
        # 重新绑定 Console 处理器到新页面
        page.on('console', handle_console)
        
        print(f"{Colors.YELLOW}⚠️  注意：Playwright headless 模式下麦克风权限可能不可用{Colors.END}")
        
        await asyncio.sleep(2)
        
        # 模拟说话（通过 JavaScript 触发）
        print(f"\n{Colors.BLUE}[步骤 3] 模拟说话...{Colors.END}")
        await page.evaluate("""
            if (window.isMuted !== undefined) {
                window.isMuted = false;
            }
            if (window.isSpeaking !== undefined) {
                window.isSpeaking = true;
            }
        """)
        await asyncio.sleep(2)
        
        # 模拟发送 STT 结果
        print(f"\n{Colors.BLUE}[步骤 4] 发送 STT 结果...{Colors.END}")
        await page.evaluate("""
            if (window.gateway && window.gateway.sendSTTResult) {
                window.gateway.sendSTTResult('你好');
            }
        """)
        await asyncio.sleep(10)  # 等待 Agent 回复和 TTS 播放
        
        # 检查播放状态
        print(f"\n{Colors.BLUE}[步骤 5] 检查播放状态...{Colors.END}")
        is_playing = await page.evaluate("window._isPlayingTTS")
        print(f"   _isPlayingTTS: {is_playing}")
        
        # 检查 AudioContext
        has_audio_context = await page.evaluate("""
            window.gateway && window.gateway.audioContext !== null && window.gateway.audioContext !== undefined
        """)
        print(f"   gateway.audioContext: {'存在' if has_audio_context else '不存在'}")
        
        # 检查音频队列
        queue_length = await page.evaluate("""
            window.gateway && window.gateway.audioQueue ? window.gateway.audioQueue.length : -1
        """)
        print(f"   audioQueue 长度：{queue_length}")
        
        # 等待播放完成
        print(f"\n{Colors.BLUE}[步骤 6] 等待播放完成 (10 秒)...{Colors.END}")
        await asyncio.sleep(10)
        
        # 分析日志
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BLUE}📊 日志分析{Colors.END}")
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        
        # 关键日志检查
        checks = {
            '收到 TTS 音频数据': False,
            '开始播放 TTS': False,
            '_playAudioBase64': False,
            '_playNextInQueue': False,
            '创建 AudioContext': False,
            '开始播放': False,
            'TTS 播放完成': False,
        }
        
        for log in console_logs:
            text = log['text']
            if '收到 TTS 音频数据' in text:
                checks['收到 TTS 音频数据'] = True
            if '开始播放 TTS' in text:
                checks['开始播放 TTS'] = True
            if '_playAudioBase64' in text:
                checks['_playAudioBase64'] = True
            if '_playNextInQueue' in text:
                checks['_playNextInQueue'] = True
            if '创建 AudioContext' in text:
                checks['创建 AudioContext'] = True
            if '开始播放' in text:
                checks['开始播放'] = True
            if 'TTS 播放完成' in text:
                checks['TTS 播放完成'] = True
        
        # 打印检查结果
        all_passed = True
        for check_name, passed in checks.items():
            status = f"{Colors.GREEN}✅{Colors.END}" if passed else f"{Colors.RED}❌{Colors.END}"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        # 错误检查
        errors = [log for log in console_logs if '❌' in log['text'] or 'Error' in log['text'] or 'error' in log['text']]
        if errors:
            print(f"\n{Colors.RED}发现 {len(errors)} 个错误:{Colors.END}")
            for error in errors:
                print(f"  - {error['text']}")
        else:
            print(f"\n{Colors.GREEN}✅ 未发现错误{Colors.END}")
        
        # 关闭浏览器
        await browser.close()
        
        # 最终判断
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
        if all_passed:
            print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.GREEN}║  ✅ TTS 播放测试通过 - 所有关键日志都存在                      ║{Colors.END}")
            print(f"{Colors.GREEN}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            return 0
        else:
            print(f"{Colors.YELLOW}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.YELLOW}║  ⚠️  TTS 播放测试失败 - 部分关键日志缺失                       ║{Colors.END}")
            print(f"{Colors.YELLOW}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            
            # 诊断建议
            print(f"\n{Colors.BLUE}🔍 诊断建议:{Colors.END}")
            if not checks['收到 TTS 音频数据']:
                print(f"  1. 网关可能没有发送音频数据 → 检查网关 TTS 回调")
            if not checks['开始播放 TTS']:
                print(f"  2. 前端可能跳过了播放 → 检查_isPlayingTTS 标志")
            if not checks['_playAudioBase64']:
                print(f"  3. gateway.playAudio 可能未调用 → 检查 SDK 集成")
            if not checks['创建 AudioContext']:
                print(f"  4. AudioContext 可能创建失败 → 检查浏览器兼容性")
            if not checks['开始播放']:
                print(f"  5. 播放逻辑可能有问题 → 检查_playNextInQueue")
            
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_tts_playback())
    sys.exit(exit_code)
