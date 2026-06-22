//! MCP Server main entry point

use async_trait::async_trait;
use mcp_server::{McpServer, Tool, ToolHandler, ToolResult};
use serde_json::{json, Value as JsonValue};
use std::io::{self, BufRead, Write};
use std::sync::Arc;

/// A simple calculator tool
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
                mcp_server::McpError::InvalidParams("Missing operation".to_string())
            })?;

        let a = args.get("a").and_then(|v| v.as_f64()).ok_or_else(|| {
            mcp_server::McpError::InvalidParams("Missing or invalid parameter a".to_string())
        })?;

        let b = args.get("b").and_then(|v| v.as_f64()).ok_or_else(|| {
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
            _ => {
                return Err(mcp_server::McpError::InvalidParams(format!(
                    "Unknown operation: {}",
                    operation
                )));
            }
        };

        Ok(ToolResult::text(format!("{}", result)))
    }
}

/// A simple echo tool
struct EchoTool;

#[async_trait]
impl ToolHandler for EchoTool {
    async fn execute(&self, arguments: Option<JsonValue>) -> mcp_server::Result<ToolResult> {
        let args = arguments.ok_or_else(|| {
            mcp_server::McpError::InvalidParams("Missing arguments".to_string())
        })?;

        let message = args
            .get("message")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                mcp_server::McpError::InvalidParams("Missing message parameter".to_string())
            })?;

        Ok(ToolResult::text(message.to_string()))
    }
}

#[tokio::main]
async fn main() -> mcp_server::Result<()> {
    eprintln!("MCP Server starting...");

    let server = McpServer::new("example-mcp-server", "0.1.0");

    // Register calculator tool
    let calculator_tool = Tool {
        name: "calculator".to_string(),
        description: "Perform basic arithmetic operations".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
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

    // Register echo tool
    let echo_tool = Tool {
        name: "echo".to_string(),
        description: "Echo back the input message".to_string(),
        input_schema: json!({
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to echo"
                }
            },
            "required": ["message"]
        }),
    };
    server
        .register_tool(echo_tool, Arc::new(EchoTool))
        .await?;

    eprintln!("MCP Server ready. Waiting for requests on stdin...");

    // Read from stdin line by line
    let stdin = io::stdin();
    let stdout = io::stdout();

    for line in stdin.lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }

        eprintln!("Received: {}", line);

        match server.handle_request(&line).await {
            Ok(response) => {
                eprintln!("Sending: {}", response);
                let mut out = stdout.lock();
                writeln!(out, "{}", response)?;
                out.flush()?;
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                // Send error response
                let error_response = json!({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": format!("Internal error: {}", e)
                    },
                    "id": null
                });
                let mut out = stdout.lock();
                writeln!(out, "{}", error_response)?;
                out.flush()?;
            }
        }
    }

    Ok(())
}
