from setuptools import setup, find_packages

setup(
    name="edge-quant",
    version="0.1.0",
    author="Edge Quant Team",
    author_email="edge-quant@example.com",
    description="端侧极致量化模型框架",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/edge-quant/edge-quant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "torch": ["torch>=2.0.0"],
        "onnx": ["onnx>=1.14.0", "onnxruntime>=1.15.0"],
        "all": [
            "torch>=2.0.0",
            "onnx>=1.14.0",
            "onnxruntime>=1.15.0",
            "matplotlib>=3.5.0",
            "tqdm>=4.62.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "edge-quant=src.cli:main",
        ],
    },
)
