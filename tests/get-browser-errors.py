#!/usr/bin/env python3
"""
获取浏览器控制台错误
"""

import asyncio
from playwright.async_api import async_playwright

async def get_errors():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                errors.append(f"[ERROR] {msg.text}")
            elif msg.type == 'warning':
                errors.append(f"[WARN] {msg.text}")
        
        page.on('console', handle_console)
        page.on('pageerror', lambda e: errors.append(f"[EXCEPTION] {str(e)}"))
        
        # 打开页面
        print("打开页面...")
        await page.goto("http://localhost:8080/test-pages/pro-call.html", wait_until='networkidle')
        
        # 等待 10 秒
        print("等待 10 秒收集错误...")
        await asyncio.sleep(10)
        
        # 输出错误
        print("\n" + "="*80)
        print("收集到的错误:")
        print("="*80)
        
        if errors:
            for err in errors:
                print(err)
        else:
            print("✅ 没有发现错误")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_errors())
