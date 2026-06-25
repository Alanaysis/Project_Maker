from setuptools import setup, find_packages

setup(
    name="gesture-recognition",
    version="1.0.0",
    description="Hand gesture recognition system with keypoint detection and gesture classification",
    author="Learning Project Factory",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "torch>=1.12.0",
        "torchvision>=0.13.0",
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "Pillow>=9.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
