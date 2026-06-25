from setuptools import setup, find_packages

setup(
    name='gradient-descent',
    version='0.1.0',
    description='Implementation of various gradient descent optimization algorithms',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your-email@example.com',
    url='https://github.com/your-username/gradient-descent',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20.0',
        'matplotlib>=3.3.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.12.0',
            'flake8>=3.9.0',
            'black>=21.0.0',
            'isort>=5.9.0',
            'mypy>=0.900',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    keywords='optimization gradient-descent machine-learning adam sgd',
)
