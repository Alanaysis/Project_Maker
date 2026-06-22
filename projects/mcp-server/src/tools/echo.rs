//! Echo tool implementation

use async_trait::async_trait;
use serde_json::{json, Value as JsonValue};

use crate::tool::{Tool, ToolHandler, ToolResult};

/// Echo tool that returns the input message
pub struct EchoTool;

#[async_trait]
impl ToolHandler for EchoTool {
    async fn execute(&self, arguments: Option<JsonValue>) -> crate::Result<ToolResult> {
        let args = arguments.ok_or_else(|| {
            crate::McpError::InvalidParams("Missing arguments".to_string())
        })?;

        let message = args
            .get("message")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                crate::McpError::InvalidParams("Missing message parameter".to_string())
            })?;

        Ok(ToolResult::text(message.to_string()))
    }
}

impl EchoTool {
    /// Get the tool definition
    pub fn tool_definition() -> Tool {
        Tool {
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
        }
    }
}
