"""
Industrial Vision Detection - 安装配置

用于安装项目为 Python 包。

使用方法:
    # 开发模式安装
    pip install -e .

    # 普通安装
    pip install .
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# 读取依赖
requirements = []
with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # 处理带注释的行
            if '#' in line:
                line = line[:line.index('#')].strip()
            requirements.append(line)

setup(
    name='industrial-vision-detection',
    version='0.1.0',
    author='Industrial Vision Detection Team',
    description='工业视觉检测神经网络 - 学习项目',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/industrial-vision-detection',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Image Recognition',
    ],
    keywords='computer vision, object detection, yolo, industrial inspection',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/industrial-vision-detection/issues',
        'Source': 'https://github.com/yourusername/industrial-vision-detection',
    },
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
        ],
        'deploy': [
            'onnx>=1.14.0',
            'onnxruntime>=1.15.0',
        ],
    },
)
