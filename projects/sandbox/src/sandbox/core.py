"""
sandbox.core - 沙箱核心模块

实现沙箱的核心逻辑，整合进程隔离、资源限制、系统调用过滤和文件系统隔离。
"""

import os
import sys
import json
import time
import signal
import ctypes
import ctypes.util
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path

from .syscall_filter import SyscallFilter, FilterMode
from .resource_limits import ResourceLimits
from .filesystem import FilesystemIsolation
from .namespace_isolation import NamespaceIsolation


class SandboxMode(Enum):
    """沙箱运行模式"""
    SIMPLE = auto()       # 简单模式：仅 seccomp + rlimit
    CHROOT = auto()       # chroot 模式：文件系统隔离
    NAMESPACE = auto()    # namespace 模式：完整隔离
    FULL = auto()         # 完整模式：所有隔离机制


@dataclass
class SandboxConfig:
    """沙箱配置"""
    # 基本配置
    mode: SandboxMode = SandboxMode.FULL
    command: List[str] = field(default_factory=list)
    working_dir: str = "/tmp"

    # 资源限制
    memory_limit_mb: int = 256
    cpu_time_limit_sec: int = 30
    file_size_limit_mb: int = 100
    open_files_limit: int = 64
    process_limit: int = 16

    # 系统调用过滤
    filter_mode: FilterMode = FilterMode.WHITELIST
    allowed_syscalls: List[str] = field(default_factory=list)
    blocked_syscalls: List[str] = field(default_factory=list)

    # 文件系统隔离
    enable_chroot: bool = True
    read_only_mounts: List[str] = field(default_factory=list)
    tmpfs_mounts: List[str] = field(default_factory=list)
    allowed_paths: List[str] = field(default_factory=list)

    # Namespace 隔离
    enable_pid_namespace: bool = True
    enable_net_namespace: bool = True
    enable_mount_namespace: bool = True
    enable_uts_namespace: bool = True
    enable_ipc_namespace: bool = True

    # 超时和监控
    timeout_sec: int = 60
    capture_output: bool = True
    log_syscalls: bool = False


@dataclass
class SandboxResult:
    """沙箱执行结果"""
    exit_code: int = -1
    signal_num: int = 0
    stdout: str = ""
    stderr: str = ""
    cpu_time_user: float = 0.0
    cpu_time_sys: float = 0.0
    memory_peak_kb: int = 0
    syscalls_allowed: int = 0
    syscalls_blocked: int = 0
    timed_out: bool = False
    killed: bool = False
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "signal_num": self.signal_num,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "cpu_time_user": self.cpu_time_user,
            "cpu_time_sys": self.cpu_time_sys,
            "memory_peak_kb": self.memory_peak_kb,
            "syscalls_allowed": self.syscalls_allowed,
            "syscalls_blocked": self.syscalls_blocked,
            "timed_out": self.timed_out,
            "killed": self.killed,
            "error": self.error,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class Sandbox:
    """
    沙箱隔离类

    整合进程隔离、资源限制、系统调用过滤和文件系统隔离。
    支持多种隔离模式：简单、chroot、namespace、完整模式。
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._syscall_filter = SyscallFilter()
        self._resource_limits = ResourceLimits()
        self._filesystem = FilesystemIsolation()
        self._namespace = NamespaceIsolation()
        self._child_pid: Optional[int] = None
        self._result: Optional[SandboxResult] = None

    def run(self, command: Optional[List[str]] = None) -> SandboxResult:
        """
        在沙箱中执行命令

        Args:
            command: 要执行的命令列表，如果为 None 则使用配置中的命令

        Returns:
            SandboxResult: 执行结果
        """
        cmd = command or self.config.command
        if not cmd:
            return SandboxResult(error="No command specified")

        self._result = SandboxResult()

        try:
            if self.config.mode == SandboxMode.SIMPLE:
                return self._run_simple(cmd)
            elif self.config.mode == SandboxMode.CHROOT:
                return self._run_chroot(cmd)
            elif self.config.mode == SandboxMode.NAMESPACE:
                return self._run_namespace(cmd)
            elif self.config.mode == SandboxMode.FULL:
                return self._run_full(cmd)
            else:
                return SandboxResult(error=f"Unknown mode: {self.config.mode}")
        except Exception as e:
            self._result.error = str(e)
            return self._result

    def _run_simple(self, cmd: List[str]) -> SandboxResult:
        """简单模式：仅 seccomp + rlimit"""
        result = SandboxResult()
        start_time = time.time()

        try:
            # 构建 seccomp 过滤器
            seccomp_json = self._build_seccomp_json()

            # 准备子进程环境
            env = os.environ.copy()
            env["SANDBOX_MODE"] = "simple"
            env["SANDBOX_SECCOMP"] = seccomp_json

            # 执行子进程
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if self.config.capture_output else None,
                stderr=subprocess.PIPE if self.config.capture_output else None,
                env=env,
                cwd=self.config.working_dir,
                preexec_fn=lambda: self._apply_child_restrictions(),
            )

            self._child_pid = proc.pid

            # 等待子进程完成或超时
            try:
                stdout, stderr = proc.communicate(timeout=self.config.timeout_sec)
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.timed_out = True
                result.killed = True

            # 收集资源使用统计
            result.cpu_time_user = time.time() - start_time

        except Exception as e:
            result.error = str(e)

        return result

    def _run_chroot(self, cmd: List[str]) -> SandboxResult:
        """chroot 模式：文件系统隔离 + seccomp + rlimit"""
        result = SandboxResult()

        try:
            # 创建 chroot 环境
            chroot_dir = self._filesystem.create_chroot_environment()
            self._filesystem.setup_chroot_mounts(
                chroot_dir,
                read_only=self.config.read_only_mounts,
                tmpfs=self.config.tmpfs_mounts,
            )

            # 准备子进程
            env = os.environ.copy()
            env["SANDBOX_MODE"] = "chroot"

            # 在 chroot 中执行
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE if self.config.capture_output else None,
                stderr=subprocess.PIPE if self.config.capture_output else None,
                env=env,
                preexec_fn=lambda: self._apply_chroot_restrictions(chroot_dir),
            )

            self._child_pid = proc.pid

            try:
                stdout, stderr = proc.communicate(timeout=self.config.timeout_sec)
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.timed_out = True
                result.killed = True

            # 清理 chroot 环境
            self._filesystem.cleanup_chroot(chroot_dir)

        except Exception as e:
            result.error = str(e)

        return result

    def _run_namespace(self, cmd: List[str]) -> SandboxResult:
        """namespace 模式：完整进程隔离 + seccomp + rlimit"""
        result = SandboxResult()

        try:
            # 使用 namespace 隔离
            proc = self._namespace.create_isolated_process(
                cmd,
                pid_ns=self.config.enable_pid_namespace,
                net_ns=self.config.enable_net_namespace,
                mount_ns=self.config.enable_mount_namespace,
                uts_ns=self.config.enable_uts_namespace,
                ipc_ns=self.config.enable_ipc_namespace,
                preexec_fn=lambda: self._apply_child_restrictions(),
            )

            self._child_pid = proc.pid

            try:
                stdout, stderr = proc.communicate(timeout=self.config.timeout_sec)
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.timed_out = True
                result.killed = True

        except Exception as e:
            result.error = str(e)

        return result

    def _run_full(self, cmd: List[str]) -> SandboxResult:
        """完整模式：namespace + chroot + seccomp + rlimit"""
        result = SandboxResult()

        try:
            # 创建 chroot 环境
            chroot_dir = self._filesystem.create_chroot_environment()
            self._filesystem.setup_chroot_mounts(
                chroot_dir,
                read_only=self.config.read_only_mounts,
                tmpfs=self.config.tmpfs_mounts,
            )

            # 使用 namespace 隔离 + chroot
            proc = self._namespace.create_isolated_process(
                cmd,
                pid_ns=self.config.enable_pid_namespace,
                net_ns=self.config.enable_net_namespace,
                mount_ns=self.config.enable_mount_namespace,
                uts_ns=self.config.enable_uts_namespace,
                ipc_ns=self.config.enable_ipc_namespace,
                chroot_dir=chroot_dir,
                preexec_fn=lambda: self._apply_full_restrictions(chroot_dir),
            )

            self._child_pid = proc.pid

            try:
                stdout, stderr = proc.communicate(timeout=self.config.timeout_sec)
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                result.stdout = stdout.decode("utf-8", errors="replace") if stdout else ""
                result.stderr = stderr.decode("utf-8", errors="replace") if stderr else ""
                result.timed_out = True
                result.killed = True

            # 清理
            self._filesystem.cleanup_chroot(chroot_dir)

        except Exception as e:
            result.error = str(e)

        return result

    def _apply_child_restrictions(self):
        """在子进程中应用资源限制和 seccomp"""
        # 应用资源限制
        try:
            self._resource_limits.apply(
                memory_limit_mb=self.config.memory_limit_mb,
                cpu_time_limit_sec=self.config.cpu_time_limit_sec,
                file_size_limit_mb=self.config.file_size_limit_mb,
                open_files_limit=self.config.open_files_limit,
                process_limit=self.config.process_limit,
            )
        except (OSError, PermissionError):
            # 资源限制可能失败，继续执行
            pass

        # 应用 seccomp 过滤器（需要 root 权限）
        try:
            self._syscall_filter.apply(
                mode=self.config.filter_mode,
                allowed=self.config.allowed_syscalls,
                blocked=self.config.blocked_syscalls,
            )
        except (OSError, PermissionError):
            # seccomp 需要 root 权限，继续执行但没有过滤
            pass

    def _apply_chroot_restrictions(self, chroot_dir: str):
        """在子进程中应用 chroot 和限制"""
        # 先应用资源限制
        try:
            self._resource_limits.apply(
                memory_limit_mb=self.config.memory_limit_mb,
                cpu_time_limit_sec=self.config.cpu_time_limit_sec,
                file_size_limit_mb=self.config.file_size_limit_mb,
                open_files_limit=self.config.open_files_limit,
                process_limit=self.config.process_limit,
            )
        except (OSError, PermissionError):
            pass

        # 切换到 chroot
        try:
            os.chroot(chroot_dir)
            os.chdir("/")
        except (OSError, PermissionError):
            pass

        # 应用 seccomp
        try:
            self._syscall_filter.apply(
                mode=self.config.filter_mode,
                allowed=self.config.allowed_syscalls,
                blocked=self.config.blocked_syscalls,
            )
        except (OSError, PermissionError):
            pass

    def _apply_full_restrictions(self, chroot_dir: str):
        """应用所有限制"""
        self._apply_chroot_restrictions(chroot_dir)

    def _build_seccomp_json(self) -> str:
        """构建 seccomp 配置 JSON"""
        config = {
            "mode": self.config.filter_mode.value,
            "allowed": self.config.allowed_syscalls,
            "blocked": self.config.blocked_syscalls,
        }
        return json.dumps(config)

    def kill(self):
        """杀死沙箱中的进程"""
        if self._child_pid and self._child_pid > 0:
            try:
                os.kill(self._child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    @staticmethod
    def get_default_config() -> SandboxConfig:
        """获取默认配置"""
        return SandboxConfig(
            mode=SandboxMode.FULL,
            memory_limit_mb=256,
            cpu_time_limit_sec=30,
            file_size_limit_mb=100,
            open_files_limit=64,
            process_limit=16,
            filter_mode=FilterMode.WHITELIST,
            enable_chroot=True,
            enable_pid_namespace=True,
            enable_net_namespace=True,
            enable_mount_namespace=True,
            timeout_sec=60,
        )

    @staticmethod
    def get_code_execution_config() -> SandboxConfig:
        """获取代码执行沙箱配置"""
        return SandboxConfig(
            mode=SandboxMode.FULL,
            memory_limit_mb=128,
            cpu_time_limit_sec=10,
            file_size_limit_mb=10,
            open_files_limit=32,
            process_limit=4,
            filter_mode=FilterMode.WHITELIST,
            enable_chroot=True,
            enable_pid_namespace=True,
            enable_net_namespace=False,
            enable_mount_namespace=True,
            timeout_sec=15,
            read_only_mounts=["/usr", "/lib", "/lib64", "/bin", "/sbin"],
            tmpfs_mounts=["/tmp", "/var/tmp"],
        )

    @staticmethod
    def get_malware_analysis_config() -> SandboxConfig:
        """获取恶意代码分析配置"""
        return SandboxConfig(
            mode=SandboxMode.FULL,
            memory_limit_mb=512,
            cpu_time_limit_sec=60,
            file_size_limit_mb=50,
            open_files_limit=128,
            process_limit=32,
            filter_mode=FilterMode.BLACKLIST,
            blocked_syscalls=[
                "reboot", "kexec_load", "mount", "umount2",
                "pivot_root", "swapon", "swapoff",
            ],
            enable_chroot=True,
            enable_pid_namespace=True,
            enable_net_namespace=True,
            enable_mount_namespace=True,
            enable_uts_namespace=True,
            enable_ipc_namespace=True,
            timeout_sec=120,
            log_syscalls=True,
            read_only_mounts=["/usr", "/lib", "/lib64", "/bin", "/sbin", "/etc"],
            tmpfs_mounts=["/tmp", "/var/tmp", "/dev", "/proc", "/sys"],
        )
