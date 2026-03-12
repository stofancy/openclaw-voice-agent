#!/usr/bin/env python3
"""
前端功能自动化测试
使用 Selenium/Puppeteer 测试浏览器端功能
"""

import sys
import os
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

# 测试结果
test_results = {'passed': 0, 'failed': 0, 'total': 0}

def test(name, condition, details=""):
    test_results['total'] += 1
    if condition:
        test_results['passed'] += 1
        print(f"{Colors.GREEN}✅ [PASS]{Colors.END} {name}")
        return True
    else:
        test_results['failed'] += 1
        print(f"{Colors.RED}❌ [FAIL]{Colors.END} {name} - {details}")
        return False

def setup_driver():
    """设置 Chrome 浏览器（无头模式）"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

async def test_page_load():
    """测试 1: 页面加载"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 1: 页面加载{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnCall"))
        )
        
        test("页面加载成功", "AI Travel Agent" in driver.title, f"标题：{driver.title}")
        
        # 检查拨号按钮
        btn_call = driver.find_element(By.ID, "btnCall")
        test("拨号按钮存在", btn_call.is_displayed(), "按钮可见")
        
        # 检查挂断按钮
        btn_hangup = driver.find_element(By.ID, "btnHangup")
        test("挂断按钮存在", btn_hangup.is_displayed(), "按钮可见")
        
        # 检查静音按钮
        btn_mic = driver.find_element(By.ID, "btnMic")
        test("静音按钮存在", btn_mic.is_displayed(), "按钮可见")
        
        return True
    except Exception as e:
        test("页面加载", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def test_mic_permission():
    """测试 2: 麦克风权限"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 2: 麦克风权限{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnCall"))
        )
        
        # 点击拨号按钮
        btn_call = driver.find_element(By.ID, "btnCall")
        btn_call.click()
        
        # 等待 3 秒（麦克风权限请求）
        time.sleep(3)
        
        # 检查控制台日志
        logs = driver.get_log('browser')
        has_mic_log = any('🎤' in log['message'] for log in logs)
        test("麦克风权限请求", has_mic_log, "日志中包含麦克风请求")
        
        return True
    except Exception as e:
        test("麦克风权限", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def test_mute_function():
    """测试 3: 静音功能"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 3: 静音功能{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnCall"))
        )
        
        # 点击拨号按钮
        btn_call = driver.find_element(By.ID, "btnCall")
        btn_call.click()
        
        # 等待连接
        time.sleep(3)
        
        # 点击静音按钮
        btn_mic = driver.find_element(By.ID, "btnMic")
        btn_mic.click()
        
        # 等待 1 秒
        time.sleep(1)
        
        # 检查静音状态
        is_muted = 'muted' in btn_mic.get_attribute('class')
        test("静音按钮状态", is_muted, "按钮有 muted 类")
        
        # 检查 isMuted 变量
        is_muted_js = driver.execute_script("return window.isMuted;")
        test("isMuted 变量", is_muted_js == True, f"isMuted={is_muted_js}")
        
        return True
    except Exception as e:
        test("静音功能", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def test_volume_animation():
    """测试 4: 音量动画"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 4: 音量动画{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "volumeBar"))
        )
        
        # 检查音量条存在
        volume_bar = driver.find_element(By.ID, "volumeBar")
        test("音量条存在", volume_bar.is_displayed(), "音量条可见")
        
        # 检查初始宽度
        initial_width = volume_bar.get_attribute('style')
        test("音量条初始状态", 'width' in initial_width, f"样式：{initial_width}")
        
        return True
    except Exception as e:
        test("音量动画", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def test_tts_playback():
    """测试 5: TTS 播放"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 5: TTS 播放{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "btnCall"))
        )
        
        # 点击拨号
        btn_call = driver.find_element(By.ID, "btnCall")
        btn_call.click()
        
        # 等待连接
        time.sleep(3)
        
        # 检查 _isPlayingTTS 标志
        is_playing = driver.execute_script("return window._isPlayingTTS || false;")
        test("TTS 播放标志初始化", is_playing == False, f"_isPlayingTTS={is_playing}")
        
        # 检查 _replyShown 标志
        reply_shown = driver.execute_script("return window._replyShown || false;")
        test("回复显示标志初始化", reply_shown == False, f"_replyShown={reply_shown}")
        
        return True
    except Exception as e:
        test("TTS 播放", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def test_subtitle_display():
    """测试 6: 字幕显示"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 6: 字幕显示{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    driver = None
    try:
        driver = setup_driver()
        driver.get("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "call-area"))
        )
        
        # 检查字幕容器存在
        call_area = driver.find_element(By.CLASS_NAME, "call-area")
        test("通话区域存在", call_area.is_displayed(), "区域可见")
        
        # 检查 Agent 区域
        agent_section = driver.find_element(By.CLASS_NAME, "agent-section")
        test("Agent 区域存在", agent_section.is_displayed(), "区域可见")
        
        # 检查用户区域
        user_section = driver.find_element(By.CLASS_NAME, "user-section")
        test("用户区域存在", user_section.is_displayed(), "区域可见")
        
        return True
    except Exception as e:
        test("字幕显示", False, str(e))
        return False
    finally:
        if driver:
            driver.quit()

async def run_all_tests():
    """运行所有前端测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 前端功能自动化测试{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    # 测试 1: 页面加载
    await test_page_load()
    
    # 测试 2: 麦克风权限
    await test_mic_permission()
    
    # 测试 3: 静音功能
    await test_mute_function()
    
    # 测试 4: 音量动画
    await test_volume_animation()
    
    # 测试 5: TTS 播放
    await test_tts_playback()
    
    # 测试 6: 字幕显示
    await test_subtitle_display()
    
    # 汇总报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 测试报告{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"总测试数：{total}")
    print(f"通过：{Colors.GREEN}{passed}{Colors.END}")
    print(f"失败：{Colors.RED}{failed}{Colors.END}")
    print(f"通过率：{pass_rate:.1f}%")
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  有 {failed} 个测试失败，请修复{Colors.END}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
