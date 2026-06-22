"""
测试运行脚本

⭐ 重点：运行所有测试并显示结果
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Running Quantitative Trading System Tests")
    print("=" * 60)

    # 运行测试
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ])

    print("=" * 60)
    if exit_code == 0:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
