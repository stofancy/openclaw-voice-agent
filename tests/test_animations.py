#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画效果测试 - 波纹动画 + 状态切换

测试内容：
1. 波纹动画存在性验证（CSS 文件静态分析）
2. 动画时长验证
3. 状态切换流畅性验证
4. 按钮点击反馈验证
5. 前端运行时验证（需要服务运行）

验收标准：
- 波纹动画：3 层同心圆，流畅扩散
- 状态切换：6 种状态过渡平滑
- 按钮动画：点击反馈明显
- 性能：动画不卡顿（60fps）
"""

import pytest
import os
import re
from pathlib import Path

# 配置
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:3000")
TIMEOUT = 10000  # 10 秒超时
CSS_FILE = Path(__file__).parent.parent / "frontend" / "src" / "App.css"


def read_css_content():
    """读取 CSS 文件内容"""
    with open(CSS_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def css_has_animation(css_content, animation_name):
    """检查 CSS 是否包含指定动画定义"""
    pattern = rf'@keyframes\s+{animation_name}\s*\{{'
    return bool(re.search(pattern, css_content))


def css_has_class(css_content, class_name):
    """检查 CSS 是否包含指定类定义"""
    pattern = rf'\.{class_name}\s*\{{'
    return bool(re.search(pattern, css_content))


def get_animation_duration(css_content, selector):
    """从 CSS 中提取动画时长"""
    # 匹配 animation 属性：animation: ripple 1.5s ease-out infinite;
    pattern = rf'{selector}[^{{]*\{{[^}}]*animation:[^;]*?(\d+\.?\d*)s'
    match = re.search(pattern, css_content)
    if match:
        return float(match.group(1))
    return None


class TestRippleAnimation:
    """波纹动画测试（静态 CSS 分析）"""
    
    def test_ripple_animation_definition_exists(self):
        """测试 ripple 动画定义存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'ripple'), "ripple 动画未定义"
    
    def test_ripple_rings_classes_exist(self):
        """测试 3 层波纹环 CSS 类存在"""
        css_content = read_css_content()
        
        assert css_has_class(css_content, 'ring-1'), "ring-1 类未定义"
        assert css_has_class(css_content, 'ring-2'), "ring-2 类未定义"
        assert css_has_class(css_content, 'ring-3'), "ring-3 类未定义"
    
    def test_ripple_animation_duration(self):
        """测试波纹动画时长（1.5s）"""
        css_content = read_css_content()
        
        # 查找 ring-1 的动画时长
        duration = get_animation_duration(css_content, '.ring-1')
        
        # 验证动画时长在 1.4-1.6s 之间（允许小误差）
        assert duration is not None, "未找到 ring-1 的动画时长定义"
        assert 1.4 <= duration <= 1.6, f"动画时长应为 1.5s，实际为{duration}s"
    
    def test_ripple_animation_infinite(self):
        """测试波纹动画循环播放"""
        css_content = read_css_content()
        
        # 检查是否包含 infinite
        pattern = r'animation:\s*ripple\s+[\d.]+s\s+ease-out\s+infinite'
        assert re.search(pattern, css_content), "波纹动画未设置循环播放（infinite）"
    
    def test_ripple_animation_opacity_gradient(self):
        """测试波纹动画透明度渐变（1.0 → 0）"""
        css_content = read_css_content()
        
        # 检查 ripple 动画关键帧中的透明度变化（使用 DOTALL 模式匹配多行）
        ripple_keyframes = re.search(r'@keyframes\s+ripple\s*\{(.+?)\n\}', css_content, re.DOTALL)
        assert ripple_keyframes, "未找到 ripple 动画关键帧"
        
        keyframe_content = ripple_keyframes.group(1)
        
        # 检查 0% 时 opacity: 1
        assert re.search(r'0%\s*\{.+?opacity:\s*1', keyframe_content, re.DOTALL), "ripple 动画 0% 时 opacity 应为 1"
        
        # 检查 100% 时 opacity: 0
        assert re.search(r'100%\s*\{.+?opacity:\s*0', keyframe_content, re.DOTALL), "ripple 动画 100% 时 opacity 应为 0"
    
    def test_ripple_animation_scale_transform(self):
        """测试波纹动画缩放变换（从 0.8 到 2）"""
        css_content = read_css_content()
        
        ripple_keyframes = re.search(r'@keyframes\s+ripple\s*\{(.+?)\n\}', css_content, re.DOTALL)
        keyframe_content = ripple_keyframes.group(1)
        
        # 检查 transform scale
        assert re.search(r'0%\s*\{.+?scale\(0\.8\)', keyframe_content, re.DOTALL), "ripple 动画 0% 时应 scale(0.8)"
        assert re.search(r'100%\s*\{.+?scale\(2\)', keyframe_content, re.DOTALL), "ripple 动画 100% 时应 scale(2)"
    
    def test_ripple_animation_delays(self):
        """测试 3 层波纹的延迟设置（0s, 0.5s, 1s）"""
        css_content = read_css_content()
        
        # 检查动画延迟（在 voice-animation 状态类中）
        # ring-1: 无延迟或 0s
        has_ring1 = re.search(r'\.voice-animation\.(?:connecting|listening|speaking)\s+\.ring-1\s*\{[^}]*ripple\s+[\d.]+s\s+ease-out(?:\s+0s)?\s+infinite', css_content, re.DOTALL)
        assert has_ring1, "ring-1 应有 ripple 动画（延迟 0s）"
        
        # ring-2: 0.5s 延迟
        has_ring2 = re.search(r'\.voice-animation\.(?:connecting|listening|speaking)\s+\.ring-2\s*\{[^}]*0\.5s\s+infinite', css_content, re.DOTALL)
        assert has_ring2, "ring-2 延迟应为 0.5s"
        
        # ring-3: 1s 延迟
        has_ring3 = re.search(r'\.voice-animation\.(?:connecting|listening|speaking)\s+\.ring-3\s*\{[^}]*1s\s+infinite', css_content, re.DOTALL)
        assert has_ring3, "ring-3 延迟应为 1s"


class TestStateTransition:
    """状态切换动画测试（静态 CSS 分析）"""
    
    def test_pulse_animation_exists(self):
        """测试 pulse 脉冲动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'pulse'), "pulse 动画未定义"
    
    def test_spin_animation_exists(self):
        """测试 spin 旋转动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'spin'), "spin 动画未定义"
    
    def test_fade_in_animation_exists(self):
        """测试 fadeIn 淡入动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'fadeIn'), "fadeIn 动画未定义"
    
    def test_fade_out_animation_exists(self):
        """测试 fadeOut 淡出动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'fadeOut'), "fadeOut 动画未定义"
    
    def test_status_classes_exist(self):
        """测试所有状态类存在"""
        css_content = read_css_content()
        
        states = ['idle', 'connecting', 'listening', 'processing', 'speaking', 'error']
        for state in states:
            assert css_has_class(css_content, state), f"状态类.{state} 未定义"
    
    def test_status_transition_class(self):
        """测试状态切换过渡类"""
        css_content = read_css_content()
        assert css_has_class(css_content, 'status-transition'), "status-transition 类未定义"
    
    def test_connecting_state_pulse_animation(self):
        """测试 connecting 状态脉冲动画"""
        css_content = read_css_content()
        
        # 检查 connecting 状态是否有 pulse 动画
        pattern = r'\.status-indicator\.connecting[^{]*\{[^}]*animation:[^}]*pulse'
        assert re.search(pattern, css_content), "connecting 状态应有 pulse 动画"
    
    def test_processing_state_spin_animation(self):
        """测试 processing 状态旋转动画"""
        css_content = read_css_content()
        
        # 检查 processing 状态的 voice-circle 是否有 spin 动画
        pattern = r'\.voice-animation\.processing\s+\.voice-circle[^{]*\{[^}]*animation:[^}]*spin'
        assert re.search(pattern, css_content), "processing 状态应有 spin 动画"
    
    def test_transition_property_exists(self):
        """测试 transition 属性存在"""
        css_content = read_css_content()
        
        # 检查 status-indicator 是否有 transition
        pattern = r'\.status-indicator\s*\{[^}]*transition:'
        assert re.search(pattern, css_content), "status-indicator 应有 transition 属性"
    
    def test_all_state_transitions_covered(self):
        """测试所有状态切换覆盖"""
        css_content = read_css_content()
        
        # 检查状态切换类
        transitions = [
            'idle-to-connecting',
            'connecting-to-listening',
            'listening-to-processing',
            'processing-to-speaking',
            'speaking-to-idle'
        ]
        
        for transition in transitions:
            assert css_has_class(css_content, transition) or \
                   re.search(rf'{transition}', css_content), \
                   f"状态切换.{transition} 未定义"


class TestButtonAnimations:
    """按钮点击动画测试（静态 CSS 分析）"""
    
    def test_btn_scale_animation_exists(self):
        """测试 btnScale 缩放动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'btnScale'), "btnScale 动画未定义"
    
    def test_btn_shake_animation_exists(self):
        """测试 btnShake 抖动动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'btnShake'), "btnShake 动画未定义"
    
    def test_btn_pulse_animation_exists(self):
        """测试 btnPulse 脉冲动画存在"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'btnPulse'), "btnPulse 动画未定义"
    
    def test_connect_button_animation(self):
        """测试连接按钮动画（缩放 + 变色）"""
        css_content = read_css_content()
        
        # 检查.btn-connect.clicked 动画
        pattern = r'\.btn-connect\.clicked\s*\{[^}]*animation:[^}]*btnScale'
        assert re.search(pattern, css_content), "连接按钮点击应有 btnScale 动画"
    
    def test_hangup_button_animation(self):
        """测试挂断按钮动画（抖动）"""
        css_content = read_css_content()
        
        # 检查.btn-hangup.clicked 动画
        pattern = r'\.btn-hangup\.clicked\s*\{[^}]*animation:[^}]*btnShake'
        assert re.search(pattern, css_content), "挂断按钮点击应有 btnShake 动画"
    
    def test_mic_button_animation(self):
        """测试静音按钮动画（脉冲）"""
        css_content = read_css_content()
        
        # 检查.btn-mic.clicked 动画
        pattern = r'\.btn-mic\.clicked\s*\{[^}]*animation:[^}]*btnPulse'
        assert re.search(pattern, css_content), "静音按钮点击应有 btnPulse 动画"
    
    def test_button_hover_transform(self):
        """测试按钮悬停变换"""
        css_content = read_css_content()
        
        # 检查.control-btn:hover 的 transform
        pattern = r'\.control-btn:hover[^{]*\{[^}]*transform:[^}]*translateY\(-2px\)'
        assert re.search(pattern, css_content), "按钮悬停应有 translateY 变换"
    
    def test_button_classes_exist(self):
        """测试所有按钮类存在"""
        css_content = read_css_content()
        
        buttons = ['btn-connect', 'btn-hangup', 'btn-mic', 'btn-retry']
        for btn in buttons:
            assert css_has_class(css_content, btn), f"按钮类.{btn} 未定义"


class TestAnimationPerformance:
    """动画性能测试（静态 CSS 分析）"""
    
    def test_css_animation_hardware_accelerated(self):
        """测试 CSS 动画使用硬件加速（transform/opacity）"""
        css_content = read_css_content()
        
        # 检查 ripple 动画是否使用 transform（硬件加速）
        ripple_keyframes = re.search(r'@keyframes\s+ripple\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', css_content)
        assert ripple_keyframes, "未找到 ripple 动画关键帧"
        
        keyframe_content = ripple_keyframes.group(1)
        assert 'transform' in keyframe_content, "ripple 动画应使用 transform（硬件加速）"
    
    def test_animation_duration_reasonable(self):
        """测试动画时长合理（不超过 3s）"""
        css_content = read_css_content()
        
        # 查找所有 animation-duration 或 animation 简写
        durations = re.findall(r'animation:[^;]*?(\d+\.?\d*)s', css_content)
        
        for duration in durations:
            dur = float(duration)
            assert dur <= 3.0, f"动画时长{dur}s 过长，应不超过 3s"
    
    def test_no_inline_styles_blocking(self):
        """测试无阻塞内联样式"""
        css_content = read_css_content()
        
        # 检查是否有 animation: none 阻止动画
        assert 'animation: none' not in css_content or \
               '@media (prefers-reduced-motion: reduce)' in css_content, \
               "不应有全局 animation: none（除非在 reduced-motion 媒体查询中）"
    
    def test_easing_functions_appropriate(self):
        """测试缓动函数适当"""
        css_content = read_css_content()
        
        # 检查是否使用了适当的缓动函数
        has_ease = 'ease-out' in css_content or 'ease-in-out' in css_content or 'ease-in' in css_content
        assert has_ease, "应使用适当的缓动函数（ease-out/ease-in-out/ease-in）"


class TestAccessibility:
    """辅助功能测试（静态 CSS 分析）"""
    
    def test_reduced_motion_media_query(self):
        """测试减少动画媒体查询支持"""
        css_content = read_css_content()
        
        # 检查是否有 prefers-reduced-motion 媒体查询
        pattern = r'@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)'
        assert re.search(pattern, css_content), "应支持 prefers-reduced-motion 媒体查询"
    
    def test_reduced_motion_disables_animations(self):
        """测试减少动画媒体查询禁用动画"""
        css_content = read_css_content()
        
        # 检查媒体查询内是否禁用了动画
        reduced_motion = re.search(
            r'@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
            css_content
        )
        
        if reduced_motion:
            media_content = reduced_motion.group(1)
            assert 'animation-duration' in media_content or 'animation: none' in media_content, \
                   "reduced-motion 应禁用或减少动画时长"


class TestAdditionalCoverage:
    """额外测试覆盖"""
    
    def test_shake_animation_exists(self):
        """测试 shake 抖动动画存在（用于错误状态）"""
        css_content = read_css_content()
        assert css_has_animation(css_content, 'shake'), "shake 动画未定义"
    
    def test_voice_animation_container_exists(self):
        """测试 voice-animation 容器类存在"""
        css_content = read_css_content()
        assert css_has_class(css_content, 'voice-animation'), "voice-animation 类未定义"
    
    def test_voice_circle_exists(self):
        """测试 voice-circle 类存在"""
        css_content = read_css_content()
        assert css_has_class(css_content, 'voice-circle'), "voice-circle 类未定义"
    
    def test_error_state_animation(self):
        """测试 error 状态动画"""
        css_content = read_css_content()
        
        # 检查 error 状态的 shake 动画
        pattern = r'\.voice-animation\.error[^{]*\{[^}]*animation:[^}]*shake'
        assert re.search(pattern, css_content, re.DOTALL), "error 状态应有 shake 动画"
    
    def test_btn_retry_animation(self):
        """测试重试按钮动画"""
        css_content = read_css_content()
        
        # 检查.btn-retry.clicked 动画
        pattern = r'\.btn-retry\.clicked\s*\{[^}]*animation:[^}]*btnScale'
        assert re.search(pattern, css_content), "重试按钮点击应有 btnScale 动画"
    
    def test_voice_ring_transparent_base(self):
        """测试波纹环基础透明样式"""
        css_content = read_css_content()
        
        # 检查.voice-ring 的基础 opacity: 0
        pattern = r'\.voice-ring\s*\{[^}]*opacity:\s*0'
        assert re.search(pattern, css_content, re.DOTALL), "voice-ring 基础样式应有 opacity: 0"


class TestRuntimeAnimations:
    """运行时动画测试（需要服务运行，可选）"""
    
    @pytest.mark.skip(reason="需要前端服务运行，手动执行：pytest -m runtime")
    @pytest.mark.runtime
    def test_ripple_rings_visible_runtime(self):
        """测试 3 层波纹环运行时可见"""
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            page.wait_for_selector(".voice-animation", timeout=TIMEOUT)
            
            ring_1 = page.locator(".ring-1")
            ring_2 = page.locator(".ring-2")
            ring_3 = page.locator(".ring-3")
            
            assert ring_1.is_visible(), "ring-1 应可见"
            assert ring_2.is_visible(), "ring-2 应可见"
            assert ring_3.is_visible(), "ring-3 应可见"
            
            browser.close()
    
    @pytest.mark.skip(reason="需要前端服务运行，手动执行：pytest -m runtime")
    @pytest.mark.runtime
    def test_state_transition_runtime(self):
        """测试状态切换运行时效果"""
        from playwright.sync_api import sync_playwright, expect
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_URL, timeout=TIMEOUT)
            
            # 点击连接
            page.click(".btn-connect")
            page.wait_for_timeout(500)
            
            # 验证状态变化
            status = page.locator(".status-indicator")
            expect(status).to_have_attribute("class", ".*connecting.*")
            
            browser.close()


if __name__ == "__main__":
    # 默认运行静态测试
    pytest.main([__file__, "-v", "--tb=short", "-m", "not runtime"])
    
    # 运行所有测试（包括运行时测试，需要服务）
    # pytest.main([__file__, "-v", "--tb=short"])
