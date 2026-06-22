# 05 - 开发手册

## 环境搭建

### 系统要求

- **操作系统**：Linux、macOS、Windows
- **Rust 版本**：1.70+
- **内存**：4GB+
- **磁盘空间**：1GB+

### 安装 Rust

```bash
# 安装 rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 配置环境变量
source $HOME/.cargo/env

# 验证安装
rustc --version
cargo --version
```

### 克隆项目

```bash
git clone <repository-url>
cd mcp-server
```

### 编译项目

```bash
# 调试版本
cargo build

# 发布版本
cargo build --release
```

## 核心模块解析

### 1. 错误处理模块 (`error.rs`)

**重点难点**：⭐ Rust 的错误处理模式

```rust
// 使用 thiserror 宏定义错误类型
#[derive(Error, Debug)]
pub enum McpError {
    #[error("Tool not found: {0}")]
    ToolNotFound(String),
    // ...
}

// Result 类型别名
pub type Result<T> = std::result::Result<T, McpError>;
```

**学习要点**：
- 使用 `thiserror` 简化错误定义
- 实现 `Display` trait 提供错误消息
- 错误转换和传播

### 2. JSON-RPC 模块 (`jsonrpc.rs`)

**重点难点**：⭐⭐ JSON-RPC 2.0 协议实现

```rust
// 请求消息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,      // 必须为 "2.0"
    pub method: String,       // 方法名
    pub params: Option<Value>, // 参数（可选）
    pub id: Option<Value>,    // 请求 ID（通知时为 None）
}
```

**学习要点**：
- Serde 序列化和反序列化
- JSON-RPC 消息格式
- 错误码规范

### 3. 工具模块 (`tool.rs`)

**重点难点**：⭐⭐⭐ 异步 Trait 和动态分发

```rust
// 异步工具处理 trait
#[async_trait]
pub trait ToolHandler: Send + Sync {
    async fn execute(&self, arguments: Option<Value>) -> Result<ToolResult>;
}

// 工具注册表
pub struct ToolRegistry {
    tools: HashMap<String, Arc<dyn ToolHandler>>,
    definitions: HashMap<String, Tool>,
}
```

**学习要点**：
- `async-trait` 宏的使用
- `Arc<dyn Trait>` 动态分发
- `Send + Sync` 约束

### 4. MCP 服务器模块 (`mcp.rs`)

**重点难点**：⭐⭐⭐ 共享状态和并发

```rust
pub struct McpServer {
    info: ServerInfo,
    tool_registry: Arc<Mutex<ToolRegistry>>,
}
```

**学习要点**：
- `Arc<Mutex<T>>` 共享状态模式
- 异步锁的使用
- 请求分发设计

## 开发流程

### 1. 添加新工具

```rust
use async_trait::async_trait;
use mcp_server::{Tool, ToolHandler, ToolResult};
use serde_json::json;

// 定义工具处理结构
struct MyTool;

// 实现 ToolHandler trait
#[async_trait]
impl ToolHandler for MyTool {
    async fn execute(
        &self,
        arguments: Option<serde_json::Value>,
    ) -> mcp_server::Result<ToolResult> {
        // 解析参数
        let args = arguments.ok_or_else(|| {
            mcp_server::McpError::InvalidParams("Missing arguments".to_string())
        })?;

        // 执行逻辑
        let result = "Hello from MyTool!";

        // 返回结果
        Ok(ToolResult::text(result))
    }
}

// 注册工具
let tool = Tool {
    name: "my_tool".to_string(),
    description: "My custom tool".to_string(),
    input_schema: json!({
        "type": "object",
        "properties": {
            "input": { "type": "string" }
        }
    }),
};

server.register_tool(tool, Arc::new(MyTool)).await?;
```

### 2. 添加新的错误类型

```rust
// 在 error.rs 中添加
#[derive(Error, Debug)]
pub enum McpError {
    // ... 现有错误
    
    #[error("My custom error: {0}")]
    MyCustomError(String),
}

// 在 McpError 实现中添加转换
impl McpError {
    pub fn to_jsonrpc_error(&self) -> JsonValue {
        match self {
            // ... 现有错误处理
            
            McpError::MyCustomError(msg) => serde_json::json!({
                "code": -32000,
                "message": format!("Custom error: {}", msg)
            }),
        }
    }
}
```

### 3. 添加新的 JSON-RPC 方法

```rust
// 在 mcp.rs 的 dispatch 方法中添加
async fn dispatch(&self, request: &JsonRpcRequest) -> JsonRpcResponse {
    match request.method.as_str() {
        // ... 现有方法
        
        "my/method" => self.handle_my_method(&request.params).await,
        _ => error_response(METHOD_NOT_FOUND),
    }
}

// 实现处理方法
async fn handle_my_method(&self, params: &Option<Value>) -> Result<Value> {
    // 实现逻辑
    Ok(json!({ "result": "success" }))
}
```

## 测试指南

### 单元测试

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tool_creation() {
        let tool = Tool {
            name: "test".to_string(),
            description: "Test tool".to_string(),
            input_schema: json!({}),
        };
        assert_eq!(tool.name, "test");
    }
}
```

### 集成测试

```rust
#[tokio::test]
async fn test_full_workflow() {
    let server = McpServer::new("test", "1.0.0");
    
    // 注册工具
    // ...
    
    // 发送请求
    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": { "name": "test", "arguments": {} },
        "id": 1
    }).to_string();
    
    let response = server.handle_request(&request).await.unwrap();
    // 验证响应
}
```

### 运行测试

```bash
# 运行所有测试
cargo test

# 运行特定测试
cargo test test_name

# 显示测试输出
cargo test -- --nocapture
```

## 调试技巧

### 1. 启用日志

```rust
// 在 main.rs 中添加
env_logger::init();
log::debug!("Request: {:?}", request);
```

### 2. 使用 cargo-watch

```bash
# 安装
cargo install cargo-watch

# 自动重编译和测试
cargo watch -x test
```

### 3. 性能分析

```bash
# 安装 cargo-flamegraph
cargo install flamegraph

# 生成火焰图
cargo flamegraph
```

## 常见问题

### Q: 如何处理大文件？
A: 使用流式处理，避免一次性加载整个文件到内存。

### Q: 如何实现异步工具？
A: 使用 `#[async_trait]` 宏和 `async fn`。

### Q: 如何共享状态？
A: 使用 `Arc<Mutex<T>>` 模式。

## 最佳实践

1. **错误处理**：使用 `Result` 类型，避免 `unwrap()`
2. **异步编程**：使用 `async/await`，避免阻塞
3. **类型安全**：充分利用 Rust 的类型系统
4. **文档注释**：所有公共 API 都要有文档
5. **测试覆盖**：核心功能必须有测试

## 参考资源

- [Rust 官方文档](https://doc.rust-lang.org)
- [Tokio 教程](https://tokio.rs/tokio/tutorial)
- [Serde 文档](https://serde.rs)
- [async-trait 文档](https://docs.rs/async-trait)
