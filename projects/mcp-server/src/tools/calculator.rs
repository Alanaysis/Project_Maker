//! Calculator tool implementation

use async_trait::async_trait;
use serde_json::{json, Value as JsonValue};

use crate::tool::{Tool, ToolHandler, ToolResult};

/// Calculator tool supporting basic arithmetic operations
pub struct CalculatorTool;

#[async_trait]
impl ToolHandler for CalculatorTool {
    async fn execute(&self, arguments: Option<JsonValue>) -> crate::Result<ToolResult> {
        let args = arguments.ok_or_else(|| {
            crate::McpError::InvalidParams("Missing arguments".to_string())
        })?;

        let operation = args
            .get("operation")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                crate::McpError::InvalidParams("Missing operation parameter".to_string())
            })?;

        let a = args
            .get("a")
            .and_then(|v| v.as_f64())
            .ok_or_else(|| {
                crate::McpError::InvalidParams("Missing or invalid parameter a".to_string())
            })?;

        let b = args
            .get("b")
            .and_then(|v| v.as_f64())
            .ok_or_else(|| {
                crate::McpError::InvalidParams("Missing or invalid parameter b".to_string())
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
                return Err(crate::McpError::InvalidParams(format!(
                    "Unknown operation: {}. Supported: add, subtract, multiply, divide, power, modulo",
                    operation
                )));
            }
        };

        Ok(ToolResult::text(format!("{}", result)))
    }
}

impl CalculatorTool {
    /// Get the tool definition
    pub fn tool_definition() -> Tool {
        Tool {
            name: "calculator".to_string(),
            description: "Perform basic arithmetic operations (add, subtract, multiply, divide, power, modulo)".to_string(),
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
        }
    }
}
