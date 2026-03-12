#!/usr/bin/env python3
"""
测试前端 Console 日志是否发送到后端
"""

import sys
import os
import asyncio
from playwright.async_api import async_playwright

async def test_console_logs():
    """测试 Console 日志"""
    print("="*80)
    print("🧪 测试前端 Console 日志发送到后端")
    print("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # 捕获前端 Console 日志
        frontend_logs = []
        
        def handle_console(msg):
            text = msg.text
            frontend_logs.append(text)
            print(f"[前端] {text}")
        
        page.on('console', handle_console)
        
        # 打开页面
        print("\n[1] 打开页面...")
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        
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
