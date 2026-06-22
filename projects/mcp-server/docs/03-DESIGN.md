# 03 - 技术设计

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   JSON-RPC   │  │     MCP      │  │    Tool      │  │
│  │   Layer      │──│   Protocol   │──│  Registry    │  │
│  │              │  │    Layer     │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                 │          │
│         ▼                 ▼                 ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Request    │  │   Response   │  │   Tools      │  │
│  │   Parser     │  │   Builder    │  │  (Handlers)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 职责 | 关键类型 |
|------|------|----------|
| `jsonrpc` | JSON-RPC 协议实现 | `JsonRpcRequest`, `JsonRpcResponse` |
| `mcp` | MCP 协议处理 | `McpServer` |
| `tool` | 工具管理 | `Tool`, `ToolRegistry`, `ToolHandler` |
| `error` | 错误处理 | `McpError` |

## 数据结构设计

### JSON-RPC 消息

```rust
// 请求消息
struct JsonRpcRequest {
    jsonrpc: String,      // 固定为 "2.0"
    method: String,       // 方法名
    params: Option<Value>, // 参数
    id: Option<Value>,    // 请求 ID（通知时为 None）
}

// 响应消息
struct JsonRpcResponse {
    jsonrpc: String,      // 固定为 "2.0"
    result: Option<Value>, // 成功结果
    error: Option<Error>,  // 错误信息
    id: Option<Value>,    // 对应的请求 ID
}
```

### MCP 类型

```rust
// 工具定义
struct Tool {
    name: String,           // 工具名称
    description: String,    // 工具描述
    input_schema: Value,    // 输入参数的 JSON Schema
}

// 工具调用请求
struct ToolCall {
    name: String,           // 工具名称
    arguments: Option<Value>, // 调用参数
}

// 工具调用结果
struct ToolResult {
    is_error: bool,         // 是否为错误
    content: Vec<Content>,  // 结果内容
}
```

## 接口设计

### 公共 API

#### McpServer

```rust
impl McpServer {
    /// 创建新的 MCP 服务器
    pub fn new(name: &str, version: &str) -> Self;

    /// 注册工具
    pub async fn register_tool(
        &self,
        tool: Tool,
        handler: Arc<dyn ToolHandler>,
    ) -> Result<()>;

    /// 处理请求
    pub async fn handle_request(&self, request: &str) -> Result<String>;
}
```

#### ToolHandler Trait

```rust
#[async_trait]
pub trait ToolHandler: Send + Sync {
    /// 执行工具
    async fn execute(
        &self,
        arguments: Option<Value>,
    ) -> Result<ToolResult>;
}
```

### 内部接口

#### 请求分发

```rust
async fn dispatch(&self, request: &JsonRpcRequest) -> JsonRpcResponse {
    match request.method.as_str() {
        "initialize" => self.handle_initialize(params),
        "tools/list" => self.handle_tools_list(),
        "tools/call" => self.handle_tools_call(params),
        _ => error_response(METHOD_NOT_FOUND),
    }
}
```

## 错误处理设计

### 错误类型

```rust
enum McpError {
    JsonRpc { code: i32, message: String },
    ToolNotFound(String),
    InvalidParams(String),
    ToolExecutionFailed(String),
    Serialization(serde_json::Error),
    Io(std::io::Error),
}
```

### 错误码

| 错误码 | 含义 |
|--------|------|
| -32700 | 解析错误 |
| -32600 | 无效请求 |
| -32601 | 方法未找到 |
| -32602 | 无效参数 |
| -32603 | 内部错误 |
| -32000 | 工具未找到 |
| -32001 | 工具执行错误 |

## 并发设计

### 共享状态

使用 `Arc<Mutex<ToolRegistry>>` 管理共享的工具注册表：

```rust
pub struct McpServer {
    info: ServerInfo,
    tool_registry: Arc<Mutex<ToolRegistry>>,
}
```

### 异步执行

- 使用 Tokio 异步运行时
- 工具执行使用 async trait
- 支持并发工具调用

## 扩展点设计

### 传输层抽象

```rust
#[async_trait]
pub trait Transport: Send + Sync {
    async fn read_request(&mut self) -> Result<String>;
    async fn write_response(&mut self, response: &str) -> Result<()>;
}
```

### 中间件支持

```rust
pub trait Middleware: Send + Sync {
    fn before_request(&self, request: &mut JsonRpcRequest);
    fn after_response(&self, response: &mut JsonRpcResponse);
}
```

## 依赖关系

```toml
[dependencies]
serde = "1.0"          # 序列化框架
serde_json = "1.0"     # JSON 处理
tokio = "1.0"          # 异步运行时
thiserror = "1.0"      # 错误处理
async-trait = "0.1"    # 异步 trait 支持
```
