//! Built-in tools tests

use mcp_server::tools::{CalculatorTool, EchoTool, TimestampTool};
use mcp_server::{McpServer, ToolHandler};
use serde_json::json;
use std::sync::Arc;

#[tokio::test]
async fn test_calculator_add() {
    let tool = CalculatorTool;
    let args = json!({"operation": "add", "a": 10, "b": 5});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "15");
}

#[tokio::test]
async fn test_calculator_subtract() {
    let tool = CalculatorTool;
    let args = json!({"operation": "subtract", "a": 10, "b": 5});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "5");
}

#[tokio::test]
async fn test_calculator_multiply() {
    let tool = CalculatorTool;
    let args = json!({"operation": "multiply", "a": 10, "b": 5});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "50");
}

#[tokio::test]
async fn test_calculator_divide() {
    let tool = CalculatorTool;
    let args = json!({"operation": "divide", "a": 10, "b": 5});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "2");
}

#[tokio::test]
async fn test_calculator_divide_by_zero() {
    let tool = CalculatorTool;
    let args = json!({"operation": "divide", "a": 10, "b": 0});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(result.is_error);
}

#[tokio::test]
async fn test_calculator_power() {
    let tool = CalculatorTool;
    let args = json!({"operation": "power", "a": 2, "b": 3});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "8");
}

#[tokio::test]
async fn test_calculator_invalid_operation() {
    let tool = CalculatorTool;
    let args = json!({"operation": "invalid", "a": 10, "b": 5});
    let result = tool.execute(Some(args)).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_calculator_missing_args() {
    let tool = CalculatorTool;
    let result = tool.execute(None).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_echo() {
    let tool = EchoTool;
    let args = json!({"message": "Hello, World!"});
    let result = tool.execute(Some(args)).await.unwrap();
    assert!(!result.is_error);
    assert_eq!(result.content[0].text(), "Hello, World!");
}

#[tokio::test]
async fn test_echo_missing_message() {
    let tool = EchoTool;
    let args = json!({});
    let result = tool.execute(Some(args)).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_timestamp() {
    let tool = TimestampTool;
    let result = tool.execute(None).await.unwrap();
    assert!(!result.is_error);
    // Verify it's a valid number
    let timestamp: u64 = result.content[0].text().parse().unwrap();
    assert!(timestamp > 0);
}

#[tokio::test]
async fn test_calculator_integration() {
    let server = McpServer::new("test-server", "1.0.0");

    server
        .register_tool(
            CalculatorTool::tool_definition(),
            Arc::new(CalculatorTool),
        )
        .await
        .unwrap();

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "calculator",
            "arguments": {
                "operation": "multiply",
                "a": 6,
                "b": 7
            }
        },
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["result"]["isError"], false);
    assert_eq!(response["result"]["content"][0]["text"], "42");
}

#[tokio::test]
async fn test_echo_integration() {
    let server = McpServer::new("test-server", "1.0.0");

    server
        .register_tool(EchoTool::tool_definition(), Arc::new(EchoTool))
        .await
        .unwrap();

    let request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "echo",
            "arguments": {
                "message": "test message"
            }
        },
        "id": 1
    })
    .to_string();

    let response = server.handle_request(&request).await.unwrap();
    let response: serde_json::Value = serde_json::from_str(&response).unwrap();

    assert_eq!(response["result"]["isError"], false);
    assert_eq!(response["result"]["content"][0]["text"], "test message");
}
