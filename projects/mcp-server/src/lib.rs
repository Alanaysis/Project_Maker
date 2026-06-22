//! MCP Server - Model Context Protocol Implementation
//!
//! This library implements a Model Context Protocol (MCP) server that allows
//! AI models to call external tools through a standardized JSON-RPC interface.
//!
//! ## Quick Start
//!
//! ```rust,no_run
//! use mcp_server::{McpServer, Tool, ToolHandler, ToolResult};
//! use serde_json::json;
//! use std::sync::Arc;
//!
//! # async fn example() -> mcp_server::Result<()> {
//! // Create server
//! let server = McpServer::new("my-server", "1.0.0");
//!
//! // Define a tool
//! let tool = Tool {
//!     name: "echo".to_string(),
//!     description: "Echo back the input".to_string(),
//!     input_schema: json!({
//!         "type": "object",
//!         "properties": {
//!             "message": { "type": "string" }
//!         }
//!     }),
//! };
//!
//! # struct EchoTool;
//! # #[async_trait::async_trait]
//! # impl ToolHandler for EchoTool {
//! #     async fn execute(&self, args: Option<serde_json::Value>) -> mcp_server::Result<ToolResult> {
//! #         Ok(ToolResult::text("echo"))
//! #     }
//! # }
//! // Register the tool
//! server.register_tool(tool, Arc::new(EchoTool)).await?;
//!
//! // Handle requests
//! let response = server.handle_request(r#"{"jsonrpc":"2.0","method":"tools/list","id":1}"#).await?;
//! # Ok(())
//! # }
//! ```

pub mod error;
pub mod jsonrpc;
pub mod mcp;
pub mod tool;
pub mod tools;

pub use error::{McpError, Result};
pub use mcp::McpServer;
pub use tool::{Tool, ToolHandler, ToolRegistry, ToolResult};
