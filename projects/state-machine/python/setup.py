"""
Setup script for the State Machine Framework.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="state-machine-framework",
    version="1.0.0",
    author="State Machine Team",
    author_email="team@statemachine.dev",
    description="A comprehensive state machine library for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/statemachine/state-machine-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "coverage>=7.0.0",
            "flake8>=6.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={},
    project_urls={
        "Bug Reports": "https://github.com/statemachine/state-machine-python/issues",
        "Source": "https://github.com/statemachine/state-machine-python",
    },
)
