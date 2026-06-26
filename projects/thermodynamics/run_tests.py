"""
热力学模拟 (Thermodynamics Simulation)
热传导和热对流模拟学习项目

本项目旨在通过数值模拟方法学习和理解热力学基本原理，
特别是热传导和热对流过程。
"""

# 运行测试
import subprocess
import sys
import os

test_dir = os.path.join(os.path.dirname(__file__), "tests")
result = subprocess.run(
    [sys.executable, "-m", "pytest", test_dir, "-v"],
    cwd=os.path.dirname(__file__),
)
sys.exit(result.returncode)
