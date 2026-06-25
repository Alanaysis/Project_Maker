"""
去中心化投票系统安装脚本
"""

from setuptools import setup, find_packages

setup(
    name="decentralized-voting",
    version="1.0.0",
    description="基于区块链的去中心化投票系统",
    author="Decentralized Voting Team",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
