"""
运行所有测试
"""
import sys
import os

# 添加项目根目录
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_bezier_engine import run_all_tests

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
