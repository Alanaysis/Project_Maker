"""
sandbox.filesystem - 文件系统隔离模块

实现 chroot 环境、只读挂载和临时文件系统。
"""

import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict


class FilesystemIsolation:
    """
    文件系统隔离管理器

    提供 chroot 环境创建、只读挂载和临时文件系统功能。
    """

    def __init__(self):
        self._chroot_dir: Optional[str] = None
        self._mounts: List[str] = []

    def create_chroot_environment(self, base_dir: Optional[str] = None) -> str:
        """
        创建 chroot 环境

        Args:
            base_dir: 基础目录，如果为 None 则使用临时目录

        Returns:
            chroot 目录路径
        """
        if base_dir:
            chroot_dir = base_dir
            os.makedirs(chroot_dir, exist_ok=True)
        else:
            chroot_dir = tempfile.mkdtemp(prefix="sandbox_chroot_")

        self._chroot_dir = chroot_dir

        # 创建基本目录结构
        dirs = [
            "bin", "sbin", "lib", "lib64", "usr", "etc",
            "tmp", "var", "proc", "sys", "dev", "opt",
            "home", "root", "mnt", "media",
        ]
        for d in dirs:
            os.makedirs(os.path.join(chroot_dir, d), exist_ok=True)

        # 复制必要的二进制文件和库
        self._copy_essential_files(chroot_dir)

        return chroot_dir

    def _copy_essential_files(self, chroot_dir: str):
        """复制必要的二进制文件和库到 chroot 环境"""
        # 基本命令
        essential_bins = [
            "/bin/sh", "/bin/bash", "/bin/ls", "/bin/cat",
            "/bin/echo", "/bin/mkdir", "/bin/rm", "/bin/cp",
            "/bin/mv", "/bin/ln", "/bin/chmod", "/bin/chown",
            "/usr/bin/env", "/usr/bin/whoami", "/usr/bin/id",
        ]

        for bin_path in essential_bins:
            if os.path.exists(bin_path):
                self._copy_with_deps(bin_path, chroot_dir)

    def _copy_with_deps(self, src: str, chroot_dir: str):
        """复制文件及其依赖库"""
        # 复制文件本身
        dst = os.path.join(chroot_dir, src.lstrip("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        try:
            shutil.copy2(src, dst)
            os.chmod(dst, 0o755)
        except (IOError, OSError):
            pass

        # 获取并复制依赖库
        try:
            result = subprocess.run(
                ["ldd", src],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if "=>" in line:
                    lib_path = line.split("=>")[1].strip().split()[0]
                    if os.path.exists(lib_path):
                        lib_dst = os.path.join(chroot_dir, lib_path.lstrip("/"))
                        os.makedirs(os.path.dirname(lib_dst), exist_ok=True)
                        try:
                            shutil.copy2(lib_path, lib_dst)
                        except (IOError, OSError):
                            pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    def setup_chroot_mounts(self,
                            chroot_dir: str,
                            read_only: Optional[List[str]] = None,
                            tmpfs: Optional[List[str]] = None,
                            bind: Optional[Dict[str, str]] = None):
        """
        设置 chroot 挂载点

        Args:
            chroot_dir: chroot 目录
            read_only: 只读挂载的路径列表
            tmpfs: tmpfs 挂载的路径列表
            bind: bind 挂载映射 {源路径: 目标路径}
        """
        read_only = read_only or []
        tmpfs = tmpfs or []
        bind = bind or {}

        # 只读挂载
        for path in read_only:
            target = os.path.join(chroot_dir, path.lstrip("/"))
            if os.path.exists(path) and os.path.exists(target):
                try:
                    subprocess.run(
                        ["mount", "--bind", path, target],
                        check=True,
                        capture_output=True,
                        timeout=5,
                    )
                    subprocess.run(
                        ["mount", "-o", "remount,ro", target],
                        check=True,
                        capture_output=True,
                        timeout=5,
                    )
                    self._mounts.append(target)
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    pass

        # tmpfs 挂载
        for path in tmpfs:
            target = os.path.join(chroot_dir, path.lstrip("/"))
            os.makedirs(target, exist_ok=True)
            try:
                subprocess.run(
                    ["mount", "-t", "tmpfs", "-o", "size=64m", "tmpfs", target],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                self._mounts.append(target)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        # bind 挂载
        for src, dst in bind.items():
            target = os.path.join(chroot_dir, dst.lstrip("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            try:
                subprocess.run(
                    ["mount", "--bind", src, target],
                    check=True,
                    capture_output=True,
                    timeout=5,
                )
                self._mounts.append(target)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

    def cleanup_chroot(self, chroot_dir: Optional[str] = None):
        """
        清理 chroot 环境

        Args:
            chroot_dir: chroot 目录，如果为 None 则使用上次创建的目录
        """
        target_dir = chroot_dir or self._chroot_dir
        if not target_dir:
            return

        # 卸载所有挂载点
        for mount_point in reversed(self._mounts):
            try:
                subprocess.run(
                    ["umount", "-l", mount_point],
                    capture_output=True,
                    timeout=10,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        self._mounts.clear()

        # 删除 chroot 目录
        if target_dir and os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except (IOError, OSError):
                pass

        if target_dir == self._chroot_dir:
            self._chroot_dir = None

    def setup_readonly_rootfs(self, chroot_dir: str):
        """
        设置只读根文件系统

        Args:
            chroot_dir: chroot 目录
        """
        # 将根文件系统挂载为只读
        try:
            subprocess.run(
                ["mount", "-o", "remount,ro", chroot_dir],
                capture_output=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass

    def create_overlay_filesystem(self,
                                  lower_dir: str,
                                  work_dir: Optional[str] = None,
                                  upper_dir: Optional[str] = None) -> str:
        """
        创建 overlay 文件系统

        Args:
            lower_dir: 底层只读目录
            work_dir: 工作目录
            upper_dir: 上层可写目录

        Returns:
            合并后的挂载点路径
        """
        if work_dir is None:
            work_dir = tempfile.mkdtemp(prefix="sandbox_overlay_work_")
        if upper_dir is None:
            upper_dir = tempfile.mkdtemp(prefix="sandbox_overlay_upper_")

        merged_dir = tempfile.mkdtemp(prefix="sandbox_overlay_merged_")

        try:
            subprocess.run(
                [
                    "mount", "-t", "overlay", "overlay",
                    "-o", f"lowerdir={lower_dir},upperdir={upper_dir},workdir={work_dir}",
                    merged_dir,
                ],
                check=True,
                capture_output=True,
                timeout=5,
            )
            self._mounts.append(merged_dir)
            return merged_dir
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to create overlay filesystem: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_chroot()
        return False
