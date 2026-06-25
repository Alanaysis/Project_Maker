from setuptools import setup, find_packages

setup(
    name="linear-programming",
    version="1.0.0",
    description="线性规划库 - 单纯形法、对偶理论、敏感性分析",
    author="AIanaysis",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
)
