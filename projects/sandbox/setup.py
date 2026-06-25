"""
sandbox - 沙箱隔离模块

一个完整的进程沙箱实现，支持 seccomp BPF 系统调用过滤、Linux namespace 隔离、
chroot 文件系统隔离和资源限制。
"""

from setuptools import setup, find_packages

setup(
    name="sandbox-isolation",
    version="1.0.0",
    description="进程沙箱隔离模块 - seccomp, namespace, chroot, 资源限制",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Sandbox Project",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Operating System",
    ],
    keywords="sandbox isolation seccomp namespace chroot security",
    entry_points={
        "console_scripts": [
            "sandbox-exec=examples.code_execution_sandbox:main",
            "sandbox-analyze=examples.malware_analysis:main",
        ],
    },
)
