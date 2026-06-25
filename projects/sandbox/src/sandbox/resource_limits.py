"""
sandbox.resource_limits - 资源限制模块

使用 POSIX rlimit 和 cgroups 限制进程资源使用。
"""

import os
import ctypes
import ctypes.util
from dataclasses import dataclass
from typing import Optional

# rlimit 常量
RLIMIT_CPU = 0        # CPU 时间限制（秒）
RLIMIT_FSIZE = 1      # 文件大小限制
RLIMIT_DATA = 2       # 数据段大小限制
RLIMIT_STACK = 3      # 栈大小限制
RLIMIT_CORE = 4       # core 文件大小限制
RLIMIT_RSS = 5        # 常驻内存集限制
RLIMIT_NPROC = 6      # 进程数量限制
RLIMIT_NOFILE = 7     # 文件描述符数量限制
RLIMIT_MEMLOCK = 8    # 锁定内存限制
RLIMIT_AS = 9         # 虚拟内存大小限制
RLIMIT_LOCKS = 10     # 文件锁数量限制
RLIMIT_SIGPENDING = 11  # 信号队列限制
RLIMIT_MSGQUEUE = 12  # 消息队列限制
RLIMIT_NICE = 13      # nice 值限制
RLIMIT_RTPRIO = 14    # 实时优先级限制
RLIMIT_RTTIME = 15    # 实时调度限制

RLIM_INFINITY = -1  # 无限制


@dataclass
class rlimit:
    """rlimit 结构"""
    rlim_cur: int = RLIM_INFINITY  # 软限制
    rlim_max: int = RLIM_INFINITY  # 硬限制


class ResourceLimits:
    """
    资源限制管理器

    使用 POSIX rlimit 限制进程资源使用。
    """

    def __init__(self):
        self._libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        self._limits = {}

    def set_limit(self, resource: int, soft: int, hard: Optional[int] = None):
        """
        设置资源限制

        Args:
            resource: 资源类型（RLIMIT_*）
            soft: 软限制
            hard: 硬限制（默认与软限制相同）
        """
        if hard is None:
            hard = soft
        self._limits[resource] = (soft, hard)

    def get_limit(self, resource: int) -> tuple:
        """
        获取资源限制

        Args:
            resource: 资源类型（RLIMIT_*）

        Returns:
            (软限制, 硬限制) 元组
        """

        class rlimit_struct(ctypes.Structure):
            _fields_ = [
                ("rlim_cur", ctypes.c_ulong),
                ("rlim_max", ctypes.c_ulong),
            ]

        rl = rlimit_struct()
        ret = self._libc.getrlimit(resource, ctypes.byref(rl))
        if ret != 0:
            raise OSError(f"getrlimit failed: {ctypes.get_errno()}")

        return (rl.rlim_cur, rl.rlim_max)

    def apply(self,
              memory_limit_mb: int = 0,
              cpu_time_limit_sec: int = 0,
              file_size_limit_mb: int = 0,
              open_files_limit: int = 0,
              process_limit: int = 0,
              stack_limit_mb: int = 0,
              core_dump: bool = False):
        """
        应用资源限制

        Args:
            memory_limit_mb: 虚拟内存限制（MB）
            cpu_time_limit_sec: CPU 时间限制（秒）
            file_size_limit_mb: 文件大小限制（MB）
            open_files_limit: 打开文件数量限制
            process_limit: 进程数量限制
            stack_limit_mb: 栈大小限制（MB）
            core_dump: 是否允许 core dump
        """

        class rlimit_struct(ctypes.Structure):
            _fields_ = [
                ("rlim_cur", ctypes.c_ulong),
                ("rlim_max", ctypes.c_ulong),
            ]

        def _set(resource: int, value: int):
            rl = rlimit_struct()
            rl.rlim_cur = value
            rl.rlim_max = value
            ret = self._libc.setrlimit(resource, ctypes.byref(rl))
            if ret != 0:
                errno = ctypes.get_errno()
                # 忽略一些常见错误
                if errno != 1:  # EPERM
                    pass

        # 虚拟内存限制
        if memory_limit_mb > 0:
            _set(RLIMIT_AS, memory_limit_mb * 1024 * 1024)

        # CPU 时间限制
        if cpu_time_limit_sec > 0:
            _set(RLIMIT_CPU, cpu_time_limit_sec)

        # 文件大小限制
        if file_size_limit_mb > 0:
            _set(RLIMIT_FSIZE, file_size_limit_mb * 1024 * 1024)

        # 打开文件数量限制
        if open_files_limit > 0:
            _set(RLIMIT_NOFILE, open_files_limit)

        # 进程数量限制
        if process_limit > 0:
            _set(RLIMIT_NPROC, process_limit)

        # 栈大小限制
        if stack_limit_mb > 0:
            _set(RLIMIT_STACK, stack_limit_mb * 1024 * 1024)

        # Core dump 限制
        if not core_dump:
            _set(RLIMIT_CORE, 0)

    def apply_config(self, config: dict):
        """
        从配置字典应用资源限制

        Args:
            config: 配置字典，键为资源名称，值为限制值
        """
        resource_map = {
            "cpu": RLIMIT_CPU,
            "memory": RLIMIT_AS,
            "file_size": RLIMIT_FSIZE,
            "stack": RLIMIT_STACK,
            "core": RLIMIT_CORE,
            "nproc": RLIMIT_NOFILE,
            "nofile": RLIMIT_NOFILE,
            "memlock": RLIMIT_MEMLOCK,
        }

        for name, value in config.items():
            if name in resource_map:
                self.set_limit(resource_map[name], value)

    @staticmethod
    def format_limit(resource: int, value: int) -> str:
        """格式化限制值为人类可读字符串"""
        if value == RLIM_INFINITY:
            return "unlimited"

        if resource in (RLIMIT_AS, RLIMIT_DATA, RLIMIT_STACK, RLIMIT_RSS, RLIMIT_MEMLOCK):
            # 内存相关，显示为 MB
            return f"{value / (1024*1024):.1f} MB"
        elif resource == RLIMIT_FSIZE:
            return f"{value / (1024*1024):.1f} MB"
        elif resource == RLIMIT_CPU:
            return f"{value} seconds"
        else:
            return str(value)


class CgroupLimits:
    """
    cgroups 资源限制

    使用 Linux cgroups v2 限制进程资源。
    """

    CGROUP_ROOT = "/sys/fs/cgroup"

    def __init__(self, name: str):
        """
        Args:
            name: cgroup 名称
        """
        self.name = name
        self.path = os.path.join(self.CGROUP_ROOT, name)
        self._created = False

    def create(self):
        """创建 cgroup"""
        os.makedirs(self.path, exist_ok=True)
        self._created = True

    def delete(self):
        """删除 cgroup"""
        if self._created and os.path.exists(self.path):
            try:
                os.rmdir(self.path)
            except OSError:
                pass
            self._created = False

    def set_memory_limit(self, limit_bytes: int):
        """
        设置内存限制

        Args:
            limit_bytes: 内存限制（字节）
        """
        if not self._created:
            self.create()

        # cgroups v2
        max_file = os.path.join(self.path, "memory.max")
        if os.path.exists(max_file):
            with open(max_file, "w") as f:
                f.write(str(limit_bytes))

        # cgroups v1
        limit_file = os.path.join(self.path, "memory.limit_in_bytes")
        if os.path.exists(limit_file):
            with open(limit_file, "w") as f:
                f.write(str(limit_bytes))

    def set_cpu_limit(self, quota_us: int, period_us: int = 100000):
        """
        设置 CPU 限制

        Args:
            quota_us: CPU 配额（微秒）
            period_us: CPU 周期（微秒）
        """
        if not self._created:
            self.create()

        # cgroups v2
        max_file = os.path.join(self.path, "cpu.max")
        if os.path.exists(max_file):
            with open(max_file, "w") as f:
                f.write(f"{quota_us} {period_us}")

        # cgroups v1
        quota_file = os.path.join(self.path, "cpu.cfs_quota_us")
        period_file = os.path.join(self.path, "cpu.cfs_period_us")
        if os.path.exists(quota_file):
            with open(quota_file, "w") as f:
                f.write(str(quota_us))
            with open(period_file, "w") as f:
                f.write(str(period_us))

    def set_pids_limit(self, max_pids: int):
        """
        设置进程数量限制

        Args:
            max_pids: 最大进程数
        """
        if not self._created:
            self.create()

        max_file = os.path.join(self.path, "pids.max")
        if os.path.exists(max_file):
            with open(max_file, "w") as f:
                f.write(str(max_pids))

    def add_process(self, pid: int):
        """将进程添加到 cgroup"""
        if not self._created:
            self.create()

        procs_file = os.path.join(self.path, "cgroup.procs")
        if os.path.exists(procs_file):
            with open(procs_file, "w") as f:
                f.write(str(pid))

    def get_memory_usage(self) -> int:
        """获取当前内存使用量（字节）"""
        usage_file = os.path.join(self.path, "memory.current")
        if os.path.exists(usage_file):
            with open(usage_file, "r") as f:
                return int(f.read().strip())

        usage_file = os.path.join(self.path, "memory.usage_in_bytes")
        if os.path.exists(usage_file):
            with open(usage_file, "r") as f:
                return int(f.read().strip())

        return 0

    def get_pids_count(self) -> int:
        """获取当前进程数"""
        pids_file = os.path.join(self.path, "pids.current")
        if os.path.exists(pids_file):
            with open(pids_file, "r") as f:
                return int(f.read().strip())
        return 0

    def __enter__(self):
        self.create()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.delete()
        return False
