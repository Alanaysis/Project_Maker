from setuptools import setup, find_packages

setup(
    name="erc20-token",
    version="1.0.0",
    description="ERC20 Token Implementation in Python",
    author="AI Assistant",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
)
