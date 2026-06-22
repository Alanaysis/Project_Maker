//! Tool registration and management for MCP

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use std::collections::HashMap;
use std::sync::Arc;

/// Tool definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Tool {
    /// Tool name (unique identifier)
    pub name: String,
    /// Human-readable description
    pub description: String,
    /// JSON Schema for input parameters
    #[serde(rename = "inputSchema")]
    pub input_schema: JsonValue,
}

/// Tool call request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    /// Tool name
    pub name: String,
    /// Tool arguments
    pub arguments: Option<JsonValue>,
}

/// Tool call result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    /// Whether the tool call was successful
    pub is_error: bool,
    /// Result content
    pub content: Vec<ToolContent>,
}

/// Content in a tool result
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ToolContent {
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "image")]
    Image { data: String, mime_type: String },
}

impl ToolContent {
    /// Get text content if this is a text variant
    pub fn text(&self) -> &str {
        match self {
            ToolContent::Text { text } => text,
            _ => "",
        }
    }
}

impl ToolResult {
    /// Create a successful text result
    pub fn text(text: impl Into<String>) -> Self {
        Self {
            is_error: false,
            content: vec![ToolContent::Text { text: text.into() }],
        }
    }

    /// Create an error result
    pub fn error(message: impl Into<String>) -> Self {
        Self {
            is_error: true,
            content: vec![ToolContent::Text { text: message.into() }],
        }
    }
}

/// Trait for implementing tools
#[async_trait]
pub trait ToolHandler: Send + Sync {
    /// Execute the tool with given arguments
    async fn execute(&self, arguments: Option<JsonValue>) -> crate::Result<ToolResult>;
}

/// Registry for managing tools
pub struct ToolRegistry {
    tools: HashMap<String, Arc<dyn ToolHandler>>,
    definitions: HashMap<String, Tool>,
}

impl ToolRegistry {
    /// Create a new empty registry
    pub fn new() -> Self {
        Self {
            tools: HashMap::new(),
            definitions: HashMap::new(),
        }
    }

    /// Register a new tool
    pub fn register(
        &mut self,
        tool: Tool,
        handler: Arc<dyn ToolHandler>,
    ) -> crate::Result<()> {
        let name = tool.name.clone();
        if self.tools.contains_key(&name) {
            return Err(crate::McpError::InvalidParams(format!(
                "Tool already registered: {}",
                name
            )));
        }
        self.definitions.insert(name.clone(), tool);
        self.tools.insert(name, handler);
        Ok(())
    }

    /// Get a tool handler by name
    pub fn get_handler(&self, name: &str) -> Option<Arc<dyn ToolHandler>> {
        self.tools.get(name).cloned()
    }

    /// Get all tool definitions
    pub fn list_tools(&self) -> Vec<Tool> {
        self.definitions.values().cloned().collect()
    }

    /// Check if a tool exists
    pub fn has_tool(&self, name: &str) -> bool {
        self.tools.contains_key(name)
    }
}

impl Default for ToolRegistry {
    fn default() -> Self {
        Self::new()
    }
}
