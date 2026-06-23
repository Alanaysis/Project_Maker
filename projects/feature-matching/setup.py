"""
特征匹配 SIFT/ORB 包配置
"""

from setuptools import setup, find_packages

setup(
    name='feature-matching',
    version='1.0.0',
    description='图像特征点检测和匹配 - SIFT/ORB实现',
    author='AIanaysis',
    author_email='ai@example.com',
    packages=find_packages(),
    install_requires=[
        'opencv-python>=4.5.0',
        'opencv-contrib-python>=4.5.0',
        'numpy>=1.20.0',
        'matplotlib>=3.5.0',
    ],
    extras_require={
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='computer-vision feature-matching sift orb opencv',
)
