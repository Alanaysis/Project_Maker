"""视频理解项目安装配置"""

from setuptools import setup, find_packages

setup(
    name="video-understanding",
    version="0.1.0",
    description="视频内容理解与摘要系统",
    author="AIanaysis",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "torch>=1.12.0",
        "torchvision>=0.13.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
)
