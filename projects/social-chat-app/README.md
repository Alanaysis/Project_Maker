# Social Chat Application (社交聊天应用)

一个基于 Python + WebSocket 的实时社交聊天应用，支持单聊、群聊、文件传输、好友管理等功能。

## 项目简介

本项目是一个功能完整的社交聊天系统，采用 WebSocket 实现实时通信，支持多种消息类型和社交功能。适合学习实时通信、WebSocket、数据库设计等技术。

### 核心特性

- **用户系统**: 注册、登录、用户资料管理、JWT认证
- **好友管理**: 添加好友、好友请求、好友列表、删除好友
- **单聊功能**: 一对一实时聊天、消息历史、已读回执
- **群聊功能**: 创建群组、加入/退出群组、群组消息
- **消息类型**: 文本消息、图片消息、文件消息
- **消息管理**: 消息存储、消息搜索、离线消息
- **实时通知**: 在线状态、输入状态、消息推送
- **Web前端**: 完整的聊天界面，响应式设计

## 快速开始

### 环境要求

- Python 3.9+
- pip

### 安装依赖

```bash
# 进入项目目录
cd projects/social-chat-app

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 启动服务器

```bash
# 启动WebSocket服务器
python -m src.main

# 或者
python src/main.py
```

服务器将在 `http://localhost:8765` 启动。

### 访问应用

打开浏览器访问 `http://localhost:8765/static/index.html`

## 项目结构

```
social-chat-app/
├── src/
│   ├── __init__.py
│   ├── main.py              # 主程序入口
│   ├── server/              # 服务器模块
│   │   ├── __init__.py
│   │   ├── websocket_server.py  # WebSocket服务器
│   │   └── connection_manager.py # 连接管理器
│   ├── client/              # 客户端模块
│   │   ├── __init__.py
│   │   └── chat_client.py   # 聊天客户端
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库模型定义
│   │   └── db_manager.py    # 数据库管理器
│   └── utils/               # 工具模块
│       ├── __init__.py
│       ├── auth.py          # 认证服务
│       └── validators.py    # 数据验证
├── static/                  # 静态资源
│   ├── index.html           # 主页面
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/
│       └── app.js           # 前端JavaScript
├── tests/                   # 测试文件
│   ├── __init__.py
│   ├── test_auth.py         # 认证测试
│   └── test_validators.py   # 验证器测试
├── examples/                # 示例代码
│   ├── client_example.py    # 客户端示例
│   └── api_example.py       # API示例
├── docs/                    # 文档
│   ├── 01_RESEARCH.md       # 技术调研
│   ├── 02_REQUIREMENTS.md   # 需求分析
│   ├── 03_DESIGN.md         # 系统设计
│   ├── 04_PRODUCT.md        # 产品设计
│   └── 05_DEVELOPMENT.md    # 开发指南
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明
```

## 技术栈

### 后端
- **Python 3.9+**: 主要编程语言
- **websockets**: WebSocket服务器
- **aiohttp**: HTTP服务器
- **SQLAlchemy**: ORM框架
- **aiosqlite**: 异步SQLite驱动
- **bcrypt**: 密码加密
- **PyJWT**: JWT令牌

### 前端
- **HTML5/CSS3**: 页面结构和样式
- **JavaScript**: 前端逻辑
- **WebSocket API**: 实时通信

### 数据库
- **SQLite**: 轻量级数据库（可扩展到PostgreSQL/MySQL）

## API 文档

### HTTP API

#### 用户注册
```http
POST /api/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123",
  "nickname": "测试用户"
}
```

#### 用户登录
```http
POST /api/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

#### 搜索用户
```http
GET /api/users/search?q=test
Authorization: Bearer <token>
```

### WebSocket 消息

连接地址: `ws://localhost:8765/ws?token=<jwt_token>`

#### 发送消息
```json
{
  "type": "send_message",
  "content": "Hello!",
  "receiver_id": 2,
  "message_type": "text"
}
```

#### 发送群聊消息
```json
{
  "type": "send_message",
  "content": "Hello Group!",
  "group_id": 1,
  "message_type": "text"
}
```

#### 输入状态
```json
{
  "type": "typing",
  "receiver_id": 2,
  "is_typing": true
}
```

#### 已读回执
```json
{
  "type": "read_receipt",
  "sender_id": 2
}
```

#### 获取好友列表
```json
{
  "type": "get_friends"
}
```

#### 发送好友请求
```json
{
  "type": "send_friend_request",
  "to_user_id": 3,
  "message": "请求添加好友"
}
```

#### 创建群组
```json
{
  "type": "create_group",
  "name": "我的群组",
  "description": "群组描述"
}
```

#### 获取消息历史
```json
{
  "type": "get_messages",
  "receiver_id": 2,
  "limit": 50
}
```

#### 搜索消息
```json
{
  "type": "search_messages",
  "query": "关键词"
}
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_auth.py -v
pytest tests/test_validators.py -v

# 运行并生成覆盖率报告
pytest tests/ -v --cov=src --cov-report=html
```

## 配置说明

### 环境变量

```bash
# 服务器配置
HOST=0.0.0.0           # 监听地址
PORT=8765              # 监听端口
DB_PATH=social_chat.db # 数据库路径

# JWT配置
JWT_SECRET_KEY=your-secret-key  # JWT密钥（生产环境请修改）
```

### 数据库配置

默认使用SQLite，如需使用其他数据库，修改 `src/models/db_manager.py` 中的连接字符串：

```python
# PostgreSQL
self.db_url = "postgresql+asyncpg://user:password@localhost/dbname"

# MySQL
self.db_url = "mysql+aiomysql://user:password@localhost/dbname"
```

## 扩展功能

### 添加新的消息类型

1. 在 `src/models/database.py` 中添加新的 `MessageType`
2. 在 `src/server/websocket_server.py` 中处理新消息类型
3. 在前端 `static/js/app.js` 中添加渲染逻辑

### 添加新的WebSocket事件

1. 在 `src/server/websocket_server.py` 的 `_handle_message` 方法中添加处理器
2. 在 `src/server/connection_manager.py` 中实现相关逻辑
3. 在客户端 `src/client/chat_client.py` 中添加对应方法

## 部署说明

### 生产环境部署

1. **修改JWT密钥**: 使用强随机密钥
2. **使用PostgreSQL**: 替换SQLite以支持高并发
3. **添加Nginx**: 反向代理和负载均衡
4. **使用Docker**: 容器化部署

### Docker部署示例

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8765
CMD ["python", "-m", "src.main"]
```

```bash
docker build -t social-chat-app .
docker run -p 8765:8765 social-chat-app
```

## 性能优化

1. **连接池**: 使用数据库连接池减少连接开销
2. **消息缓存**: 使用Redis缓存热点消息
3. **分页加载**: 消息历史分页加载
4. **压缩传输**: 启用WebSocket压缩
5. **CDN加速**: 静态资源使用CDN

## 安全建议

1. **HTTPS**: 生产环境必须使用HTTPS
2. **输入验证**: 所有用户输入都需要验证
3. **SQL注入**: 使用ORM防止SQL注入
4. **XSS防护**: 前端输出需要转义
5. **频率限制**: 添加API频率限制
6. **文件上传**: 限制文件类型和大小

## 常见问题

### Q: 如何修改服务器端口？
A: 设置环境变量 `PORT=8080` 或修改 `src/main.py` 中的默认值。

### Q: 如何支持文件上传？
A: 需要添加文件存储服务（如MinIO、AWS S3），并修改消息处理逻辑。

### Q: 如何扩展到多服务器？
A: 使用Redis作为消息队列，实现跨服务器消息转发。

## 学习资源

- [WebSocket协议](https://tools.ietf.org/html/rfc6455)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [aiohttp文档](https://docs.aiohttp.org/)
- [JWT介绍](https://jwt.io/introduction)

## 许可证

MIT License

## 贡献指南

欢迎提交Issue和Pull Request！
