#!/usr/bin/env python3
"""
TTS 播放自动化测试 - 使用 Playwright 自动测试并验证声音不重叠
"""

import sys
import os
import asyncio
import pytest
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

@pytest.mark.asyncio
async def test_tts_no_overlap():
    """测试 TTS 播放不重叠"""
    global console_logs, tts_audio_count, play_count
    console_logs = []
    tts_audio_count = 0
    play_count = 0
    
    print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BLUE}🧪 TTS 播放不重叠自动化测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*80}{Colors.END}")
    
    async with async_playwright() as p:
        # 启动浏览器（无头模式，适合CI环境）
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--autoplay-policy=no-user-gesture-required'
            ]
        )
        
        # 创建新上下文
        context = await browser.new_context()
        page = await context.new_page()
        
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
            elif '⚠️ TTS 正在播放，跳过' in text:
                print(f"{Colors.YELLOW}[防重复] {text}{Colors.END}")
            elif '⚠️ 正在播放，拒绝新音频' in text:
                print(f"{Colors.YELLOW}[SDK 防重复] {text}{Colors.END}")
            elif '❌' in text or 'Error' in text:
                print(f"{Colors.RED}[错误] {text}{Colors.END}")
        
        page.on('console', handle_console)
        
        # 导航到页面
        print(f"\n{Colors.BLUE}[步骤 1] 打开页面...{Colors.END}")
        await page.goto("http://localhost:5173/", wait_until='networkidle')
        await page.wait_for_selector('#btnCall')
        print(f"{Colors.GREEN}✅ 页面加载成功{Colors.END}")
        
        # 点击拨号
        print(f"\n{Colors.BLUE}[步骤 2] 点击拨号...{Colors.END}")
        await page.click('#btnCall')
        await asyncio.sleep(2)
        
        # 模拟发送 STT 结果（触发 TTS）
        print(f"\n{Colors.BLUE}[步骤 3] 模拟发送 STT 结果...{Colors.END}")
        await page.evaluate("""
            if (window.gateway && window.gateway.sendSTTResult) {
                window.gateway.sendSTTResult('你好');
            }
        """)
        
        # 等待 TTS 播放完成（最多 15 秒）
        print(f"\n{Colors.BLUE}[步骤 4] 等待 TTS 播放完成 (15 秒)...{Colors.END}")
        await asyncio.sleep(15)
        
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
        
        if overlap_detected:
            print(f"{Colors.RED}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.RED}║  ❌ TTS 播放重叠检测成功 - 发现问题                              ║{Colors.END}")
            print(f"{Colors.RED}╚════════════════════════════════════════════════════════════════╝{Colors.END}")
            await browser.close()
            return 1
        elif play_count <= 1:
            print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════════════╗{Colors.END}")
            print(f"{Colors.GREEN}║  ✅ TTS 播放测试通过 - 没有重叠                                 ║{Colors.END}")
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