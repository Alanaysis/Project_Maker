//! Error types for MCP server

use serde_json::Value as JsonValue;
use thiserror::Error;

/// Result type alias for MCP operations
pub type Result<T> = std::result::Result<T, McpError>;

/// Main error type for MCP server
#[derive(Error, Debug)]
pub enum McpError {
    /// JSON-RPC protocol errors
    #[error("JSON-RPC error: {message}")]
    JsonRpc {
        code: i32,
        message: String,
        data: Option<JsonValue>,
    },

    /// Tool not found
    #[error("Tool not found: {0}")]
    ToolNotFound(String),

    /// Invalid tool parameters
    #[error("Invalid parameters: {0}")]
    InvalidParams(String),

    /// Tool execution failed
    #[error("Tool execution failed: {0}")]
    ToolExecutionFailed(String),

    /// Serialization/Deserialization error
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    /// IO error
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// Invalid request
    #[error("Invalid request: {0}")]
    InvalidRequest(String),

    /// Method not found
    #[error("Method not found: {0}")]
    MethodNotFound(String),
}

impl McpError {
    /// Convert error to JSON-RPC error response
    pub fn to_jsonrpc_error(&self) -> JsonValue {
        match self {
            McpError::JsonRpc { code, message, data } => {
                let mut error = serde_json::json!({
                    "code": code,
                    "message": message
                });
                if let Some(data) = data {
                    error["data"] = data.clone();
                }
                error
            }
            McpError::ToolNotFound(name) => serde_json::json!({
                "code": -32601,
                "message": format!("Tool not found: {}", name)
            }),
            McpError::InvalidParams(msg) => serde_json::json!({
                "code": -32602,
                "message": format!("Invalid params: {}", msg)
            }),
            McpError::ToolExecutionFailed(msg) => serde_json::json!({
                "code": -32000,
                "message": format!("Tool execution failed: {}", msg)
            }),
            McpError::MethodNotFound(method) => serde_json::json!({
                "code": -32601,
                "message": format!("Method not found: {}", method)
            }),
            _ => serde_json::json!({
                "code": -32603,
                "message": format!("Internal error: {}", self)
            }),
        }
    }
}
