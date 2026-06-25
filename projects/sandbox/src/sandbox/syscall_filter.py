"""
sandbox.syscall_filter - 系统调用过滤模块

实现 seccomp BPF 系统调用过滤，支持白名单和黑名单模式。
"""

import os
import struct
import ctypes
import ctypes.util
from enum import Enum
from typing import List, Optional, Dict, Set

# seccomp 常量
SECCOMP_MODE_DISABLED = 0
SECCOMP_MODE_STRICT = 1
SECCOMP_MODE_FILTER = 2

SECCOMP_RET_KILL = 0x00000000
SECCOMP_RET_TRAP = 0x00030000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_LOG = 0x00070000
SECCOMP_RET_ALLOW = 0x7FFF0000

PR_SET_NO_NEW_PRIVS = 38
PR_SET_SECCOMP = 22
PR_GET_SECCOMP = 21

# BPF 指令常量
BPF_LD = 0x00
BPF_W = 0x00
BPF_ABS = 0x20
BPF_JMP = 0x05
BPF_JEQ = 0x10
BPF_K = 0x00
BPF_RET = 0x06

# Architecture constants
AUDIT_ARCH_X86_64 = 0xC000003E
AUDIT_ARCH_AARCH64 = 0xC00000B7
AUDIT_ARCH_I386 = 0x40000003
AUDIT_ARCH_ARM = 0x40000028

# Get current architecture
import platform
import struct

def _get_audit_arch():
    """Get the audit architecture constant for the current system"""
    machine = platform.machine()
    if machine == "x86_64" or machine == "amd64":
        return AUDIT_ARCH_X86_64
    elif machine == "aarch64" or machine == "arm64":
        return AUDIT_ARCH_AARCH64
    elif machine == "i386" or machine == "i686":
        return AUDIT_ARCH_I386
    elif machine == "armv7l" or machine == "armv6l":
        return AUDIT_ARCH_ARM
    else:
        # Default to x86_64
        return AUDIT_ARCH_X86_64

def _get_seccomp_data_arch_offset():
    """Get the offset of the arch field in seccomp_data"""
    # seccomp_data is defined as:
    # struct seccomp_data {
    #     int nr;                    // offset 0
    #     __u32 arch;                // offset 4
    #     __u64 instruction_pointer; // offset 8
    #     __u64 args[6];             // offset 16
    # };
    return 4

def _get_seccomp_data_nr_offset():
    """Get the offset of the nr field in seccomp_data"""
    return 0


class FilterMode(Enum):
    """系统调用过滤模式"""
    WHITELIST = "whitelist"  # 只允许列出的系统调用
    BLACKLIST = "blacklist"  # 阻止列出的系统调用


# x86_64 系统调用号映射
SYSCALL_TABLE_X86_64: Dict[str, int] = {
    "read": 0,
    "write": 1,
    "open": 2,
    "close": 3,
    "stat": 4,
    "fstat": 5,
    "lstat": 6,
    "poll": 7,
    "lseek": 8,
    "mmap": 9,
    "mprotect": 10,
    "munmap": 11,
    "brk": 12,
    "rt_sigaction": 13,
    "rt_sigprocmask": 14,
    "rt_sigreturn": 15,
    "ioctl": 16,
    "pread64": 17,
    "pwrite64": 18,
    "readv": 19,
    "writev": 20,
    "access": 21,
    "pipe": 22,
    "select": 23,
    "sched_yield": 24,
    "mremap": 25,
    "msync": 26,
    "madvise": 28,
    "dup": 32,
    "dup2": 33,
    "nanosleep": 35,
    "getpid": 39,
    "clone": 56,
    "fork": 57,
    "vfork": 58,
    "execve": 59,
    "exit": 60,
    "wait4": 61,
    "kill": 62,
    "uname": 63,
    "fcntl": 72,
    "flock": 73,
    "fsync": 74,
    "fdatasync": 75,
    "ftruncate": 77,
    "getdents": 78,
    "getcwd": 79,
    "chdir": 80,
    "mkdir": 83,
    "rmdir": 84,
    "creat": 85,
    "unlink": 87,
    "readlink": 89,
    "chmod": 90,
    "fchmod": 91,
    "chown": 92,
    "fchown": 93,
    "lchown": 94,
    "umask": 95,
    "getuid": 102,
    "getgid": 104,
    "geteuid": 107,
    "getegid": 108,
    "setpgid": 109,
    "getppid": 110,
    "setsid": 112,
    "setuid": 105,
    "setgid": 106,
    "getgroups": 115,
    "setgroups": 116,
    "sigaltstack": 131,
    "arch_prctl": 158,
    "futex": 202,
    "set_tid_address": 218,
    "clock_gettime": 228,
    "exit_group": 231,
    "epoll_wait": 232,
    "epoll_ctl": 233,
    "tgkill": 234,
    "openat": 257,
    "mkdirat": 258,
    "unlinkat": 263,
    "renameat": 264,
    "readlinkat": 267,
    "faccessat": 269,
    "dup3": 292,
    "epoll_create1": 291,
    "pipe2": 293,
    "clock_gettime64": 403,
    "newfstatat": 262,
    "set_robust_list": 273,
    "getrandom": 318,
    "prlimit64": 302,
    "statfs": 137,
    "getrlimit": 97,
    "getdents64": 217,
    "close_range": 436,
    "rseq": 334,
}

# aarch64 系统调用号映射
SYSCALL_TABLE_AARCH64: Dict[str, int] = {
    "read": 63,
    "write": 64,
    "open": 56,
    "close": 57,
    "stat": 78,
    "fstat": 80,
    "lstat": 79,
    "poll": 7,
    "lseek": 62,
    "mmap": 222,
    "mprotect": 226,
    "munmap": 215,
    "brk": 214,
    "rt_sigaction": 134,
    "rt_sigprocmask": 135,
    "rt_sigreturn": 139,
    "ioctl": 29,
    "pread64": 67,
    "pwrite64": 68,
    "readv": 65,
    "writev": 66,
    "access": 48,
    "pipe": 59,
    "select": 23,
    "sched_yield": 124,
    "mremap": 216,
    "msync": 227,
    "madvise": 233,
    "dup": 23,
    "dup2": 1000,  # Not directly available on aarch64
    "nanosleep": 101,
    "getpid": 172,
    "clone": 220,
    "fork": 1001,  # Not directly available, use clone
    "vfork": 1002,  # Not directly available, use clone
    "execve": 221,
    "exit": 93,
    "wait4": 260,
    "kill": 129,
    "uname": 160,
    "fcntl": 25,
    "flock": 32,
    "fsync": 82,
    "fdatasync": 83,
    "ftruncate": 46,
    "getdents": 1003,  # Not directly available, use getdents64
    "getcwd": 17,
    "chdir": 49,
    "mkdir": 34,
    "rmdir": 35,
    "creat": 1004,  # Not directly available, use openat
    "unlink": 35,
    "readlink": 78,
    "chmod": 52,
    "fchmod": 53,
    "chown": 54,
    "fchown": 55,
    "lchown": 1005,  # Not directly available
    "umask": 166,
    "getuid": 174,
    "getgid": 176,
    "geteuid": 175,
    "getegid": 177,
    "setpgid": 154,
    "getppid": 173,
    "setsid": 157,
    "setuid": 146,
    "setgid": 144,
    "getgroups": 158,
    "setgroups": 159,
    "sigaltstack": 132,
    "arch_prctl": 1006,  # Not available on aarch64
    "futex": 98,
    "set_tid_address": 96,
    "clock_gettime": 113,
    "exit_group": 94,
    "epoll_wait": 1007,  # Use epoll_pwait
    "epoll_ctl": 21,
    "tgkill": 131,
    "openat": 56,
    "mkdirat": 34,
    "unlinkat": 35,
    "renameat": 264,
    "readlinkat": 78,
    "faccessat": 48,
    "dup3": 24,
    "epoll_create1": 20,
    "pipe2": 59,
    "clock_gettime64": 113,
    "newfstatat": 79,
    "set_robust_list": 99,
    "getrandom": 278,
    "prlimit64": 261,
    "statfs": 44,
    "getrlimit": 163,
    "getdents64": 61,
    "close_range": 436,
    "rseq": 293,
    # Dangerous syscalls (usually blocked)
    "reboot": 142,
    "mount": 40,
    "umount2": 39,
    "pivot_root": 41,
    "swapon": 225,
    "swapoff": 224,
    "kexec_load": 104,
    "ptrace": 117,
    "process_vm_readv": 270,
    "process_vm_writev": 271,
}

# Get the current architecture's syscall table
def _get_syscall_table():
    """Get the syscall table for the current architecture"""
    machine = platform.machine()
    if machine in ("x86_64", "amd64"):
        return SYSCALL_TABLE_X86_64
    elif machine in ("aarch64", "arm64"):
        return SYSCALL_TABLE_AARCH64
    else:
        # Default to x86_64
        return SYSCALL_TABLE_X86_64

# Current architecture's syscall table
SYSCALL_TABLE = _get_syscall_table()

# 反向映射
SYSCALL_NAMES: Dict[int, str] = {v: k for k, v in SYSCALL_TABLE.items()}

# 默认安全系统调用白名单
DEFAULT_WHITELIST = [
    "read", "write", "close", "stat", "fstat", "lstat",
    "poll", "lseek", "mmap", "mprotect", "munmap", "brk",
    "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
    "ioctl", "access", "pipe", "select", "sched_yield",
    "dup", "dup2", "nanosleep", "getpid", "getuid", "getgid",
    "geteuid", "getegid", "getppid", "fcntl", "flock",
    "fsync", "fdatasync", "getdents", "getcwd", "chdir",
    "readlink", "umask", "sigaltstack", "arch_prctl",
    "futex", "set_tid_address", "clock_gettime", "exit_group",
    "epoll_wait", "epoll_ctl", "openat", "faccessat",
    "dup3", "epoll_create1", "pipe2", "exit",
    # Additional syscalls needed for basic programs
    "open", "newfstatat", "set_robust_list", "getrandom",
    "rseq", "prlimit64", "statfs", "getrlimit",
    "readlinkat", "getdents64", "close_range",
    # execve is needed to run programs
    "execve",
    # Additional syscalls for Python and other interpreters
    "gettid", "tgkill", "kill", "wait4", "waitid",
    "madvise", "mremap", "msync", "mincore",
    "statx", "faccessat2", "openat2",
    "socket", "connect", "bind", "listen", "accept",
    "sendto", "recvfrom", "sendmsg", "recvmsg",
    "shutdown", "setsockopt", "getsockopt",
    "getsockname", "getpeername",
    "epoll_create", "epoll_wait_old", "epoll_ctl_old",
    "eventfd", "eventfd2",
    "signalfd", "signalfd4",
    "timerfd_create", "timerfd_settime", "timerfd_gettime",
    "inotify_init", "inotify_init1", "inotify_add_watch", "inotify_rm_watch",
    "mkdir", "mkdirat", "rmdir", "unlink", "unlinkat",
    "rename", "renameat", "renameat2",
    "link", "linkat", "symlink", "symlinkat",
    "readlink", "readlinkat",
    "chmod", "fchmod", "fchmodat",
    "chown", "fchown", "lchown", "fchownat", "lchownat",
    "utime", "utimes", "futimesat", "utimensat",
    "getcwd", "chdir", "fchdir",
    "pivot_root",  # Usually blocked but needed for some programs
    "mount", "umount2",  # Usually blocked
    "swapon", "swapoff",  # Usually blocked
    "reboot",  # Usually blocked
    "kexec_load",  # Usually blocked
    "ptrace",  # Usually blocked
    "process_vm_readv", "process_vm_writev",  # Usually blocked
]

# 默认危险系统调用黑名单
DEFAULT_BLACKLIST = [
    "fork", "vfork", "clone", "execve",
    "kill", "tgkill",
    "mount", "umount2", "pivot_root",
    "reboot", "kexec_load",
    "swapon", "swapoff",
    "setuid", "setgid", "setgroups",
    "ptrace", "process_vm_readv", "process_vm_writev",
]


class BPFInstruction:
    """BPF 指令"""
    def __init__(self, code: int, jt: int = 0, jf: int = 0, k: int = 0):
        self.code = code
        self.jt = jt
        self.jf = jf
        self.k = k

    def to_bytes(self) -> bytes:
        """转换为 BPF 指令格式 (2 bytes code, 1 jt, 1 jf, 4 k)"""
        return struct.pack("HBBI", self.code, self.jt, self.jf, self.k)


class SyscallFilter:
    """
    系统调用过滤器

    使用 seccomp BPF 过滤系统调用，支持白名单和黑名单模式。
    """

    def __init__(self):
        self._rules: List[Dict] = []
        self._mode: FilterMode = FilterMode.WHITELIST

    def set_mode(self, mode: FilterMode):
        """设置过滤模式"""
        self._mode = mode

    def add_allowed(self, syscall: str):
        """添加允许的系统调用"""
        if syscall in SYSCALL_TABLE:
            self._rules.append({
                "syscall": syscall,
                "nr": SYSCALL_TABLE[syscall],
                "allow": True,
            })

    def add_blocked(self, syscall: str):
        """添加阻止的系统调用"""
        if syscall in SYSCALL_TABLE:
            self._rules.append({
                "syscall": syscall,
                "nr": SYSCALL_TABLE[syscall],
                "allow": False,
            })

    def add_allowed_list(self, syscalls: List[str]):
        """批量添加允许的系统调用"""
        for sc in syscalls:
            self.add_allowed(sc)

    def add_blocked_list(self, syscalls: List[str]):
        """批量添加阻止的系统调用"""
        for sc in syscalls:
            self.add_blocked(sc)

    def build_bpf_program(self) -> List[BPFInstruction]:
        """
        构建 BPF 程序

        Returns:
            BPF 指令列表
        """
        instructions: List[BPFInstruction] = []

        # 验证架构
        arch = _get_audit_arch()
        arch_offset = _get_seccomp_data_arch_offset()
        nr_offset = _get_seccomp_data_nr_offset()

        # 验证架构
        instructions.append(BPFInstruction(
            BPF_LD | BPF_W | BPF_ABS, 0, 0, arch_offset
        ))
        instructions.append(BPFInstruction(
            BPF_JMP | BPF_JEQ | BPF_K, 1, 0, arch
        ))
        instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_KILL))

        # 加载系统调用号
        instructions.append(BPFInstruction(
            BPF_LD | BPF_W | BPF_ABS, 0, 0, nr_offset
        ))

        # 规则
        if self._mode == FilterMode.WHITELIST:
            # 白名单模式：匹配的允许，不匹配的杀死
            allow_rules = [r for r in self._rules if r["allow"]]
            block_rules = [r for r in self._rules if not r["allow"]]

            # 先检查黑名单（如果有的话）
            for rule in block_rules:
                instructions.append(BPFInstruction(
                    BPF_JMP | BPF_JEQ | BPF_K, 0, 1, rule["nr"]
                ))
                instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_KILL))

            # 白名单跳转
            # ALLOW is at the end of the program
            # Current position is after header (4) + block rules
            # We need to calculate the offset to jump to ALLOW
            num_allow = len(allow_rules)
            num_block = len(block_rules)

            for i, rule in enumerate(allow_rules):
                # Offset to ALLOW = num_allow - i + 1
                # This jumps over the remaining allow rules and the KILL instruction
                jump_offset = num_allow - i + 1
                instructions.append(BPFInstruction(
                    BPF_JMP | BPF_JEQ | BPF_K, jump_offset, 0, rule["nr"]
                ))

            # 默认：杀死
            instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_KILL))
            # 允许
            instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_ALLOW))

        else:
            # 黑名单模式：匹配的杀死，不匹配的允许
            block_rules = [r for r in self._rules if not r["allow"]]
            allow_rules = [r for r in self._rules if r["allow"]]

            # 先检查白名单（如果有的话）
            for rule in allow_rules:
                instructions.append(BPFInstruction(
                    BPF_JMP | BPF_JEQ | BPF_K, 1, 0, rule["nr"]
                ))
                instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_ALLOW))

            # 黑名单跳转
            jump_offset = len(block_rules)
            for rule in block_rules:
                instructions.append(BPFInstruction(
                    BPF_JMP | BPF_JEQ | BPF_K, jump_offset, 0, rule["nr"]
                ))
                jump_offset -= 1

            # 默认：允许
            instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_ALLOW))
            # 杀死
            instructions.append(BPFInstruction(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_KILL))

        return instructions

    def apply(self,
              mode: Optional[FilterMode] = None,
              allowed: Optional[List[str]] = None,
              blocked: Optional[List[str]] = None):
        """
        应用 seccomp 过滤器

        Args:
            mode: 过滤模式
            allowed: 允许的系统调用列表
            blocked: 阻止的系统调用列表
        """
        if mode:
            self._mode = mode

        if allowed:
            self.add_allowed_list(allowed)
        elif not self._rules and self._mode == FilterMode.WHITELIST:
            self.add_allowed_list(DEFAULT_WHITELIST)

        if blocked:
            self.add_blocked_list(blocked)
        elif not self._rules and self._mode == FilterMode.BLACKLIST:
            self.add_blocked_list(DEFAULT_BLACKLIST)

        # 构建 BPF 程序
        bpf_instructions = self.build_bpf_program()

        # 转换为字节
        bpf_bytes = b""
        for instr in bpf_instructions:
            bpf_bytes += instr.to_bytes()

        # 使用 prctl 安装 seccomp 过滤器
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

        # 设置 NO_NEW_PRIVS
        ret = libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
        if ret != 0:
            raise OSError(f"prctl(NO_NEW_PRIVS) failed: {ctypes.get_errno()}")

        # 构建 sock_fprog
        class sock_fprog(ctypes.Structure):
            _fields_ = [
                ("len", ctypes.c_ushort),
                ("filter", ctypes.c_char_p),
            ]

        fprog = sock_fprog()
        fprog.len = len(bpf_instructions)
        fprog.filter = bpf_bytes

        # Keep a reference to bpf_bytes to prevent garbage collection
        self._bpf_bytes = bpf_bytes

        # 安装过滤器
        ret = libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(fprog), 0, 0)
        if ret != 0:
            raise OSError(f"prctl(SECCOMP) failed: {ctypes.get_errno()}")

    @staticmethod
    def get_syscall_number(name: str) -> Optional[int]:
        """获取系统调用号"""
        return SYSCALL_TABLE.get(name)

    @staticmethod
    def get_syscall_name(nr: int) -> str:
        """获取系统调用名称"""
        return SYSCALL_NAMES.get(nr, f"unknown({nr})")

    @staticmethod
    def get_default_whitelist() -> List[str]:
        """获取默认白名单"""
        return DEFAULT_WHITELIST.copy()

    @staticmethod
    def get_default_blacklist() -> List[str]:
        """获取默认黑名单"""
        return DEFAULT_BLACKLIST.copy()
