from setuptools import setup, find_packages

setup(
    name="basic-circuit",
    version="1.0.0",
    description="基本电路模拟 - 电阻、电容、电感、电压源、电流源的电路分析",
    author="AI Analysis",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "scipy>=1.7.0",
    ],
    python_requires=">=3.8",
)
