from setuptools import setup, find_packages

setup(
    name="factor-mining",
    version="1.0.0",
    description="量化因子挖掘框架",
    author="AI Analysis",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.3.0",
    ],
    extras_require={
        "viz": ["matplotlib>=3.7.0", "seaborn>=0.12.0"],
        "stats": ["statsmodels>=0.14.0"],
        "storage": ["pyarrow>=12.0.0"],
        "dev": ["pytest", "flake8", "mypy"],
    },
    python_requires=">=3.8",
)
