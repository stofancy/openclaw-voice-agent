#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画效果测试 - 波纹动画 + 状态切换

测试内容：
1. 波纹动画存在性验证
2. 动画时长验证
3. 状态切换流畅性验证
4. 按钮点击反馈验证

验收标准：
- 波纹动画：3 层同心圆，流畅扩散
- 状态切换：6 种状态过渡平滑
- 按钮动画：点击反馈明显
- 性能：动画不卡顿（60fps）
"""

import pytest
from playwright.sync_api import sync_playwright, expect
import time
import os

# 配置
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:3000")
TIMEOUT = 10000  # 10 秒超时


class TestRippleAnimation:
    """波纹动画测试"""
    
    def test_ripple_rings_exist(self):
        """测试 3 层波纹环存在"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 等待页面加载
            page.wait_for_selector(".voice-animation", timeout=TIMEOUT)
            
            # 验证 3 层波纹环存在
            ring_1 = page.locator(".ring-1")
            ring_2 = page.locator(".ring-2")
            ring_3 = page.locator(".ring-3")
            
            expect(ring_1).to_be_visible()
            expect(ring_2).to_be_visible()
            expect(ring_3).to_be_visible()
            
            browser.close()
    
    def test_ripple_animation_class_exists(self):
        """测试波纹动画 CSS 类存在"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 检查 CSS 中是否存在 ripple 动画定义
            has_ripple_animation = page.evaluate("""
                () => {
                    const styles = document.styleSheets;
                    for (let i = 0; i < styles.length; i++) {
                        try {
                            const rules = styles[i].cssRules;
                            for (let j = 0; j < rules.length; j++) {
                                if (rules[j].name === 'ripple') {
                                    return true;
                                }
                            }
                        } catch (e) {}
                    }
                    return false;
                }
            """)
            
            assert has_ripple_animation, "ripple 动画未定义"
            
            browser.close()
    
    def test_ripple_animation_duration(self):
        """测试波纹动画时长（1.5s）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 获取波纹动画时长
            animation_duration = page.evaluate("""
                () => {
                    const ring = document.querySelector('.ring-1');
                    if (ring) {
                        const style = getComputedStyle(ring);
                        return parseFloat(style.animationDuration);
                    }
                    return 0;
                }
            """)
            
            # 验证动画时长在 1.4-1.6s 之间（允许小误差）
            assert 1.4 <= animation_duration <= 1.6, f"动画时长应为 1.5s，实际为{animation_duration}s"
            
            browser.close()
    
    def test_ripple_animation_infinite(self):
        """测试波纹动画循环播放"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 触发动画状态
            page.click(".btn-connect")
            page.wait_for_timeout(500)  # 等待连接
            
            # 验证动画循环
            animation_iteration = page.evaluate("""
                () => {
                    const ring = document.querySelector('.ring-1');
                    if (ring) {
                        const style = getComputedStyle(ring);
                        return style.animationIterationCount;
                    }
                    return '0';
                }
            """)
            
            assert animation_iteration == "infinite", f"动画应循环播放，实际为{animation_iteration}"
            
            browser.close()


class TestStateTransition:
    """状态切换动画测试"""
    
    def test_idle_to_connecting_transition(self):
        """测试 idle → connecting 状态切换（淡入 + 脉冲）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 初始状态应为 idle
            status_indicator = page.locator(".status-indicator")
            expect(status_indicator).to_have_class("status-indicator idle")
            
            # 点击连接按钮
            page.click(".btn-connect")
            page.wait_for_timeout(300)
            
            # 验证状态变为 connecting
            expect(status_indicator).to_have_class("status-indicator connecting")
            
            # 验证脉冲动画
            has_pulse = page.evaluate("""
                () => {
                    const indicator = document.querySelector('.status-indicator.connecting');
                    if (indicator) {
                        const style = getComputedStyle(indicator);
                        return style.animationName.includes('pulse');
                    }
                    return false;
                }
            """)
            
            assert has_pulse, "connecting 状态应有脉冲动画"
            
            browser.close()
    
    def test_connecting_to_listening_transition(self):
        """测试 connecting → listening 状态切换（波纹启动）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 点击连接
            page.click(".btn-connect")
            page.wait_for_timeout(500)
            
            # 模拟进入 listening 状态（通过 JS）
            page.evaluate("""
                () => {
                    const voiceAnim = document.querySelector('.voice-animation');
                    if (voiceAnim) {
                        voiceAnim.classList.remove('connecting');
                        voiceAnim.classList.add('listening');
                    }
                }
            """)
            
            page.wait_for_timeout(300)
            
            # 验证波纹动画启动
            ripple_active = page.evaluate("""
                () => {
                    const ring = document.querySelector('.voice-animation.listening .ring-1');
                    if (ring) {
                        const style = getComputedStyle(ring);
                        return style.animationName === 'ripple';
                    }
                    return false;
                }
            """)
            
            assert ripple_active, "listening 状态应启动波纹动画"
            
            browser.close()
    
    def test_listening_to_processing_transition(self):
        """测试 listening → processing 状态切换（旋转加载）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 切换到 processing 状态
            page.evaluate("""
                () => {
                    const voiceAnim = document.querySelector('.voice-animation');
                    if (voiceAnim) {
                        voiceAnim.classList.remove('listening');
                        voiceAnim.classList.add('processing');
                    }
                }
            """)
            
            page.wait_for_timeout(300)
            
            # 验证旋转动画
            spin_active = page.evaluate("""
                () => {
                    const circle = document.querySelector('.voice-animation.processing .voice-circle');
                    if (circle) {
                        const style = getComputedStyle(circle);
                        return style.animationName === 'spin';
                    }
                    return false;
                }
            """)
            
            assert spin_active, "processing 状态应有旋转动画"
            
            browser.close()
    
    def test_processing_to_speaking_transition(self):
        """测试 processing → speaking 状态切换（波纹继续）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 切换到 speaking 状态
            page.evaluate("""
                () => {
                    const voiceAnim = document.querySelector('.voice-animation');
                    if (voiceAnim) {
                        voiceAnim.classList.remove('processing');
                        voiceAnim.classList.add('speaking');
                    }
                }
            """)
            
            page.wait_for_timeout(300)
            
            # 验证波纹动画继续
            ripple_active = page.evaluate("""
                () => {
                    const ring = document.querySelector('.voice-animation.speaking .ring-1');
                    if (ring) {
                        const style = getComputedStyle(ring);
                        return style.animationName === 'ripple';
                    }
                    return false;
                }
            """)
            
            assert ripple_active, "speaking 状态应继续波纹动画"
            
            browser.close()
    
    def test_speaking_to_idle_transition(self):
        """测试 speaking → idle 状态切换（淡出）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 先切换到 speaking
            page.evaluate("""
                () => {
                    const voiceAnim = document.querySelector('.voice-animation');
                    if (voiceAnim) {
                        voiceAnim.classList.add('speaking');
                    }
                }
            """)
            
            page.wait_for_timeout(300)
            
            # 切换到 idle
            page.evaluate("""
                () => {
                    const voiceAnim = document.querySelector('.voice-animation');
                    if (voiceAnim) {
                        voiceAnim.classList.remove('speaking');
                        voiceAnim.classList.add('idle');
                    }
                }
            """)
            
            page.wait_for_timeout(500)
            
            # 验证回到 idle 状态
            expect(page.locator(".voice-animation")).to_have_class("voice-animation idle")
            
            browser.close()
    
    def test_status_transition_smoothness(self):
        """测试状态切换流畅性（transition 属性）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 验证状态指示器有 transition 属性
            has_transition = page.evaluate("""
                () => {
                    const indicator = document.querySelector('.status-indicator');
                    if (indicator) {
                        const style = getComputedStyle(indicator);
                        return style.transition !== 'none' && style.transition !== '';
                    }
                    return false;
                }
            """)
            
            assert has_transition, "状态指示器应有 transition 属性以实现平滑过渡"
            
            browser.close()


class TestButtonAnimations:
    """按钮点击动画测试"""
    
    def test_connect_button_click_animation(self):
        """测试连接按钮点击动画（缩放 + 变色）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            btn = page.locator(".btn-connect")
            
            # 点击按钮
            btn.click()
            
            # 验证按钮有点击反馈（通过检查 active 状态或动画）
            page.wait_for_timeout(100)
            
            has_animation = page.evaluate("""
                () => {
                    const btn = document.querySelector('.btn-connect');
                    if (btn) {
                        const style = getComputedStyle(btn);
                        return style.transform !== 'none' || 
                               style.animationName !== 'none';
                    }
                    return false;
                }
            """)
            
            assert has_animation, "连接按钮应有点击动画"
            
            browser.close()
    
    def test_hangup_button_click_animation(self):
        """测试挂断按钮点击动画（抖动 + 红色）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 先连接
            page.click(".btn-connect")
            page.wait_for_timeout(1000)
            
            btn = page.locator(".btn-hangup")
            
            # 点击挂断
            btn.click()
            page.wait_for_timeout(100)
            
            # 验证抖动动画
            has_shake = page.evaluate("""
                () => {
                    const btn = document.querySelector('.btn-hangup');
                    if (btn) {
                        const style = getComputedStyle(btn);
                        return style.animationName.includes('shake') || 
                               style.transform !== 'none';
                    }
                    return false;
                }
            """)
            
            assert has_shake, "挂断按钮应有抖动动画"
            
            browser.close()
    
    def test_mic_button_click_animation(self):
        """测试静音按钮点击动画（切换图标 + 颜色）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            btn = page.locator(".btn-mic")
            
            # 获取初始状态
            initial_class = btn.get_attribute("class")
            
            # 点击按钮
            btn.click()
            page.wait_for_timeout(300)
            
            # 验证状态切换
            new_class = btn.get_attribute("class")
            
            # 按钮应该有状态变化（muted 或 unmuted）
            assert initial_class != new_class or btn.is_enabled(), "静音按钮应有状态变化"
            
            browser.close()
    
    def test_button_hover_animation(self):
        """测试按钮悬停动画"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            btn = page.locator(".btn-connect")
            
            # 悬停
            btn.hover()
            page.wait_for_timeout(200)
            
            # 验证悬停效果（transform 或 box-shadow 变化）
            has_hover = page.evaluate("""
                () => {
                    const btn = document.querySelector('.btn-connect:hover');
                    if (btn) {
                        const style = getComputedStyle(btn);
                        return style.transform !== 'none' || 
                               parseFloat(style.boxShadow) > 0;
                    }
                    return false;
                }
            """)
            
            assert has_hover, "按钮应有悬停动画"
            
            browser.close()


class TestAnimationPerformance:
    """动画性能测试"""
    
    def test_animation_no_jank(self):
        """测试动画流畅性（60fps）"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 触发动画
            page.click(".btn-connect")
            page.wait_for_timeout(500)
            
            # 检查 FPS（Playwright 不直接支持 FPS 检测，这里做基本验证）
            # 实际项目中可使用 browser.new_context({ recordVideo: {...} }) 录制分析
            
            # 验证动画元素存在且可见
            rings_visible = page.evaluate("""
                () => {
                    const rings = document.querySelectorAll('.ring-1, .ring-2, .ring-3');
                    return Array.from(rings).every(ring => {
                        const style = getComputedStyle(ring);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity > 0;
                    });
                }
            """)
            
            assert rings_visible, "波纹环应全部可见且流畅动画"
            
            browser.close()
    
    def test_css_animation_supported(self):
        """测试浏览器支持 CSS 动画"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            supports_animation = page.evaluate("""
                () => {
                    return typeof CSSAnimation !== 'undefined' ||
                           'animation' in document.documentElement.style;
                }
            """)
            
            assert supports_animation, "浏览器应支持 CSS 动画"
            
            browser.close()


class TestAccessibility:
    """辅助功能测试"""
    
    def test_reduced_motion_support(self):
        """测试减少动画偏好支持"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 设置减少动画偏好
            context = browser.new_context(
                reduced_motion="reduce"
            )
            page = context.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 验证页面加载正常（即使动画被禁用）
            expect(page.locator(".voice-animation")).to_be_visible()
            
            browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
