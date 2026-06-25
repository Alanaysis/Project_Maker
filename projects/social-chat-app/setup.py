"""
Setup script for social-chat-app
"""

from setuptools import setup, find_packages

setup(
    name="social-chat-app",
    version="1.0.0",
    description="A real-time social chat application built with Python and WebSocket",
    author="AI Assistant",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "websockets>=12.0",
        "aiohttp>=3.9.0",
        "sqlalchemy>=2.0.0",
        "aiosqlite>=0.19.0",
        "bcrypt>=4.1.0",
        "PyJWT>=2.8.0",
        "aiofiles>=23.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "httpx>=0.25.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chat-server=src.main:main",
        ],
    },
)
