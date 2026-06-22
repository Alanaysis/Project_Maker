//! MCP Server implementation

use serde::{Deserialize, Serialize};
use serde_json::Value as JsonValue;
use std::sync::Arc;
use tokio::sync::Mutex;

use crate::jsonrpc::{JsonRpcError, JsonRpcRequest, JsonRpcResponse};
use crate::tool::{ToolCall, ToolRegistry};

/// MCP Server capabilities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerCapabilities {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tools: Option<ToolsCapability>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolsCapability {
    pub list_changed: bool,
}

/// MCP Server information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerInfo {
    pub name: String,
    pub version: String,
}

/// Initialize request params
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InitializeParams {
    #[serde(rename = "protocolVersion")]
    pub protocol_version: String,
    pub capabilities: ClientCapabilities,
    #[serde(rename = "clientInfo")]
    pub client_info: ClientInfo,
}

/// Client capabilities
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientCapabilities {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub roots: Option<JsonValue>,
}

/// Client information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientInfo {
    pub name: String,
    pub version: String,
}

/// MCP Server
pub struct McpServer {
    info: ServerInfo,
    tool_registry: Arc<Mutex<ToolRegistry>>,
}

impl McpServer {
    /// Create a new MCP server
    pub fn new(name: impl Into<String>, version: impl Into<String>) -> Self {
        Self {
            info: ServerInfo {
                name: name.into(),
                version: version.into(),
            },
            tool_registry: Arc::new(Mutex::new(ToolRegistry::new())),
        }
    }

    /// Register a tool
    pub async fn register_tool(
        &self,
        tool: crate::tool::Tool,
        handler: Arc<dyn crate::tool::ToolHandler>,
    ) -> crate::Result<()> {
        let mut registry = self.tool_registry.lock().await;
        registry.register(tool, handler)
    }

    /// Handle a JSON-RPC request
    pub async fn handle_request(&self, request: &str) -> crate::Result<String> {
        let request = JsonRpcRequest::from_str(request)?;
        let response = self.dispatch(&request).await;
        response.to_json()
    }

    /// Dispatch request to appropriate handler
    async fn dispatch(&self, request: &JsonRpcRequest) -> JsonRpcResponse {
        let id = request.id.clone();

        let result = match request.method.as_str() {
            "initialize" => self.handle_initialize(&request.params).await,
            "tools/list" => self.handle_tools_list().await,
            "tools/call" => self.handle_tools_call(&request.params).await,
            "notifications/initialized" => {
                // Notification, no response needed
                return JsonRpcResponse::success(id, serde_json::json!({}));
            }
            _ => {
                return JsonRpcResponse::error(
                    id,
                    JsonRpcError {
                        code: crate::jsonrpc::error_codes::METHOD_NOT_FOUND,
                        message: format!("Method not found: {}", request.method),
                        data: None,
                    },
                );
            }
        };

        match result {
            Ok(result) => JsonRpcResponse::success(id, result),
            Err(e) => JsonRpcResponse::error(id, e.to_jsonrpc_error().into()),
        }
    }

    /// Handle initialize request
    async fn handle_initialize(&self, params: &Option<JsonValue>) -> crate::Result<JsonValue> {
        let _params: InitializeParams = match params {
            Some(p) => serde_json::from_value(p.clone())?,
            None => {
                return Err(crate::McpError::InvalidParams(
                    "Missing initialize params".to_string(),
                ))
            }
        };

        let response = serde_json::json!({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": false
                }
            },
            "serverInfo": {
                "name": self.info.name,
                "version": self.info.version
            }
        });

        Ok(response)
    }

    /// Handle tools/list request
    async fn handle_tools_list(&self) -> crate::Result<JsonValue> {
        let registry = self.tool_registry.lock().await;
        let tools = registry.list_tools();
        Ok(serde_json::json!({ "tools": tools }))
    }

    /// Handle tools/call request
    async fn handle_tools_call(&self, params: &Option<JsonValue>) -> crate::Result<JsonValue> {
        let call: ToolCall = match params {
            Some(p) => serde_json::from_value(p.clone())?,
            None => {
                return Err(crate::McpError::InvalidParams(
                    "Missing tool call params".to_string(),
                ))
            }
        };

        let registry = self.tool_registry.lock().await;
        let handler = registry
            .get_handler(&call.name)
            .ok_or_else(|| crate::McpError::ToolNotFound(call.name.clone()))?;

        // Drop the lock before async operation
        drop(registry);

        let result = handler.execute(call.arguments).await?;
        Ok(serde_json::to_value(result)?)
    }
}

/// Helper function to create a tool definition
pub fn create_tool(
    name: impl Into<String>,
    description: impl Into<String>,
    input_schema: JsonValue,
) -> crate::tool::Tool {
    crate::tool::Tool {
        name: name.into(),
        description: description.into(),
        input_schema,
    }
}
