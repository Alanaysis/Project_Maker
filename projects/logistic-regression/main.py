#!/usr/bin/env python3
"""
逻辑回归项目主入口

运行方式: python main.py
"""

import sys
import os

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from examples.basic_usage import main as run_basic_example


def main():
    """运行示例"""
    print("正在运行逻辑回归示例...\n")
    run_basic_example()


if __name__ == '__main__':
    main()
