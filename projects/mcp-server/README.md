# MCP Server - Model Context Protocol Implementation

## 项目概述

这是一个用 Rust 实现的 Model Context Protocol (MCP) 服务器。MCP 是一种开放协议，用于标准化 AI 应用程序与外部数据源、工具和工作流的连接方式。

## 学习目标

通过这个项目，你将学习到：

1. **MCP 协议规范**
   - 理解 MCP 的架构设计（Host、Client、Server）
   - 掌握 JSON-RPC 2.0 通信协议
   - 了解工具、资源、提示等核心概念

2. **Rust 异步编程**
   - 使用 Tokio 进行异步 I/O
   - async/await 语法和 trait
   - 共享状态和并发控制

3. **协议实现**
   - 消息序列化/反序列化
   - 请求路由和分发
   - 错误处理和响应格式化

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Rust | 主语言 | ⭐⭐⭐ |
| Tokio | 异步运行时 | ⭐⭐ |
| Serde | 序列化框架 | ⭐⭐ |
| JSON-RPC 2.0 | 通信协议 | ⭐⭐ |

## 核心概念

### MCP 架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Host     │────▶│   Client    │────▶│   Server    │
│ (AI 应用)   │     │ (协议处理)   │     │ (工具提供)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 核心流程

```
AI 请求 → 协议解析 → 工具路由 → 执行 → 结果返回
```

### JSON-RPC 方法

| 方法 | 描述 |
|------|------|
| `initialize` | 初始化握手 |
| `tools/list` | 列出可用工具 |
| `tools/call` | 调用工具 |
| `resources/list` | 列出资源 |
| `resources/read` | 读取资源 |

## 项目结构

```
mcp-server/
├── src/
│   ├── lib.rs          # 库入口
│   ├── main.rs         # 可执行文件入口
│   ├── error.rs        # 错误类型定义
│   ├── jsonrpc.rs      # JSON-RPC 实现
│   ├── mcp.rs          # MCP 服务器核心
│   └── tool.rs         # 工具注册和管理
├── tests/
│   └── mcp_test.rs     # 集成测试
├── examples/
│   └── simple_server.rs # 使用示例
├── docs/               # 文档目录
└── Cargo.toml          # 项目配置
```

## 快速开始

### 环境要求

- Rust 1.70+
- Cargo

### 编译运行

```bash
# 编译项目
cargo build

# 运行测试
cargo test

# 运行示例
cargo run --example simple_server

# 运行服务器
cargo run
```

### 使用方式

服务器启动后，通过 stdin/stdout 进行 JSON-RPC 通信：

```json
// 请求: 初始化
{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"client","version":"1.0.0"}},"id":1}

// 响应
{"jsonrpc":"2.0","result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":false}},"serverInfo":{"name":"example-mcp-server","version":"0.1.0"}},"id":1}

// 请求: 列出工具
{"jsonrpc":"2.0","method":"tools/list","id":2}

// 请求: 调用工具
{"jsonrpc":"2.0","method":"tools/call","params":{"name":"calculator","arguments":{"operation":"add","a":1,"b":2}},"id":3}
```

## 重点难点

### ⭐ JSON-RPC 协议实现

JSON-RPC 2.0 是 MCP 的通信基础。关键点：
- 请求/响应/通知三种消息类型
- 错误码规范（-32700 到 -32000）
- ID 字段用于关联请求和响应

### ⭐ 异步工具执行

使用 Rust 的 async trait 实现异步工具：
```rust
#[async_trait]
pub trait ToolHandler: Send + Sync {
    async fn execute(&self, arguments: Option<Value>) -> Result<ToolResult>;
}
```

### ⭐ 共享状态管理

使用 `Arc<Mutex<ToolRegistry>>` 在异步环境中安全共享工具注册表。

## 值得思考

1. **为什么选择 JSON-RPC 而不是 REST？**
   - JSON-RPC 是二进制协议，更适合流式通信
   - 支持双向通信和通知
   - 更轻量级，适合本地通信

2. **MCP 与 Function Calling 的区别？**
   - MCP 是标准化协议，支持多种传输方式
   - Function Calling 是模型特定的实现
   - MCP 提供更丰富的功能（资源、提示等）

3. **如何扩展这个服务器？**
   - 添加更多传输方式（SSE、WebSocket）
   - 实现资源和提示功能
   - 添加认证和权限控制

## 参考资源

- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP 规范](https://spec.modelcontextprotocol.io)
- [Rust MCP SDK](https://github.com/modelcontextprotocol/rust-sdk)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [Tokio 文档](https://tokio.rs)
- [Serde 文档](https://serde.rs)

## 许可证

MIT License
