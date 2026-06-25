# 开发指南文档

## 1. 开发环境搭建

### 1.1 系统要求

| 要求 | 版本 | 说明 |
|------|------|------|
| Python | 3.9+ | 主要编程语言 |
| pip | 最新版 | 包管理工具 |
| Git | 任意 | 版本控制 |
| IDE | 任意 | 推荐VS Code |

### 1.2 环境配置

#### 安装Python

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip

# macOS
brew install python@3.9

# Windows
# 从官网下载安装包：https://www.python.org/downloads/
```

#### 创建虚拟环境

```bash
# 进入项目目录
cd projects/social-chat-app

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 安装依赖

```bash
# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

### 1.3 IDE配置

#### VS Code配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": [
        "--line-length",
        "88"
    ],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: 启动服务器",
            "type": "python",
            "request": "launch",
            "module": "src.main",
            "console": "integratedTerminal",
            "env": {
                "HOST": "0.0.0.0",
                "PORT": "8765"
            }
        }
    ]
}
```

## 2. 项目结构详解

### 2.1 目录结构

```
social-chat-app/
├── src/                    # 源代码目录
│   ├── __init__.py        # 包初始化
│   ├── main.py            # 主程序入口
│   ├── server/            # 服务器模块
│   │   ├── __init__.py
│   │   ├── websocket_server.py  # WebSocket服务器
│   │   └── connection_manager.py # 连接管理器
│   ├── client/            # 客户端模块
│   │   ├── __init__.py
│   │   └── chat_client.py # 聊天客户端
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py    # 数据库模型
│   │   └── db_manager.py  # 数据库管理器
│   └── utils/             # 工具模块
│       ├── __init__.py
│       ├── auth.py        # 认证服务
│       └── validators.py  # 数据验证
├── static/                # 静态资源
│   ├── index.html         # 主页面
│   ├── css/
│   │   └── style.css      # 样式文件
│   └── js/
│       └── app.js         # 前端JavaScript
├── tests/                 # 测试文件
│   ├── __init__.py
│   ├── test_auth.py       # 认证测试
│   └── test_validators.py # 验证器测试
├── examples/              # 示例代码
│   ├── client_example.py  # 客户端示例
│   └── api_example.py     # API示例
├── docs/                  # 文档
│   ├── 01_RESEARCH.md     # 技术调研
│   ├── 02_REQUIREMENTS.md # 需求分析
│   ├── 03_DESIGN.md       # 系统设计
│   ├── 04_PRODUCT.md      # 产品设计
│   └── 05_DEVELOPMENT.md  # 开发指南
├── requirements.txt       # 依赖列表
├── .gitignore             # Git忽略文件
└── README.md              # 项目说明
```

### 2.2 模块职责

#### server模块

**websocket_server.py**
- WebSocket服务器核心
- HTTP API处理
- 消息路由和处理
- 客户端连接管理

**connection_manager.py**
- WebSocket连接管理
- 用户在线状态维护
- 消息分发
- 心跳检测

#### client模块

**chat_client.py**
- WebSocket客户端
- 事件处理
- 消息发送接收
- 命令行客户端

#### models模块

**database.py**
- SQLAlchemy模型定义
- 数据表结构
- 关系定义

**db_manager.py**
- 数据库操作封装
- CRUD操作
- 查询优化

#### utils模块

**auth.py**
- JWT令牌管理
- 密码加密验证
- 认证中间件

**validators.py**
- 输入数据验证
- 格式检查
- 错误提示

## 3. 核心模块开发

### 3.1 WebSocket服务器开发

#### 基础结构

```python
# src/server/websocket_server.py

import asyncio
import json
import logging
from aiohttp import web
import websockets

from ..models import DatabaseManager
from ..utils import AuthService
from .connection_manager import ConnectionManager

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765, db_path='social_chat.db'):
        self.host = host
        self.port = port
        self.db = DatabaseManager(db_path)
        self.auth = AuthService()
        self.connections = ConnectionManager()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """设置HTTP路由"""
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_post('/api/register', self.handle_register)
        self.app.router.add_post('/api/login', self.handle_login)
        self.app.router.add_static('/static/', path='static', name='static')

    async def start(self):
        """启动服务器"""
        await self.db.init_db()

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        # 保持运行
        await asyncio.Event().wait()
```

#### WebSocket处理

```python
async def handle_websocket(self, request):
    """处理WebSocket连接"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # 获取并验证令牌
    token = request.query.get('token')
    payload = self.auth.verify_token(token)

    if not payload:
        await ws.send_json({'type': 'error', 'message': '认证失败'})
        await ws.close()
        return ws

    user_id = payload['user_id']
    username = payload['username']

    # 注册连接
    await self.connections.connect(user_id, username, ws)

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._handle_message(user_id, data)
    finally:
        await self.connections.disconnect(user_id)

    return ws
```

### 3.2 连接管理器开发

```python
# src/server/connection_manager.py

import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ConnectionInfo:
    user_id: int
    username: str
    websocket: Any
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

class ConnectionManager:
    def __init__(self):
        self._connections: Dict[int, ConnectionInfo] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, username: str, websocket: Any):
        """添加连接"""
        async with self._lock:
            # 断开旧连接
            if user_id in self._connections:
                old_conn = self._connections[user_id]
                try:
                    await old_conn.websocket.close()
                except Exception:
                    pass

            self._connections[user_id] = ConnectionInfo(
                user_id=user_id,
                username=username,
                websocket=websocket
            )

    async def disconnect(self, user_id: int):
        """移除连接"""
        async with self._lock:
            if user_id in self._connections:
                del self._connections[user_id]

    async def send_to_user(self, user_id: int, message: dict) -> bool:
        """向用户发送消息"""
        conn = self._connections.get(user_id)
        if conn:
            try:
                await conn.websocket.send_json(message)
                return True
            except Exception:
                await self.disconnect(user_id)
                return False
        return False

    async def broadcast(self, message: dict, exclude_user_id: int = None):
        """广播消息"""
        for user_id in list(self._connections.keys()):
            if user_id != exclude_user_id:
                await self.send_to_user(user_id, message)
```

### 3.3 数据库模型开发

```python
# src/models/database.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Table, Text
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# 好友关系表
friendship_table = Table(
    'friendships',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('status', String(20), default='pending'),
    Column('created_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50), default='')
    avatar_url = Column(String(500), default='')
    bio = Column(String(500), default='')
    status = Column(String(20), default='offline')
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    sent_messages = relationship('Message', back_populates='sender', foreign_keys='Message.sender_id')
    friends = relationship(
        'User',
        secondary=friendship_table,
        primaryjoin=id == friendship_table.c.user_id,
        secondaryjoin=id == friendship_table.c.friend_id,
        backref='friend_of'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname or self.username,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

### 3.4 认证服务开发

```python
# src/utils/auth.py

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class AuthService:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'default-secret')
        self.algorithm = 'HS256'
        self.token_expire_hours = 24

    def hash_password(self, password: str) -> str:
        """加密密码"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def generate_token(self, user_id: int, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

## 4. 开发流程

### 4.1 Git工作流

```bash
# 克隆项目
git clone <repository-url>
cd projects/social-chat-app

# 创建功能分支
git checkout -b feature/new-feature

# 开发代码
# ...

# 提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建Pull Request
# ...

# 合并到主分支
git checkout master
git merge feature/new-feature
```

### 4.2 代码规范

#### Python代码规范

```python
# 使用类型注解
def get_user(user_id: int) -> Optional[User]:
    """获取用户信息"""
    pass

# 使用异步函数
async def send_message(content: str, receiver_id: int) -> Message:
    """发送消息"""
    pass

# 使用常量
MAX_MESSAGE_LENGTH = 5000
DEFAULT_PAGE_SIZE = 50
```

#### 命名规范

```python
# 类名：PascalCase
class UserService:
    pass

# 函数名：snake_case
def get_user_by_id(user_id: int):
    pass

# 常量：UPPER_SNAKE_CASE
MAX_CONNECTIONS = 1000

# 变量：snake_case
user_name = "testuser"
```

### 4.3 提交规范

```
<type>(<scope>): <subject>

类型：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例：
feat(chat): 添加群聊功能
fix(auth): 修复登录验证问题
docs(readme): 更新项目说明
```

## 5. 测试开发

### 5.1 单元测试

```python
# tests/test_auth.py

import pytest
from src.utils.auth import AuthService

class TestAuthService:
    def setup_method(self):
        self.auth = AuthService(secret_key='test-secret')

    def test_hash_password(self):
        password = 'test123'
        hashed = self.auth.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password(self):
        password = 'test123'
        hashed = self.auth.hash_password(password)
        assert self.auth.verify_password(password, hashed) is True
        assert self.auth.verify_password('wrong', hashed) is False

    def test_generate_token(self):
        token = self.auth.generate_token(1, 'testuser')
        assert token is not None
        assert len(token) > 0

    def test_verify_token(self):
        token = self.auth.generate_token(1, 'testuser')
        payload = self.auth.verify_token(token)
        assert payload is not None
        assert payload['user_id'] == 1
        assert payload['username'] == 'testuser'
```

### 5.2 集成测试

```python
# tests/test_server.py

import pytest
import asyncio
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

class TestWebSocketServer(AioHTTPTestCase):
    async def get_application(self):
        from src.server import WebSocketServer
        server = WebSocketServer(db_path=':memory:')
        return server.app

    @unittest_run_loop
    async def test_register(self):
        resp = await self.client.request(
            'POST',
            '/api/register',
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': 'password123'
            }
        )
        assert resp.status == 200
        data = await resp.json()
        assert 'token' in data
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_auth.py -v

# 运行并生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html

# 运行并显示详细输出
pytest tests/ -v -s
```

## 6. 调试技巧

### 6.1 日志配置

```python
# src/main.py

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 使用日志
logger.info("服务器启动")
logger.error("发生错误", exc_info=True)
logger.debug("调试信息")
```

### 6.2 断点调试

```python
# 使用pdb
import pdb; pdb.set_trace()

# 使用IDE断点
# 在VS Code中点击行号左侧设置断点
```

### 6.3 WebSocket调试

```python
# 添加消息日志
async def _handle_message(self, user_id: int, data: dict):
    logger.debug(f"收到消息: user_id={user_id}, data={data}")
    # 处理消息...
```

## 7. 性能优化

### 7.1 数据库优化

```python
# 使用索引
class User(Base):
    __tablename__ = 'users'
    username = Column(String(50), unique=True, index=True)  # 添加索引

# 批量操作
async def batch_create_messages(messages: List[Message]):
    async with self.async_session() as session:
        session.add_all(messages)
        await session.commit()

# 分页查询
async def get_messages(limit: int = 50, offset: int = 0):
    async with self.async_session() as session:
        result = await session.execute(
            select(Message)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
```

### 7.2 连接优化

```python
# 连接池
from sqlalchemy.pool import AsyncAdaptedQueuePool

engine = create_async_engine(
    db_url,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=10,
    max_overflow=20
)

# 心跳检测
async def _heartbeat_checker(self):
    while True:
        await asyncio.sleep(30)
        await self.connections.cleanup_stale_connections()
```

### 7.3 消息优化

```python
# 消息压缩
import zlib

def compress_message(message: str) -> bytes:
    return zlib.compress(message.encode('utf-8'))

def decompress_message(data: bytes) -> str:
    return zlib.decompress(data).decode('utf-8')

# 批量发送
async def batch_send_messages(user_id: int, messages: List[dict]):
    conn = self.connections.get_connection(user_id)
    if conn:
        for msg in messages:
            await conn.websocket.send_json(msg)
```

## 8. 部署指南

### 8.1 本地部署

```bash
# 启动服务器
python -m src.main

# 访问应用
open http://localhost:8765/static/index.html
```

### 8.2 Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8765
CMD ["python", "-m", "src.main"]
```

```bash
# 构建镜像
docker build -t social-chat-app .

# 运行容器
docker run -d -p 8765:8765 --name chat-app social-chat-app

# 查看日志
docker logs -f chat-app
```

### 8.3 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  chat-app:
    build: .
    ports:
      - "8765:8765"
    volumes:
      - ./data:/app/data
    environment:
      - JWT_SECRET_KEY=your-secret-key
      - DB_PATH=/app/data/chat.db
    restart: unless-stopped
```

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down
```

### 8.4 生产环境部署

```bash
# 使用Nginx反向代理
server {
    listen 80;
    server_name chat.example.com;

    location / {
        proxy_pass http://localhost:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 9. 常见问题

### 9.1 连接问题

**问题**: WebSocket连接失败

**解决方案**:
1. 检查服务器是否启动
2. 检查端口是否被占用
3. 检查防火墙设置
4. 检查令牌是否有效

### 9.2 数据库问题

**问题**: 数据库锁定

**解决方案**:
1. 检查是否有未关闭的连接
2. 使用连接池
3. 避免长时间事务

### 9.3 性能问题

**问题**: 消息延迟高

**解决方案**:
1. 检查网络连接
2. 优化数据库查询
3. 使用缓存
4. 增加服务器资源

## 10. 扩展开发

### 10.1 添加新功能

1. 在 `models/database.py` 中添加新的模型
2. 在 `models/db_manager.py` 中添加数据库操作
3. 在 `server/websocket_server.py` 中添加消息处理
4. 在 `static/js/app.js` 中添加前端逻辑
5. 在 `tests/` 中添加测试

### 10.2 添加新的API

```python
# 在 websocket_server.py 中添加路由
self.app.router.add_get('/api/new-endpoint', self.handle_new_endpoint)

# 实现处理函数
async def handle_new_endpoint(self, request: web.Request) -> web.Response:
    # 处理逻辑
    return web.json_response({'data': 'value'})
```

### 10.3 添加新的WebSocket消息类型

```python
# 在 _handle_message 方法中添加处理器
handlers = {
    'existing_type': self._handle_existing,
    'new_type': self._handle_new_type,  # 新增
}

# 实现处理函数
async def _handle_new_type(self, user_id: int, data: dict):
    # 处理逻辑
    pass
```

## 11. 学习资源

### 11.1 Python异步编程

- [Python asyncio文档](https://docs.python.org/3/library/asyncio.html)
- [aiohttp文档](https://docs.aiohttp.org/)
- [Real Python asyncio教程](https://realpython.com/async-io-python/)

### 11.2 WebSocket

- [WebSocket协议](https://tools.ietf.org/html/rfc6455)
- [websockets库文档](https://websockets.readthedocs.io/)
- [MDN WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

### 11.3 SQLAlchemy

- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [SQLAlchemy异步支持](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

### 11.4 JWT认证

- [JWT介绍](https://jwt.io/introduction)
- [PyJWT文档](https://pyjwt.readthedocs.io/)

## 12. 总结

本文档详细介绍了社交聊天应用的开发环境搭建、项目结构、核心模块开发、开发流程、测试、调试、性能优化、部署等方面。通过本文档，开发者可以快速上手项目开发并进行功能扩展。
