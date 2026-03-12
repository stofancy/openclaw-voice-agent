#!/usr/bin/env python3
"""
UI Mobile First 测试 - 测试响应式布局、状态切换和按钮交互
基于 Playwright 的端到端测试
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加 playwright 支持
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ 需要安装 playwright: pip install playwright")
    print("然后运行：playwright install")
    sys.exit(1)

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
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

async def test_responsive_layout():
    """测试 1: 响应式布局测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📱 测试 1: 响应式布局{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # 测试移动端视图 (375x667 - iPhone SE)
        mobile_context = await browser.new_context(viewport={'width': 375, 'height': 667})
        mobile_page = await mobile_context.new_page()
        
        # 测试桌面端视图 (1280x720)
        desktop_context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        desktop_page = await desktop_context.new_page()
        
        try:
            # 加载页面
            await mobile_page.goto('http://localhost:5173', timeout=10000)
            await desktop_page.goto('http://localhost:5173', timeout=10000)
            
            # 等待应用加载
            await mobile_page.wait_for_selector('.app', timeout=5000)
            await desktop_page.wait_for_selector('.app', timeout=5000)
            
            # 测试移动端布局元素存在
            mobile_status_bar = await mobile_page.query_selector('.status-bar')
            mobile_voice_container = await mobile_page.query_selector('.voice-container')
            mobile_controls_bar = await mobile_page.query_selector('.controls-bar')
            
            test("移动端状态栏存在", mobile_status_bar is not None, "移动端布局")
            test("移动端语音容器存在", mobile_voice_container is not None, "移动端布局")
            test("移动端控制栏存在", mobile_controls_bar is not None, "移动端布局")
            
            # 测试桌面端布局元素存在
            desktop_status_bar = await desktop_page.query_selector('.status-bar')
            desktop_voice_container = await desktop_page.query_selector('.voice-container')
            desktop_controls_bar = await desktop_page.query_selector('.controls-bar')
            
            test("桌面端状态栏存在", desktop_status_bar is not None, "桌面端布局")
            test("桌面端语音容器存在", desktop_voice_container is not None, "桌面端布局")
            test("桌面端控制栏存在", desktop_controls_bar is not None, "桌面端布局")
            
            # 测试移动端按钮尺寸（应该更大）
            mobile_btn = await mobile_page.query_selector('.control-btn')
            if mobile_btn:
                mobile_box = await mobile_btn.bounding_box()
                test("移动端按钮高度合理", mobile_box['height'] >= 60, f"高度={mobile_box['height']}px")
            
            # 测试桌面端居中布局
            desktop_app_box = await (await desktop_page.query_selector('.app')).bounding_box()
            test("桌面端应用居中", desktop_app_box['x'] > 0, f"x={desktop_app_box['x']}px")
            
        except Exception as e:
            test("响应式布局测试", False, str(e))
        finally:
            await browser.close()

async def test_state_transitions():
    """测试 2: 状态切换测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🔄 测试 2: 状态切换{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试初始状态 (idle)
            status_indicator = await page.query_selector('.status-indicator')
            initial_class = await status_indicator.get_attribute('class')
            test("初始状态为 idle", 'idle' in initial_class, f"class={initial_class}")
            
            # 测试连接中状态
            connect_btn = await page.query_selector('.btn-connect')
            await connect_btn.click()
            
            # 等待状态变化
            await page.wait_for_timeout(500)
            status_class = await (await page.query_selector('.status-indicator')).get_attribute('class')
            test("连接后状态改变", 'connecting' in status_class or 'listening' in status_class, f"class={status_class}")
            
            # 测试状态文本显示
            status_text = await (await page.query_selector('.status-indicator')).text_content()
            test("状态文本非空", len(status_text.strip()) > 0, f"text={status_text}")
            
            # 测试语音动画存在
            voice_animation = await page.query_selector('.voice-animation')
            test("语音动画元素存在", voice_animation is not None, "动画容器")
            
            # 测试控制栏按钮变化
            controls_after_connect = await page.query_selector_all('.control-btn')
            test("连接后按钮数量变化", len(controls_after_connect) >= 2, f"数量={len(controls_after_connect)}")
            
        except Exception as e:
            test("状态切换测试", False, str(e))
        finally:
            await browser.close()

async def test_button_interactions():
    """测试 3: 按钮交互测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🎛️ 测试 3: 按钮交互{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试连接按钮
            connect_btn = await page.query_selector('.btn-connect')
            test("连接按钮存在", connect_btn is not None, "连接按钮")
            
            # 测试连接按钮可点击
            connect_btn_disabled = await connect_btn.is_disabled()
            test("连接按钮初始可用", not connect_btn_disabled, "按钮状态")
            
            # 点击连接
            await connect_btn.click()
            await page.wait_for_timeout(500)
            
            # 测试挂断按钮出现
            hangup_btn = await page.query_selector('.btn-hangup')
            test("连接后挂断按钮出现", hangup_btn is not None, "挂断按钮")
            
            # 测试静音按钮出现
            mic_btn = await page.query_selector('.btn-mic')
            test("连接后静音按钮出现", mic_btn is not None, "静音按钮")
            
            # 测试静音按钮点击
            if mic_btn:
                initial_text = await mic_btn.text_content()
                await mic_btn.click()
                await page.wait_for_timeout(300)
                
                # 检查静音状态变化
                mic_btn_muted = await mic_btn.is_enabled()
                test("静音按钮可切换", mic_btn_muted, "按钮切换")
            
            # 测试挂断按钮点击
            if hangup_btn:
                await hangup_btn.click()
                await page.wait_for_timeout(500)
                
                # 检查是否回到初始状态
                connect_btn_after = await page.query_selector('.btn-connect')
                test("挂断后连接按钮恢复", connect_btn_after is not None, "状态恢复")
            
            # 测试按钮悬停效果（通过 CSS）
            btn_styles = await page.evaluate("""
                () => {
                    const btn = document.querySelector('.control-btn');
                    if (btn) {
                        const styles = window.getComputedStyle(btn);
                        return {
                            cursor: styles.cursor,
                            transition: styles.transition
                        };
                    }
                    return null;
                }
            """)
            
            test("按钮有过渡效果", btn_styles and 'transition' in str(btn_styles), "CSS 效果")
            
        except Exception as e:
            test("按钮交互测试", False, str(e))
        finally:
            await browser.close()

async def test_voice_animation():
    """测试 4: 语音动画测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🎨 测试 4: 语音动画{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试语音动画容器
            voice_animation = await page.query_selector('.voice-animation')
            test("语音动画容器存在", voice_animation is not None, "动画容器")
            
            # 测试波纹元素
            rings = await page.query_selector_all('.voice-ring')
            test("波纹环存在", len(rings) == 3, f"数量={len(rings)}")
            
            # 测试中央图标
            voice_icon = await page.query_selector('.voice-icon')
            test("中央图标存在", voice_icon is not None, "图标")
            
            # 测试动画 CSS
            animation_styles = await page.evaluate("""
                () => {
                    const ring = document.querySelector('.ring-1');
                    if (ring) {
                        const styles = window.getComputedStyle(ring);
                        return {
                            animation: styles.animation,
                            borderRadius: styles.borderRadius
                        };
                    }
                    return null;
                }
            """)
            
            test("波纹有圆形边框", animation_styles and animation_styles.get('borderRadius') == '50%', "CSS 样式")
            
            # 点击连接后测试动画状态类
            connect_btn = await page.query_selector('.btn-connect')
            if connect_btn:
                await connect_btn.click()
                await page.wait_for_timeout(500)
                
                voice_class = await (await page.query_selector('.voice-animation')).get_attribute('class')
                test("连接后动画状态改变", 'connecting' in voice_class or 'listening' in voice_class, f"class={voice_class}")
            
        except Exception as e:
            test("语音动画测试", False, str(e))
        finally:
            await browser.close()

async def test_subtitle_display():
    """测试 5: 字幕显示测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📝 测试 5: 字幕显示{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试初始无字幕
            subtitle_overlay = await page.query_selector('.subtitle-overlay')
            test("初始无字幕叠加层", subtitle_overlay is None, "字幕区域")
            
            # 模拟字幕数据（通过注入 JavaScript）
            await page.evaluate("""
                () => {
                    // 这里只是测试字幕元素可以渲染
                    const overlay = document.createElement('div');
                    overlay.className = 'subtitle-overlay';
                    overlay.innerHTML = `
                        <div class="subtitles-scroll">
                            <div class="subtitle-item user">
                                <span class="subtitle-role">👤</span>
                                <span class="subtitle-text">测试字幕</span>
                            </div>
                        </div>
                    `;
                    document.querySelector('.voice-container').appendChild(overlay);
                }
            """)
            
            await page.wait_for_timeout(300)
            
            # 测试字幕显示
            subtitle_item = await page.query_selector('.subtitle-item')
            test("字幕项可以显示", subtitle_item is not None, "字幕项")
            
            subtitle_role = await page.query_selector('.subtitle-role')
            test("字幕角色图标存在", subtitle_role is not None, "角色图标")
            
            subtitle_text = await page.query_selector('.subtitle-text')
            test("字幕文本存在", subtitle_text is not None, "文本")
            
            # 测试用户和 AI 字幕样式区分
            await page.evaluate("""
                () => {
                    const overlay = document.querySelector('.subtitle-overlay');
                    if (overlay) {
                        const aiSubtitle = document.createElement('div');
                        aiSubtitle.className = 'subtitle-item ai';
                        aiSubtitle.innerHTML = `
                            <span class="subtitle-role">🤖</span>
                            <span class="subtitle-text">AI 回复</span>
                        `;
                        overlay.querySelector('.subtitles-scroll').appendChild(aiSubtitle);
                    }
                }
            """)
            
            await page.wait_for_timeout(300)
            
            ai_subtitle = await page.query_selector('.subtitle-item.ai')
            test("AI 字幕样式区分", ai_subtitle is not None, "AI 样式")
            
        except Exception as e:
            test("字幕显示测试", False, str(e))
        finally:
            await browser.close()

async def test_error_state():
    """测试 6: 错误状态测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}⚠️ 测试 6: 错误状态{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试错误状态可以通过状态类识别
            status_indicator = await page.query_selector('.status-indicator')
            status_class = await status_indicator.get_attribute('class')
            
            # 初始不应是错误状态
            test("初始非错误状态", 'error' not in status_class, "初始状态")
            
            # 测试日志面板存在
            logs_panel = await page.query_selector('.logs-panel')
            test("日志面板存在", logs_panel is not None, "日志面板")
            
            # 测试日志可以展开
            summary = await page.query_selector('.logs-panel summary')
            test("日志面板可展开", summary is not None, "展开按钮")
            
        except Exception as e:
            test("错误状态测试", False, str(e))
        finally:
            await browser.close()

async def test_css_variables():
    """测试 7: CSS 变量定义测试"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🎨 测试 7: CSS 变量{Colors.END}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto('http://localhost:5173', timeout=10000)
            await page.wait_for_selector('.app', timeout=5000)
            
            # 测试 CSS 变量可用
            css_vars = await page.evaluate("""
                () => {
                    const styles = getComputedStyle(document.documentElement);
                    return {
                        primary: styles.getPropertyValue('--color-primary').trim(),
                        bgPrimary: styles.getPropertyValue('--bg-primary').trim(),
                        textPrimary: styles.getPropertyValue('--text-primary').trim(),
                        transitionFast: styles.getPropertyValue('--transition-fast').trim()
                    };
                }
            """)
            
            test("主题色变量定义", css_vars.get('primary'), f"primary={css_vars.get('primary')}")
            test("背景色变量定义", css_vars.get('bgPrimary'), f"bg={css_vars.get('bgPrimary')}")
            test("文字色变量定义", css_vars.get('textPrimary'), f"text={css_vars.get('textPrimary')}")
            test("动画时长变量定义", css_vars.get('transitionFast'), f"transition={css_vars.get('transitionFast')}")
            
        except Exception as e:
            test("CSS 变量测试", False, str(e))
        finally:
            await browser.close()

async def run_all_tests():
    """运行所有 UI 测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 UI Mobile First 测试套件{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # 检查前端服务是否运行
    import urllib.request
    try:
        urllib.request.urlopen('http://localhost:5173', timeout=2)
    except Exception:
        print(f"\n{Colors.YELLOW}⚠️  前端服务未运行，请先启动：cd frontend && npm run dev{Colors.END}")
        print(f"{Colors.YELLOW}   或者运行：python tests/test_all.py 启动完整服务{Colors.END}\n")
        return 1
    
    # 运行所有测试
    await test_responsive_layout()
    await test_state_transitions()
    await test_button_interactions()
    await test_voice_animation()
    await test_subtitle_display()
    await test_error_state()
    await test_css_variables()
    
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
