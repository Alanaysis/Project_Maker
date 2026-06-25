"""
sandbox - 沙箱隔离模块

提供进程隔离、资源限制、系统调用过滤和文件系统隔离功能。
"""

from .core import Sandbox, SandboxConfig, SandboxResult
from .syscall_filter import SyscallFilter, FilterMode
from .resource_limits import ResourceLimits
from .filesystem import FilesystemIsolation
from .namespace_isolation import NamespaceIsolation

__version__ = "1.0.0"
__all__ = [
    "Sandbox",
    "SandboxConfig",
    "SandboxResult",
    "SyscallFilter",
    "FilterMode",
    "ResourceLimits",
    "FilesystemIsolation",
    "NamespaceIsolation",
]
