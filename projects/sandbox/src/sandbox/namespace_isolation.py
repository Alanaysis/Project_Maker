"""
sandbox.namespace_isolation - Namespace 隔离模块

使用 Linux namespace 实现进程隔离。
"""

import os
import ctypes
import ctypes.util
import subprocess
from typing import List, Optional, Callable

# Linux namespace 常量
CLONE_NEWNS = 0x00020000      # Mount namespace
CLONE_NEWUTS = 0x04000000     # UTS namespace
CLONE_NEWIPC = 0x08000000     # IPC namespace
CLONE_NEWUSER = 0x10000000    # User namespace
CLONE_NEWPID = 0x20000000     # PID namespace
CLONE_NEWNET = 0x40000000     # Network namespace
CLONE_NEWCGROUP = 0x02000000  # Cgroup namespace

# unshare 系统调用号
SYS_UNSHARE = 272  # x86_64


class NamespaceIsolation:
    """
    Namespace 隔离管理器

    使用 Linux namespace 实现进程、网络、挂载等资源的隔离。
    """

    def __init__(self):
        self._libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

    def unshare(self, flags: int):
        """
        调用 unshare 系统调用

        Args:
            flags: namespace 标志位
        """
        ret = self._libc.unshare(flags)
        if ret != 0:
            errno = ctypes.get_errno()
            raise OSError(f"unshare failed: {os.strerror(errno)}")

    def create_pid_namespace(self):
        """创建 PID namespace"""
        self.unshare(CLONE_NEWPID)

    def create_mount_namespace(self):
        """创建 mount namespace"""
        self.unshare(CLONE_NEWNS)

    def create_net_namespace(self):
        """创建 network namespace"""
        self.unshare(CLONE_NEWNET)

    def create_uts_namespace(self):
        """创建 UTS namespace（主机名隔离）"""
        self.unshare(CLONE_NEWUTS)

    def create_ipc_namespace(self):
        """创建 IPC namespace（进程间通信隔离）"""
        self.unshare(CLONE_NEWIPC)

    def create_cgroup_namespace(self):
        """创建 cgroup namespace"""
        self.unshare(CLONE_NEWCGROUP)

    def create_user_namespace(self):
        """创建 user namespace"""
        self.unshare(CLONE_NEWUSER)

    def set_hostname(self, hostname: str):
        """
        设置主机名（需要 UTS namespace）

        Args:
            hostname: 新主机名
        """
        libc = self._libc
        ret = libc.sethostname(hostname.encode(), len(hostname))
        if ret != 0:
            raise OSError(f"sethostname failed: {ctypes.get_errno()}")

    def setup_loopback(self):
        """配置 loopback 网络接口（需要 network namespace）"""
        try:
            subprocess.run(
                ["ip", "link", "set", "lo", "up"],
                check=True,
                capture_output=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

    def create_namespaces(self,
                          pid_ns: bool = True,
                          net_ns: bool = True,
                          mount_ns: bool = True,
                          uts_ns: bool = True,
                          ipc_ns: bool = True,
                          cgroup_ns: bool = False,
                          user_ns: bool = False):
        """
        创建多个 namespace

        Args:
            pid_ns: 是否创建 PID namespace
            net_ns: 是否创建 network namespace
            mount_ns: 是否创建 mount namespace
            uts_ns: 是否创建 UTS namespace
            ipc_ns: 是否创建 IPC namespace
            cgroup_ns: 是否创建 cgroup namespace
            user_ns: 是否创建 user namespace
        """
        flags = 0
        if mount_ns:
            flags |= CLONE_NEWNS
        if uts_ns:
            flags |= CLONE_NEWUTS
        if ipc_ns:
            flags |= CLONE_NEWIPC
        if pid_ns:
            flags |= CLONE_NEWPID
        if net_ns:
            flags |= CLONE_NEWNET
        if cgroup_ns:
            flags |= CLONE_NEWCGROUP
        if user_ns:
            flags |= CLONE_NEWUSER

        if flags:
            self.unshare(flags)

    def create_isolated_process(self,
                                cmd: List[str],
                                pid_ns: bool = True,
                                net_ns: bool = True,
                                mount_ns: bool = True,
                                uts_ns: bool = True,
                                ipc_ns: bool = True,
                                chroot_dir: Optional[str] = None,
                                preexec_fn: Optional[Callable] = None,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE) -> subprocess.Popen:
        """
        创建隔离的子进程

        Args:
            cmd: 要执行的命令
            pid_ns: 是否使用 PID namespace
            net_ns: 是否使用 network namespace
            mount_ns: 是否使用 mount namespace
            uts_ns: 是否使用 UTS namespace
            ipc_ns: 是否使用 IPC namespace
            chroot_dir: chroot 目录
            preexec_fn: 子进程预执行函数
            stdout: 标准输出
            stderr: 标准错误

        Returns:
            Popen 对象
        """
        def child_setup():
            # 创建 namespace（需要 root 权限）
            try:
                self.create_namespaces(
                    pid_ns=pid_ns,
                    net_ns=net_ns,
                    mount_ns=mount_ns,
                    uts_ns=uts_ns,
                    ipc_ns=ipc_ns,
                )
            except (OSError, PermissionError):
                # namespace 创建失败，继续执行但没有隔离
                pass

            # 设置主机名
            if uts_ns:
                try:
                    self.set_hostname("sandbox")
                except OSError:
                    pass

            # 配置网络
            if net_ns:
                self.setup_loopback()

            # chroot（需要 root 权限）
            if chroot_dir:
                try:
                    os.chroot(chroot_dir)
                    os.chdir("/")
                except (OSError, PermissionError):
                    pass

            # 用户自定义的预执行函数
            if preexec_fn:
                try:
                    preexec_fn()
                except (OSError, PermissionError):
                    pass

        env = os.environ.copy()
        env["SANDBOX_NAMESPACE"] = "1"

        proc = subprocess.Popen(
            cmd,
            stdout=stdout,
            stderr=stderr,
            env=env,
            preexec_fn=child_setup,
        )

        return proc

    @staticmethod
    def get_namespace_info(pid: int) -> dict:
        """
        获取进程的 namespace 信息

        Args:
            pid: 进程 ID

        Returns:
            namespace 信息字典
        """
        ns_path = f"/proc/{pid}/ns"
        info = {}

        if os.path.exists(ns_path):
            for ns_name in os.listdir(ns_path):
                ns_link = os.path.join(ns_path, ns_name)
                try:
                    target = os.readlink(ns_link)
                    info[ns_name] = target
                except OSError:
                    pass

        return info

    @staticmethod
    def enter_namespace(pid: int, ns_type: str):
        """
        进入指定进程的 namespace

        Args:
            pid: 进程 ID
            ns_type: namespace 类型（如 "pid", "net", "mnt"）
        """
        ns_path = f"/proc/{pid}/ns/{ns_type}"
        if not os.path.exists(ns_path):
            raise FileNotFoundError(f"Namespace not found: {ns_path}")

        # 使用 setns 进入 namespace
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)

        fd = os.open(ns_path, os.O_RDONLY)
        try:
            ret = libc.setns(fd, 0)
            if ret != 0:
                raise OSError(f"setns failed: {os.strerror(ctypes.get_errno())}")
        finally:
            os.close(fd)
