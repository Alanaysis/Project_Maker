//! MCP Client Example
//!
//! This example demonstrates how to interact with an MCP server
//! by sending JSON-RPC requests and processing responses.

use serde_json::json;

/// Simulate sending a request to an MCP server
fn send_request(request: &serde_json::Value) -> serde_json::Value {
    // In a real implementation, this would send the request via stdio/SSE/WebSocket
    // and receive the response from the server

    // For demonstration, we'll create mock responses
    let method = request["method"].as_str().unwrap_or("");

    match method {
        "initialize" => {
            json!({
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": false
                        }
                    },
                    "serverInfo": {
                        "name": "example-server",
                        "version": "0.1.0"
                    }
                },
                "id": request["id"]
            })
        }
        "tools/list" => {
            json!({
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": "calculator",
                            "description": "Perform basic arithmetic operations",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "operation": {
                                        "type": "string",
                                        "enum": ["add", "subtract", "multiply", "divide"]
                                    },
                                    "a": { "type": "number" },
                                    "b": { "type": "number" }
                                },
                                "required": ["operation", "a", "b"]
                            }
                        }
                    ]
                },
                "id": request["id"]
            })
        }
        "tools/call" => {
            let tool_name = request["params"]["name"].as_str().unwrap_or("");
            match tool_name {
                "calculator" => {
                    let op = request["params"]["arguments"]["operation"].as_str().unwrap_or("");
                    let a = request["params"]["arguments"]["a"].as_f64().unwrap_or(0.0);
                    let b = request["params"]["arguments"]["b"].as_f64().unwrap_or(0.0);

                    let result = match op {
                        "add" => a + b,
                        "subtract" => a - b,
                        "multiply" => a * b,
                        "divide" => {
                            if b == 0.0 {
                                return json!({
                                    "jsonrpc": "2.0",
                                    "result": {
                                        "isError": true,
                                        "content": [{"type": "text", "text": "Division by zero"}]
                                    },
                                    "id": request["id"]
                                });
                            }
                            a / b
                        }
                        _ => 0.0,
                    };

                    json!({
                        "jsonrpc": "2.0",
                        "result": {
                            "isError": false,
                            "content": [{"type": "text", "text": format!("{}", result)}]
                        },
                        "id": request["id"]
                    })
                }
                _ => {
                    json!({
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": format!("Tool not found: {}", tool_name)
                        },
                        "id": request["id"]
                    })
                }
            }
        }
        _ => {
            json!({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": format!("Method not found: {}", method)
                },
                "id": request["id"]
            })
        }
    }
}

fn main() {
    println!("MCP Client Example\n");
    println!("This example demonstrates the MCP protocol flow:\n");

    // Step 1: Initialize
    println!("1. Initialize Connection");
    println!("------------------------");
    let init_request = json!({
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "example-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    });

    println!("Request: {}", serde_json::to_string_pretty(&init_request).unwrap());
    let init_response = send_request(&init_request);
    println!("Response: {}\n", serde_json::to_string_pretty(&init_response).unwrap());

    // Step 2: List Tools
    println!("2. List Available Tools");
    println!("-----------------------");
    let list_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 2
    });

    println!("Request: {}", serde_json::to_string_pretty(&list_request).unwrap());
    let list_response = send_request(&list_request);
    println!("Response: {}\n", serde_json::to_string_pretty(&list_response).unwrap());

    // Step 3: Call Tool
    println!("3. Call Calculator Tool");
    println!("-----------------------");
    let call_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "calculator",
            "arguments": {
                "operation": "add",
                "a": 10,
                "b": 5
            }
        },
        "id": 3
    });

    println!("Request: {}", serde_json::to_string_pretty(&call_request).unwrap());
    let call_response = send_request(&call_request);
    println!("Response: {}\n", serde_json::to_string_pretty(&call_response).unwrap());

    // Step 4: Error Handling
    println!("4. Error Handling Example");
    println!("-------------------------");
    let error_request = json!({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "nonexistent",
            "arguments": {}
        },
        "id": 4
    });

    println!("Request: {}", serde_json::to_string_pretty(&error_request).unwrap());
    let error_response = send_request(&error_request);
    println!("Response: {}\n", serde_json::to_string_pretty(&error_response).unwrap());

    println!("This demonstrates the basic MCP protocol flow:");
    println!("1. Client initializes connection with server");
    println!("2. Client lists available tools");
    println!("3. Client calls a tool with arguments");
    println!("4. Server returns results or errors");
}
