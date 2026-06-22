//! Simple MCP Server Example
//!
//! This example demonstrates how to create a simple MCP server with custom tools.

use async_trait::async_trait;
use mcp_server::{McpServer, Tool, ToolHandler, ToolResult};
use serde_json::json;
use std::sync::Arc;

/// A greeting tool that says hello
struct GreetingTool;

#[async_trait]
impl ToolHandler for GreetingTool {
    async fn execute(&self, arguments: Option<serde_json::Value>) -> mcp_server::Result<ToolResult> {
        let name = arguments
            .and_then(|a| a.get("name").cloned())
            .and_then(|v| v.as_str().map(|s| s.to_string()))
            .unwrap_or_else(|| "World".to_string());

        Ok(ToolResult::text(format!("Hello, {}!", name)))
    }
}

/// A timestamp tool that returns current time
struct TimestampTool;

#[async_trait]
impl ToolHandler for TimestampTool {
    async fn execute(&self, _arguments: Option<serde_json::Value>) -> mcp_server::Result<ToolResult> {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        Ok(ToolResult::text(format!("{}", timestamp)))
    }
}

#[tokio::main]
async fn main() -> mcp_server::Result<()> {
    // Create server
    let server = McpServer::new("example-server", "0.1.0");

    // Register greeting tool
    let greeting_tool = Tool {
        name: "greeting".to_string(),
        description: "Generate a greeting message".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet"
                }
            }
        }),
    };
    server
        .register_tool(greeting_tool, Arc::new(GreetingTool))
        .await?;

    // Register timestamp tool
    let timestamp_tool = Tool {
        name: "timestamp".to_string(),
        description: "Get current Unix timestamp".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {}
        }),
    };
    server
        .register_tool(timestamp_tool, Arc::new(TimestampTool))
        .await?;

    // Example: Process requests manually
    println!("Example: Processing MCP requests\n");

    // 1. Initialize
    let init_request = json!({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "example-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    })
    .to_string();

    println!("Request: {}", init_request);
    let response = server.handle_request(&init_request).await?;
    println!("Response: {}\n", response);

    // 2. List tools
    let list_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 2
    })
    .to_string();

    println!("Request: {}", list_request);
    let response = server.handle_request(&list_request).await?;
    println!("Response: {}\n", response);

    // 3. Call greeting tool
    let call_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "greeting",
            "arguments": {
                "name": "MCP User"
            }
        },
        "id": 3
    })
    .to_string();

    println!("Request: {}", call_request);
    let response = server.handle_request(&call_request).await?;
    println!("Response: {}\n", response);

    // 4. Call timestamp tool
    let call_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "timestamp",
            "arguments": {}
        },
        "id": 4
    })
    .to_string();

    println!("Request: {}", call_request);
    let response = server.handle_request(&call_request).await?;
    println!("Response: {}\n", response);

    Ok(())
}
