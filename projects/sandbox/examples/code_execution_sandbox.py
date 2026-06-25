#!/usr/bin/env python3
"""
code_execution_sandbox.py - 代码执行沙箱

在安全的沙箱环境中执行不受信任的代码。

使用方法:
    python code_execution_sandbox.py <代码文件或命令>
    python code_execution_sandbox.py -c "print('Hello')"
    python code_execution_sandbox.py script.py

功能:
    - 进程隔离（namespace）
    - 文件系统隔离（chroot）
    - 资源限制（CPU、内存、文件大小）
    - 系统调用过滤（seccomp）
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sandbox.core import Sandbox, SandboxConfig, SandboxMode
from sandbox.syscall_filter import FilterMode


def create_code_execution_sandbox(config: dict = None) -> Sandbox:
    """
    创建代码执行沙箱

    Args:
        config: 额外配置

    Returns:
        Sandbox 实例
    """
    # 获取预设配置
    sandbox_config = Sandbox.get_code_execution_config()

    # 应用额外配置
    if config:
        for key, value in config.items():
            if hasattr(sandbox_config, key):
                setattr(sandbox_config, key, value)

    return Sandbox(sandbox_config)


def execute_python_code(code: str, timeout: int = 10) -> dict:
    """
    在沙箱中执行 Python 代码

    Args:
        code: Python 代码
        timeout: 超时时间（秒）

    Returns:
        执行结果字典
    """
    # 将代码写入临时文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        code_file = f.name

    try:
        # 创建沙箱
        config = Sandbox.get_code_execution_config()
        config.timeout_sec = timeout
        config.command = ["python3", code_file]

        sandbox = Sandbox(config)
        result = sandbox.run()

        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "error": result.error,
        }
    finally:
        # 清理临时文件
        try:
            os.unlink(code_file)
        except OSError:
            pass


def execute_command(command: list, timeout: int = 30) -> dict:
    """
    在沙箱中执行命令

    Args:
        command: 命令列表
        timeout: 超时时间（秒）

    Returns:
        执行结果字典
    """
    config = Sandbox.get_code_execution_config()
    config.timeout_sec = timeout
    config.command = command

    sandbox = Sandbox(config)
    result = sandbox.run()

    return {
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
        "error": result.error,
    }


def main():
    parser = argparse.ArgumentParser(
        description="代码执行沙箱 - 在安全环境中执行不受信任的代码"
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="要执行的命令或脚本文件",
    )
    parser.add_argument(
        "-c", "--code",
        help="直接执行 Python 代码",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="超时时间（秒，默认 10）",
    )
    parser.add_argument(
        "-m", "--memory",
        type=int,
        default=128,
        help="内存限制（MB，默认 128）",
    )
    parser.add_argument(
        "--mode",
        choices=["simple", "chroot", "namespace", "full"],
        default="full",
        help="沙箱模式（默认 full）",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="禁用网络",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出",
    )

    args = parser.parse_args()

    # 模式映射
    mode_map = {
        "simple": SandboxMode.SIMPLE,
        "chroot": SandboxMode.CHROOT,
        "namespace": SandboxMode.NAMESPACE,
        "full": SandboxMode.FULL,
    }

    # 准备配置
    config = {
        "mode": mode_map[args.mode],
        "memory_limit_mb": args.memory,
        "timeout_sec": args.timeout,
        "enable_net_namespace": not args.no_network,
    }

    if args.code:
        # 执行 Python 代码
        print(f"[SANDBOX] 执行 Python 代码 (超时: {args.timeout}s, 内存: {args.memory}MB)")
        result = execute_python_code(args.code, timeout=args.timeout)
    elif args.command:
        # 执行命令
        if os.path.isfile(args.command):
            # 是脚本文件
            print(f"[SANDBOX] 执行脚本: {args.command}")
            result = execute_command(
                ["python3", args.command],
                timeout=args.timeout,
            )
        else:
            # 是命令
            print(f"[SANDBOX] 执行命令: {args.command}")
            result = execute_command(
                ["sh", "-c", args.command],
                timeout=args.timeout,
            )
    else:
        parser.print_help()
        return 1

    # 输出结果
    print("\n=== 执行结果 ===")
    print(f"退出码: {result['exit_code']}")

    if result["timed_out"]:
        print("状态: 超时")

    if result["error"]:
        print(f"错误: {result['error']}")

    if result["stdout"]:
        print("\n--- 标准输出 ---")
        print(result["stdout"])

    if result["stderr"]:
        print("\n--- 标准错误 ---")
        print(result["stderr"])

    if args.verbose:
        print("\n--- 详细信息 ---")
        print(f"超时: {result['timed_out']}")
        print(f"错误: {result['error']}")

    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main() or 0)
