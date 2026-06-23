"""Setup script for Actor-Critic package."""

from setuptools import setup, find_packages

setup(
    name="actor-critic",
    version="1.0.0",
    description="Actor-Critic reinforcement learning algorithm implementation",
    author="AI Learning Project",
    python_requires=">=3.8",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "torch>=2.0.0",
        "numpy>=1.24.0",
        "gymnasium>=0.29.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pyyaml>=6.0",
        ],
    },
)
