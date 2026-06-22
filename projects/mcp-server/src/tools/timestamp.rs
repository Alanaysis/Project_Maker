//! Timestamp tool implementation

use async_trait::async_trait;
use serde_json::{json, Value as JsonValue};

use crate::tool::{Tool, ToolHandler, ToolResult};

/// Timestamp tool that returns the current Unix timestamp
pub struct TimestampTool;

#[async_trait]
impl ToolHandler for TimestampTool {
    async fn execute(&self, _arguments: Option<JsonValue>) -> crate::Result<ToolResult> {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        Ok(ToolResult::text(format!("{}", timestamp)))
    }
}

impl TimestampTool {
    /// Get the tool definition
    pub fn tool_definition() -> Tool {
        Tool {
            name: "timestamp".to_string(),
            description: "Get the current Unix timestamp".to_string(),
            input_schema: json!({
                "type": "object",
                "properties": {}
            }),
        }
    }
}
