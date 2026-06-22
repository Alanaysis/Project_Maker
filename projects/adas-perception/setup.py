"""
自动驾驶感知系统安装脚本
"""

from setuptools import setup, find_packages

setup(
    name='adas-perception',
    version='0.1.0',
    author='ADAS Perception Team',
    author_email='adas@example.com',
    description='自动驾驶感知系统，支持目标检测、车道线检测、点云处理',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/adas-perception/adas-perception',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.8',
    install_requires=[
        'torch>=2.0.0',
        'torchvision>=0.15.0',
        'numpy>=1.24.0',
        'scipy>=1.10.0',
        'open3d>=0.17.0',
        'opencv-python>=4.8.0',
        'Pillow>=10.0.0',
        'pandas>=2.0.0',
        'scikit-learn>=1.3.0',
        'matplotlib>=3.7.0',
        'pyyaml>=6.0',
        'tqdm>=4.65.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'adas-perception=src.main:main',
        ],
    },
)
