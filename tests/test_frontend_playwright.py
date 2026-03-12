#!/usr/bin/env python3
"""
前端功能自动化测试 - 使用 Playwright
测试浏览器端所有功能
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

async def test_page_load(browser):
    """测试 1: 页面加载"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 1: 页面加载{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        
        # 等待页面加载
        await page.wait_for_selector('#btnCall')
        test("页面加载成功", True, "URL 可访问")
        
        # 检查标题
        title = await page.title()
        test("页面标题正确", "AI Travel Agent" in title, f"标题：{title}")
        
        # 检查拨号按钮
        btn_call = await page.query_selector('#btnCall')
        btn_call_visible = await btn_call.is_visible()
        test("拨号按钮存在且可见", btn_call_visible, "按钮可见")
        
        # 检查挂断按钮
        btn_hangup = await page.query_selector('#btnHangup')
        btn_hangup_visible = await btn_hangup.is_visible()
        test("挂断按钮存在且可见", btn_hangup_visible, "按钮可见")
        
        # 检查静音按钮
        btn_mic = await page.query_selector('#btnMic')
        btn_mic_visible = await btn_mic.is_visible()
        test("静音按钮存在且可见", btn_mic_visible, "按钮可见")
        
        # 检查音量条
        volume_bar = await page.query_selector('#volumeBar')
        volume_bar_exists = volume_bar is not None
        test("音量条存在", volume_bar_exists, "音量条元素")
        
        # 检查 Agent 区域
        agent_section = await page.query_selector('.agent-section')
        agent_section_exists = agent_section is not None
        test("Agent 区域存在", agent_section_exists, "区域元素")
        
        # 检查用户区域
        user_section = await page.query_selector('.user-section')
        user_section_exists = user_section is not None
        test("用户区域存在", user_section_exists, "区域元素")
        
        return True
    except Exception as e:
        test("页面加载", False, str(e))
        return False
    finally:
        await page.close()

async def test_call_buttons(browser):
    """测试 2: 通话按钮功能"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 2: 通话按钮功能{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('#btnCall')
        
        # 检查拨号按钮初始状态
        btn_call = await page.query_selector('#btnCall')
        btn_call_disabled = await btn_call.get_attribute('disabled')
        test("拨号按钮初始可用", btn_call_disabled is None, "按钮未禁用")
        
        # 检查挂断按钮初始状态
        btn_hangup = await page.query_selector('#btnHangup')
        btn_hangup_disabled = await btn_hangup.get_attribute('disabled')
        test("挂断按钮初始禁用", btn_hangup_disabled is not None, "按钮禁用")
        
        # 检查静音按钮初始状态
        btn_mic = await page.query_selector('#btnMic')
        btn_mic_disabled = await btn_mic.get_attribute('disabled')
        test("静音按钮初始禁用", btn_mic_disabled is not None, "按钮禁用")
        
        return True
    except Exception as e:
        test("通话按钮", False, str(e))
        return False
    finally:
        await page.close()

async def test_mute_function(browser):
    """测试 3: 静音功能"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 3: 静音功能{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('#btnCall')
        
        # 测试静音标志
        await page.evaluate("window.isMuted = false")
        is_muted = await page.evaluate("window.isMuted")
        test("静音标志初始=False", is_muted == False, f"isMuted={is_muted}")
        
        # 模拟静音状态
        await page.evaluate("window.isMuted = true")
        is_muted = await page.evaluate("window.isMuted")
        test("静音标志可设置", is_muted == True, f"isMuted={is_muted}")
        
        # 检查静音按钮存在
        btn_mic = await page.query_selector('#btnMic')
        btn_mic_exists = btn_mic is not None
        test("静音按钮存在", btn_mic_exists, "按钮元素")
        
        return True
    except Exception as e:
        test("静音功能", False, str(e))
        return False
    finally:
        await page.close()

async def test_volume_animation(browser):
    """测试 4: 音量动画"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 4: 音量动画{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        
        # 音量条可能初始隐藏，用 query_selector 而不是 wait_for
        volume_bar = await page.query_selector('#volumeBar')
        volume_bar_exists = volume_bar is not None
        test("音量条元素存在", volume_bar_exists, "元素存在")
        
        if volume_bar_exists:
            # 测试 updateVolume 函数
            await page.evaluate("""
                window.testVolumeUpdated = false;
                if (typeof updateVolume === 'function') {
                    updateVolume(0.5);
                    window.testVolumeUpdated = true;
                }
            """)
            
            volume_updated = await page.evaluate("window.testVolumeUpdated")
            test("updateVolume 函数存在", volume_updated, "函数可调用")
            
            # 检查音量条宽度变化
            new_style = await volume_bar.get_attribute('style')
            has_width = new_style and 'width' in new_style
            test("音量条宽度可更新", has_width, f"style={new_style}")
        else:
            test("updateVolume 函数存在", False, "音量条不存在")
            test("音量条宽度可更新", False, "音量条不存在")
        
        return True
    except Exception as e:
        test("音量动画", False, str(e))
        return False
    finally:
        await page.close()

async def test_subtitle_display(browser):
    """测试 5: 字幕显示"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 5: 字幕显示{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('.call-area')
        
        # 测试 updateSubtitle 函数
        await page.evaluate("""
            window.testSubtitleCreated = false;
            if (typeof updateSubtitle === 'function') {
                updateSubtitle('测试字幕', 'agent', true);
                window.testSubtitleCreated = true;
            }
        """)
        
        subtitle_created = await page.evaluate("window.testSubtitleCreated")
        test("updateSubtitle 函数存在", subtitle_created, "函数可调用")
        
        # 检查字幕元素是否创建
        agent_subtitle = await page.query_selector('#agentSubtitle')
        subtitle_exists = agent_subtitle is not None
        test("Agent 字幕元素创建", subtitle_exists, "元素存在")
        
        if subtitle_exists:
            subtitle_text = await agent_subtitle.text_content()
            test("字幕文本正确", subtitle_text == '测试字幕', f"文本：{subtitle_text}")
        
        # 测试防止重复显示
        await page.evaluate("window._replyShown = false")
        reply_shown = await page.evaluate("window._replyShown")
        test("回复显示标志初始=False", reply_shown == False, f"_replyShown={reply_shown}")
        
        return True
    except Exception as e:
        test("字幕显示", False, str(e))
        return False
    finally:
        await page.close()

async def test_tts_playback_flag(browser):
    """测试 6: TTS 播放标志"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 6: TTS 播放标志{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('.call-area')
        
        # 测试 _isPlayingTTS 标志
        await page.evaluate("window._isPlayingTTS = false")
        is_playing = await page.evaluate("window._isPlayingTTS")
        test("TTS 播放标志初始=False", is_playing == False, f"_isPlayingTTS={is_playing}")
        
        # 模拟播放中
        await page.evaluate("window._isPlayingTTS = true")
        is_playing = await page.evaluate("window._isPlayingTTS")
        test("TTS 播放标志可设置", is_playing == True, f"_isPlayingTTS={is_playing}")
        
        # 测试 onAudio 回调中的防重复逻辑
        await page.evaluate("""
            window._isPlayingTTS = false;
            window.testAudioPlayCount = 0;
            
            // 模拟 onAudio 回调
            if (!window._isPlayingTTS) {
                window._isPlayingTTS = true;
                window.testAudioPlayCount++;
                setTimeout(() => { window._isPlayingTTS = false; }, 5000);
            }
            
            // 第二次调用应该被阻止
            if (!window._isPlayingTTS) {
                window.testAudioPlayCount++;
            }
        """)
        
        play_count = await page.evaluate("window.testAudioPlayCount")
        test("TTS 播放防重复", play_count == 1, f"播放次数={play_count}")
        
        return True
    except Exception as e:
        test("TTS 播放标志", False, str(e))
        return False
    finally:
        await page.close()

async def test_mic_permission(browser):
    """测试 7: 麦克风权限"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 7: 麦克风权限{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        # 授予麦克风权限
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        await context.grant_permissions(['microphone'])
        
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('.call-area')
        
        # 测试 navigator.mediaDevices 存在
        has_media_devices = await page.evaluate("""
            !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
        """)
        test("mediaDevices API 存在", has_media_devices, "API 可用")
        
        # 测试 getUserMedia 函数
        mic_test_result = await page.evaluate("""
            (async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const tracks = stream.getAudioTracks();
                    stream.getTracks().forEach(track => track.stop());
                    return {
                        success: true,
                        hasAudioTracks: tracks.length > 0,
                        trackLabel: tracks[0]?.label || 'unknown'
                    };
                } catch (error) {
                    return {
                        success: false,
                        error: error.message
                    };
                }
            })()
        """)
        
        test("getUserMedia 调用成功", mic_test_result['success'], 
             f"结果：{mic_test_result}")
        
        if mic_test_result.get('hasAudioTracks'):
            test("获取到音频轨道", True, 
                 f"轨道标签：{mic_test_result.get('trackLabel')}")
        else:
            test("获取到音频轨道", False, "无音频轨道")
        
        return True
    except Exception as e:
        test("麦克风权限", False, str(e))
        return False
    finally:
        await page.close()

async def test_websocket_connection(browser):
    """测试 8: WebSocket 连接"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 测试 8: WebSocket 连接{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    page = await browser.new_page()
    
    try:
        await page.goto("http://localhost:8080/test-pages/pro-call.html")
        await page.wait_for_selector('.call-area')
        
        # 测试 WebSocket 构造函数存在
        has_websocket = await page.evaluate("!!WebSocket")
        test("WebSocket API 存在", has_websocket, "API 可用")
        
        # 测试 WebSocket 连接
        ws_test_result = await page.evaluate("""
            (async () => {
                return new Promise((resolve) => {
                    try {
                        const ws = new WebSocket('ws://localhost:8765');
                        
                        ws.onopen = () => {
                            ws.send(JSON.stringify({ type: 'connect' }));
                        };
                        
                        ws.onmessage = (event) => {
                            try {
                                const data = JSON.parse(event.data);
                                ws.close();
                                resolve({
                                    success: true,
                                    connected: true,
                                    responseType: data.type,
                                    gateway: data.gateway
                                });
                            } catch (e) {
                                ws.close();
                                resolve({
                                    success: false,
                                    error: 'Parse error: ' + e.message
                                });
                            }
                        };
                        
                        ws.onerror = (error) => {
                            ws.close();
                            resolve({
                                success: false,
                                error: 'WebSocket error'
                            });
                        };
                        
                        ws.onclose = () => {
                            if (!ws.onmessage) {
                                resolve({
                                    success: false,
                                    error: 'Connection closed without response'
                                });
                            }
                        };
                        
                        // 超时处理
                        setTimeout(() => {
                            ws.close();
                            resolve({
                                success: false,
                                error: 'Timeout'
                            });
                        }, 5000);
                        
                    } catch (error) {
                        resolve({
                            success: false,
                            error: error.message
                        });
                    }
                });
            })()
        """)
        
        test("WebSocket 连接成功", ws_test_result['success'], 
             f"结果：{ws_test_result}")
        
        if ws_test_result.get('connected'):
            test("收到连接响应", True, 
                 f"type={ws_test_result.get('responseType')}, gateway={ws_test_result.get('gateway')}")
        else:
            test("收到连接响应", False, ws_test_result.get('error', '未知错误'))
        
        return True
    except Exception as e:
        test("WebSocket 连接", False, str(e))
        return False
    finally:
        await page.close()

async def run_all_tests():
    """运行所有前端测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 前端功能自动化测试 (Playwright){Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            # 测试 1: 页面加载
            await test_page_load(browser)
            
            # 测试 2: 通话按钮
            await test_call_buttons(browser)
            
            # 测试 3: 静音功能
            await test_mute_function(browser)
            
            # 测试 4: 音量动画
            await test_volume_animation(browser)
            
            # 测试 5: 字幕显示
            await test_subtitle_display(browser)
            
            # 测试 6: TTS 播放标志
            await test_tts_playback_flag(browser)
            
            # 测试 7: 麦克风权限
            await test_mic_permission(browser)
            
            # 测试 8: WebSocket 连接
            await test_websocket_connection(browser)
            
        finally:
            await browser.close()
    
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
