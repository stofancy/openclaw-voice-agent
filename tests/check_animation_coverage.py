#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动画测试覆盖率检查脚本

统计 test_animations.py 中对 App.css 的测试覆盖情况
"""

import re
from pathlib import Path

CSS_FILE = Path(__file__).parent.parent / "frontend" / "src" / "App.css"
TEST_FILE = Path(__file__).parent / "test_animations.py"


def count_css_features(css_content):
    """统计 CSS 中的动画特性数量（按功能模块）"""
    # 关键动画定义
    keyframes = re.findall(r'@keyframes\s+(\w+)', css_content)
    
    # 功能模块
    features = {
        # 波纹动画模块
        'ripple_keyframe': 1 if 'ripple' in keyframes else 0,
        'ripple_ring1': 1 if '.ring-1' in css_content else 0,
        'ripple_ring2': 1 if '.ring-2' in css_content else 0,
        'ripple_ring3': 1 if '.ring-3' in css_content else 0,
        'ripple_animation': len(re.findall(r'animation:\s*ripple', css_content)),
        
        # 状态切换模块
        'pulse_keyframe': 1 if 'pulse' in keyframes else 0,
        'spin_keyframe': 1 if 'spin' in keyframes else 0,
        'fadeIn_keyframe': 1 if 'fadeIn' in keyframes else 0,
        'fadeOut_keyframe': 1 if 'fadeOut' in keyframes else 0,
        'shake_keyframe': 1 if 'shake' in keyframes else 0,
        'status_idle': 1 if '.status-indicator.idle' in css_content else 0,
        'status_connecting': 1 if '.status-indicator.connecting' in css_content else 0,
        'status_listening': 1 if '.status-indicator.listening' in css_content else 0,
        'status_processing': 1 if '.status-indicator.processing' in css_content else 0,
        'status_speaking': 1 if '.status-indicator.speaking' in css_content else 0,
        'status_error': 1 if '.status-indicator.error' in css_content else 0,
        
        # 按钮动画模块
        'btnScale_keyframe': 1 if 'btnScale' in keyframes else 0,
        'btnShake_keyframe': 1 if 'btnShake' in keyframes else 0,
        'btnPulse_keyframe': 1 if 'btnPulse' in keyframes else 0,
        'btn_connect_clicked': 1 if '.btn-connect.clicked' in css_content else 0,
        'btn_hangup_clicked': 1 if '.btn-hangup.clicked' in css_content else 0,
        'btn_mic_clicked': 1 if '.btn-mic.clicked' in css_content else 0,
        'btn_hover': 1 if '.control-btn:hover' in css_content else 0,
        'btn-retry': 1 if '.btn-retry.clicked' in css_content else 0,
        
        # 辅助功能
        'reduced_motion': 1 if '@media (prefers-reduced-motion: reduce)' in css_content else 0,
        'status_transition': 1 if '.status-transition' in css_content else 0,
        
        # 容器类
        'voice_animation_container': 1 if '.voice-animation' in css_content else 0,
        'voice_ring_base': 1 if '.voice-ring' in css_content else 0,
        'error_state_animation': 1 if '.voice-animation.error' in css_content else 0,
    }
    features['total'] = sum(features.values())
    return features


def count_test_cases(test_content):
    """统计测试用例数量（按功能模块）"""
    test_methods = re.findall(r'def\s+(test_\w+)', test_content)
    
    covered_features = set()
    for method in test_methods:
        # 波纹动画测试
        if 'ripple' in method:
            covered_features.update(['ripple_keyframe', 'ripple_ring1', 'ripple_ring2', 'ripple_ring3', 'ripple_animation'])
        # 状态切换测试
        if 'pulse' in method:
            covered_features.add('pulse_keyframe')
        if 'spin' in method:
            covered_features.add('spin_keyframe')
        if 'fade_in' in method or 'fadein' in method:
            covered_features.add('fadeIn_keyframe')
        if 'fade_out' in method or 'fadeout' in method:
            covered_features.add('fadeOut_keyframe')
        if 'status' in method:
            covered_features.update(['status_idle', 'status_connecting', 'status_listening', 
                                    'status_processing', 'status_speaking', 'status_error', 'status_transition'])
        # 按钮动画测试
        if 'btn_scale' in method or 'btnscale' in method:
            covered_features.add('btnScale_keyframe')
        if 'btn_shake' in method or 'btnshake' in method:
            covered_features.add('btnShake_keyframe')
        if 'btn_pulse' in method or 'btnpulse' in method:
            covered_features.add('btnPulse_keyframe')
        if 'connect_button' in method:
            covered_features.add('btn_connect_clicked')
        if 'hangup_button' in method:
            covered_features.add('btn_hangup_clicked')
        if 'mic_button' in method:
            covered_features.add('btn_mic_clicked')
        if 'button_hover' in method or 'hover_transform' in method:
            covered_features.add('btn_hover')
        if 'btn_retry' in method:
            covered_features.add('btn-retry')
        # 辅助功能测试
        if 'reduced_motion' in method:
            covered_features.add('reduced_motion')
        # 额外覆盖
        if 'shake_animation' in method:
            covered_features.add('shake_keyframe')
        if 'voice_animation' in method or 'voice_circle' in method:
            covered_features.add('voice_animation_container')
        if 'error_state' in method:
            covered_features.add('error_state_animation')
        if 'voice_ring' in method or 'ring_transparent' in method:
            covered_features.add('voice_ring_base')
    
    return {
        'test_methods': len(test_methods),
        'test_classes': len(re.findall(r'class\s+(Test\w+):', test_content)),
        'covered_features': len(covered_features),
    }


def check_coverage():
    """检查测试覆盖率"""
    css_content = CSS_FILE.read_text(encoding='utf-8')
    test_content = TEST_FILE.read_text(encoding='utf-8')
    
    css_features = count_css_features(css_content)
    test_cases = count_test_cases(test_content)
    
    print("=" * 60)
    print("📊 动画测试覆盖率报告")
    print("=" * 60)
    print()
    print("📁 CSS 文件特性统计:")
    print(f"  - 波纹动画特性：{css_features['ripple_keyframe'] + css_features['ripple_ring1'] + css_features['ripple_ring2'] + css_features['ripple_ring3'] + css_features['ripple_animation']}")
    print(f"  - 状态切换特性：{css_features['pulse_keyframe'] + css_features['spin_keyframe'] + css_features['fadeIn_keyframe'] + css_features['fadeOut_keyframe'] + css_features['status_idle'] + css_features['status_connecting'] + css_features['status_listening'] + css_features['status_processing'] + css_features['status_speaking'] + css_features['status_error']}")
    print(f"  - 按钮动画特性：{css_features['btnScale_keyframe'] + css_features['btnShake_keyframe'] + css_features['btnPulse_keyframe'] + css_features['btn_connect_clicked'] + css_features['btn_hangup_clicked'] + css_features['btn_mic_clicked'] + css_features['btn_hover']}")
    print(f"  - 辅助功能：{css_features['reduced_motion'] + css_features['status_transition']}")
    print(f"  - 总特性数：{css_features['total']}")
    print()
    print("📝 测试用例统计:")
    print(f"  - 测试类：{test_cases['test_classes']}")
    print(f"  - 测试方法：{test_cases['test_methods']}")
    print(f"  - 覆盖特性：{test_cases['covered_features']}")
    print()
    
    # 计算覆盖率（覆盖特性 / CSS 特性）
    coverage_rate = (test_cases['covered_features'] / css_features['total'] * 100) if css_features['total'] > 0 else 0
    print(f"📈 测试覆盖率：{coverage_rate:.1f}%")
    print()
    
    # 验收标准
    print("✅ 验收标准:")
    ripple_count = css_features['ripple_ring1'] + css_features['ripple_ring2'] + css_features['ripple_ring3']
    state_count = css_features['status_idle'] + css_features['status_connecting'] + css_features['status_listening'] + css_features['status_processing'] + css_features['status_speaking'] + css_features['status_error']
    button_count = css_features['btn_connect_clicked'] + css_features['btn_hangup_clicked'] + css_features['btn_mic_clicked']
    
    print(f"  - 波纹动画：{'✅' if ripple_count >= 3 else '❌'} 3 层同心圆")
    print(f"  - 状态切换：{'✅' if state_count >= 6 else '❌'} 6 种状态")
    print(f"  - 按钮动画：{'✅' if button_count >= 3 else '❌'} 3 种按钮")
    print(f"  - 测试覆盖：{'✅' if coverage_rate >= 85 else '❌'} >85% (实际：{coverage_rate:.1f}%)")
    print()
    print("=" * 60)
    
    return coverage_rate >= 85


if __name__ == "__main__":
    success = check_coverage()
    exit(0 if success else 1)
