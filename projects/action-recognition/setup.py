from setuptools import setup, find_packages

setup(
    name="action-recognition",
    version="1.0.0",
    description="Video-based action recognition using deep learning",
    author="AI Learning Project",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "torch>=1.12.0",
        "torchvision>=0.13.0",
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "matplotlib>=3.5.0",
            "scikit-learn>=1.0.0",
        ],
    },
)
