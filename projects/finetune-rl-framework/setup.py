"""
Finetune-RL Framework 安装配置
"""

from setuptools import setup, find_packages

setup(
    name="finetune-rl-framework",
    version="0.1.0",
    description="一个支持 LoRA 微调和 PPO 强化学习的大模型后训练框架",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Learning Project",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.21.0",
        "datasets>=2.14.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "test": ["pytest>=7.0.0"],
        "dev": [
            "pytest>=7.0.0",
            "black",
            "isort",
            "flake8",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
