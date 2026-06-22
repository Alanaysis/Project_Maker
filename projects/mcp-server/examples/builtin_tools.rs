//! Built-in Tools Example
//!
//! This example demonstrates how to use the built-in tools provided by the MCP server library.

use mcp_server::tools::{CalculatorTool, EchoTool, TimestampTool};
use mcp_server::{McpServer, ToolHandler};
use std::sync::Arc;

#[tokio::main]
async fn main() -> mcp_server::Result<()> {
    println!("Built-in Tools Example\n");

    // Create server
    let server = McpServer::new("builtin-tools-server", "0.1.0");

    // Register built-in tools
    server
        .register_tool(
            CalculatorTool::tool_definition(),
            Arc::new(CalculatorTool),
        )
        .await?;

    server
        .register_tool(EchoTool::tool_definition(), Arc::new(EchoTool))
        .await?;

    server
        .register_tool(
            TimestampTool::tool_definition(),
            Arc::new(TimestampTool),
        )
        .await?;

    // List available tools
    println!("Available Tools:");
    println!("----------------");

    let list_request = r#"{"jsonrpc":"2.0","method":"tools/list","id":1}"#;
    let response = server.handle_request(list_request).await?;
    let response: serde_json::Value = serde_json::from_str(&response)?;

    if let Some(tools) = response["result"]["tools"].as_array() {
        for tool in tools {
            println!(
                "- {}: {}",
                tool["name"].as_str().unwrap_or(""),
                tool["description"].as_str().unwrap_or("")
            );
        }
    }

    println!("\nTool Execution Examples:");
    println!("------------------------");

    // Example 1: Calculator
    println!("\n1. Calculator (add 10 + 5):");
    let calc_request = r#"{"jsonrpc":"2.0","method":"tools/call","params":{"name":"calculator","arguments":{"operation":"add","a":10,"b":5}},"id":2}"#;
    let response = server.handle_request(calc_request).await?;
    let response: serde_json::Value = serde_json::from_str(&response)?;
    println!(
        "Result: {}",
        response["result"]["content"][0]["text"]
            .as_str()
            .unwrap_or("")
    );

    // Example 2: Echo
    println!("\n2. Echo (Hello, MCP!):");
    let echo_request = r#"{"jsonrpc":"2.0","method":"tools/call","params":{"name":"echo","arguments":{"message":"Hello, MCP!"}},"id":3}"#;
    let response = server.handle_request(echo_request).await?;
    let response: serde_json::Value = serde_json::from_str(&response)?;
    println!(
        "Result: {}",
        response["result"]["content"][0]["text"]
            .as_str()
            .unwrap_or("")
    );

    // Example 3: Timestamp
    println!("\n3. Timestamp:");
    let timestamp_request = r#"{"jsonrpc":"2.0","method":"tools/call","params":{"name":"timestamp","arguments":{}},"id":4}"#;
    let response = server.handle_request(timestamp_request).await?;
    let response: serde_json::Value = serde_json::from_str(&response)?;
    println!(
        "Current timestamp: {}",
        response["result"]["content"][0]["text"]
            .as_str()
            .unwrap_or("")
    );

    Ok(())
}
