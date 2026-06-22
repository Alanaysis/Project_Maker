//! MCP Server integration tests

use async_trait::async_trait;
use mcp_server::{McpServer, Tool, ToolHandler, ToolResult};
use serde_json::json;
use std::sync::Arc;

/// Test tool that returns a fixed value
struct TestTool;

#[async_trait]
impl ToolHandler for TestTool {
    async fn execute(&self, arguments: Option<serde_json::Value>) -> mcp_server::Result<ToolResult> {
        let message = arguments
            .and_then(|a| a.get("message").cloned())
            .and_then(|v| v.as_str().map(|s| s.to_string()))
            .unwrap_or_else(|| "default".to_string());

        Ok(ToolResult::text(format!("Test: {}", message)))
    }
}

#[tokio::test]
async fn test_initialize() {
    let server = McpServer::new("test-server", "1.0.0");

    let request = json!({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["jsonrpc"], "2.0");
    assert!(response["result"].is_object());
    assert_eq!(response["result"]["protocolVersion"], "2024-11-05");
    assert_eq!(response["result"]["serverInfo"]["name"], "test-server");
    assert_eq!(response["id"], 1);
}

#[tokio::test]
async fn test_tools_list_empty() {
    let server = McpServer::new("test-server", "1.0.0");

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["jsonrpc"], "2.0");
    assert!(response["result"]["tools"].is_array());
    assert_eq!(response["result"]["tools"].as_array().unwrap().len(), 0);
}

#[tokio::test]
async fn test_tools_list_with_tools() {
    let server = McpServer::new("test-server", "1.0.0");

    let tool = Tool {
        name: "test".to_string(),
        description: "A test tool".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "message": { "type": "string" }
            }
        }),
    };

    server
        .register_tool(tool, Arc::new(TestTool))
        .await
        .unwrap();

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    let tools = response["result"]["tools"].as_array().unwrap();
    assert_eq!(tools.len(), 1);
    assert_eq!(tools[0]["name"], "test");
    assert_eq!(tools[0]["description"], "A test tool");
}

#[tokio::test]
async fn test_tools_call_success() {
    let server = McpServer::new("test-server", "1.0.0");

    let tool = Tool {
        name: "echo".to_string(),
        description: "Echo tool".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "message": { "type": "string" }
            }
        }),
    };

    server
        .register_tool(tool, Arc::new(TestTool))
        .await
        .unwrap();

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "echo",
            "arguments": {
                "message": "hello"
            }
        },
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["jsonrpc"], "2.0");
    assert!(response["result"].is_object());
    assert_eq!(response["result"]["isError"], false);
    let content = response["result"]["content"].as_array().unwrap();
    assert_eq!(content[0]["type"], "text");
    assert_eq!(content[0]["text"], "Test: hello");
}

#[tokio::test]
async fn test_tools_call_not_found() {
    let server = McpServer::new("test-server", "1.0.0");

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "nonexistent",
            "arguments": {}
        },
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["jsonrpc"], "2.0");
    assert!(response["error"].is_object());
    assert_eq!(response["error"]["code"], -32601);
}

#[tokio::test]
async fn test_method_not_found() {
    let server = McpServer::new("test-server", "1.0.0");

    let request = json!({
        "jsonrpc": "2.0",
        "method": "nonexistent/method",
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["jsonrpc"], "2.0");
    assert!(response["error"].is_object());
    assert_eq!(response["error"]["code"], -32601);
}

#[tokio::test]
async fn test_invalid_json() {
    let server = McpServer::new("test-server", "1.0.0");

    let result = server.handle_request("invalid json").await;
    assert!(result.is_err());
}
