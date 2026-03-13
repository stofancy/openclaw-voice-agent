#!/usr/bin/env python3
import pytest
"""
测试前端 Console 日志是否发送到后端
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_console_logs():
    """测试 Console 日志"""
    print("="*80)
    print("🧪 测试前端 Console 日志发送到后端")
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
        
        # 捕获前端 Console 日志
        frontend_logs = []
        
        def handle_console(msg):
            text = msg.text
            frontend_logs.append(text)
            print(f"[前端] {text}")
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:5173/")
        
        # 等待网关日志
        print("\n[2] 等待 5 秒，查看后端是否收到日志...")
        await asyncio.sleep(5)
        
        # 检查后端日志
        print("\n[3] 检查后端日志...")
        log_file = None
        import subprocess
        result = subprocess.run(
            ['bash', '-c', 'ls -t ~/workspaces/audio-proxy/logs/agent_gateway*.log | head -1'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            log_file = result.stdout.strip()
            print(f"   日志文件：{log_file}")
        
        if log_file:
            # 读取最后 100 行
            result = subprocess.run(
                ['bash', '-c', f'tail -100 "{log_file}" | grep "🌐 BROWSER"'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0 and result.stdout:
                print("\n✅ 后端收到前端日志:")
                for line in result.stdout.strip().split('\n')[-10:]:
                    print(f"  {line}")
            else:
                print("\n❌ 后端没有收到前端日志")
                print("\n前端 Console 日志:")
                for log in frontend_logs[-20:]:
                    print(f"  {log}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_console_logs())