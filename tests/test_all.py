#!/usr/bin/env python3
"""
完整测试套件 - 运行所有测试
"""

import sys
import os
import subprocess

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def run_test(test_file, description):
    """运行单个测试文件"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 {description}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False,
        text=True
    )
    
    return result.returncode == 0

def main():
    """运行所有测试"""
    print("\n")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}🧪 AI Voice Agent 完整测试套件{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = {
        'E2E 测试': run_test(
            os.path.join(test_dir, 'test_e2e.py'),
            '端到端自动化测试'
        ),
        'STT 测试': run_test(
            os.path.join(test_dir, 'test_stt.py'),
            'STT API 单元测试'
        ),
    }
    
    # 汇总报告
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}📊 总测试报告{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print()
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ 通过{Colors.END}" if result else f"{Colors.RED}❌ 失败{Colors.END}"
        print(f"{test_name}: {status}")
    
    print()
    print(f"总测试套件：{total}")
    print(f"通过：{Colors.GREEN}{passed}{Colors.END}")
    print(f"失败：{Colors.RED}{failed}{Colors.END}")
    print(f"通过率：{pass_rate:.1f}%")
    print()
    
    if failed == 0:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠️  有 {failed} 个测试套件失败，请修复{Colors.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
