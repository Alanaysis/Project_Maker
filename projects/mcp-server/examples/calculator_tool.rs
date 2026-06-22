//! Calculator Tool Example
//!
//! This example shows how to create a calculator tool with multiple operations.

use async_trait::async_trait;
use mcp_server::{McpServer, Tool, ToolHandler, ToolResult};
use serde_json::{json, Value as JsonValue};
use std::sync::Arc;

/// Calculator tool supporting basic arithmetic
struct CalculatorTool;

#[async_trait]
impl ToolHandler for CalculatorTool {
    async fn execute(&self, arguments: Option<JsonValue>) -> mcp_server::Result<ToolResult> {
        let args = arguments.ok_or_else(|| {
            mcp_server::McpError::InvalidParams("Missing arguments".to_string())
        })?;

        let operation = args
            .get("operation")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                mcp_server::McpError::InvalidParams("Missing operation parameter".to_string())
            })?;

        let a = args
            .get("a")
            .and_then(|v| v.as_f64())
            .ok_or_else(|| {
                mcp_server::McpError::InvalidParams("Missing or invalid parameter a".to_string())
            })?;

        let b = args
            .get("b")
            .and_then(|v| v.as_f64())
            .ok_or_else(|| {
                mcp_server::McpError::InvalidParams("Missing or invalid parameter b".to_string())
            })?;

        let result = match operation {
            "add" => a + b,
            "subtract" => a - b,
            "multiply" => a * b,
            "divide" => {
                if b == 0.0 {
                    return Ok(ToolResult::error("Division by zero"));
                }
                a / b
            }
            "power" => a.powf(b),
            "modulo" => {
                if b == 0.0 {
                    return Ok(ToolResult::error("Division by zero"));
                }
                a % b
            }
            _ => {
                return Err(mcp_server::McpError::InvalidParams(format!(
                    "Unknown operation: {}. Supported: add, subtract, multiply, divide, power, modulo",
                    operation
                )));
            }
        };

        Ok(ToolResult::text(format!("{}", result)))
    }
}

#[tokio::main]
async fn main() -> mcp_server::Result<()> {
    let server = McpServer::new("calculator-server", "0.1.0");

    // Register calculator tool
    let calculator_tool = Tool {
        name: "calculator".to_string(),
        description: "Perform basic arithmetic operations".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide", "power", "modulo"],
                    "description": "The arithmetic operation to perform"
                },
                "a": {
                    "type": "number",
                    "description": "First operand"
                },
                "b": {
                    "type": "number",
                    "description": "Second operand"
                }
            },
            "required": ["operation", "a", "b"]
        }),
    };

    server
        .register_tool(calculator_tool, Arc::new(CalculatorTool))
        .await?;

    // Example calculations
    println!("Calculator Tool Examples:\n");

    let examples = vec![
        ("add", 10.0, 5.0),
        ("subtract", 10.0, 5.0),
        ("multiply", 10.0, 5.0),
        ("divide", 10.0, 5.0),
        ("power", 2.0, 3.0),
        ("modulo", 10.0, 3.0),
    ];

    for (op, a, b) in examples {
        let request = json!({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "calculator",
                "arguments": {
                    "operation": op,
                    "a": a,
                    "b": b
                }
            },
            "id": 1
        })
        .to_string();

        let response = server.handle_request(&request).await?;
        let response: serde_json::Value = serde_json::from_str(&response)?;

        let result = &response["result"]["content"][0]["text"];
        println!("{} {} {} = {}", a, op, b, result.as_str().unwrap());
    }

    Ok(())
}
