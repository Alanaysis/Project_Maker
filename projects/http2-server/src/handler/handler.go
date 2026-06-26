// Package handler implements HTTP/2 request handling.
package handler

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/anthropic/http2-server/internal/connection"
	"github.com/anthropic/http2-server/internal/frame"
)

// Router handles HTTP/2 request routing
type Router struct {
	routes map[string]map[string]HandlerFunc
}

// HandlerFunc is a function that handles an HTTP/2 request
type HandlerFunc func(stream *connection.Stream) error

// NewRouter creates a new router
func NewRouter() *Router {
	return &Router{
		routes: make(map[string]map[string]HandlerFunc),
	}
}

// Get registers a handler for GET requests
func (r *Router) Get(path string, handler HandlerFunc) {
	r.addRoute("GET", path, handler)
}

// Post registers a handler for POST requests
func (r *Router) Post(path string, handler HandlerFunc) {
	r.addRoute("POST", path, handler)
}

// Put registers a handler for PUT requests
func (r *Router) Put(path string, handler HandlerFunc) {
	r.addRoute("PUT", path, handler)
}

// Delete registers a handler for DELETE requests
func (r *Router) Delete(path string, handler HandlerFunc) {
	r.addRoute("DELETE", path, handler)
}

func (r *Router) addRoute(method, path string, handler HandlerFunc) {
	if _, ok := r.routes[method]; !ok {
		r.routes[method] = make(map[string]HandlerFunc)
	}
	r.routes[method][path] = handler
}

// Handle processes an HTTP/2 request
func (r *Router) Handle(stream *connection.Stream) error {
	// Extract method and path from headers
	var method, path string
	for _, h := range stream.Headers {
		switch h.Name {
		case ":method":
			method = h.Value
		case ":path":
			path = h.Value
		}
	}

	if method == "" || path == "" {
		return sendError(stream, 400, "Bad Request")
	}

	// Find matching route
	methodRoutes, ok := r.routes[method]
	if !ok {
		return sendError(stream, 405, "Method Not Allowed")
	}

	handler, ok := methodRoutes[path]
	if !ok {
		return sendError(stream, 404, "Not Found")
	}

	// Execute handler
	return handler(stream)
}

func sendError(stream *connection.Stream, code int, message string) error {
	stream.ResponseCode = code
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: strconv.Itoa(code)},
		{Name: "content-type", Value: "text/plain"},
	}
	stream.ResponseBody = []byte(message)
	return nil
}

// DefaultHandler provides default HTTP/2 endpoints
type DefaultHandler struct {
	Router *Router
}

// NewDefaultHandler creates a default handler with common endpoints
func NewDefaultHandler() *DefaultHandler {
	router := NewRouter()

	// Register default routes
	router.Get("/", handleRoot)
	router.Get("/health", handleHealth)
	router.Get("/info", handleInfo)
	router.Post("/echo", handleEcho)

	return &DefaultHandler{
		Router: router,
	}
}

// Handle processes a request using the default handler
func (h *DefaultHandler) Handle(stream *connection.Stream) error {
	return h.Router.Handle(stream)
}

func handleRoot(stream *connection.Stream) error {
	stream.ResponseCode = 200
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: "200"},
		{Name: "content-type", Value: "text/html"},
	}
	stream.ResponseBody = []byte(`<!DOCTYPE html>
<html>
<head>
    <title>HTTP/2 Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .info { background: #f5f5f5; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Welcome to HTTP/2 Server</h1>
    <div class="info">
        <h2>Server Features</h2>
        <ul>
            <li>HTTP/2 Protocol Support</li>
            <li>Multiplexed Streams</li>
            <li>Header Compression (HPACK)</li>
            <li>Flow Control</li>
        </ul>
        <h2>Available Endpoints</h2>
        <ul>
            <li><a href="/">/</a> - This page</li>
            <li><a href="/health">/health</a> - Health check</li>
            <li><a href="/info">/info</a> - Server information</li>
            <li>POST /echo - Echo request body</li>
        </ul>
    </div>
</body>
</html>`)
	return nil
}

func handleHealth(stream *connection.Stream) error {
	stream.ResponseCode = 200
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: "200"},
		{Name: "content-type", Value: "application/json"},
	}
	stream.ResponseBody = []byte(`{"status": "healthy", "version": "1.0.0"}`)
	return nil
}

func handleInfo(stream *connection.Stream) error {
	stream.ResponseCode = 200
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: "200"},
		{Name: "content-type", Value: "application/json"},
	}

	info := fmt.Sprintf(`{
  "protocol": "HTTP/2",
  "features": [
    "multiplexing",
    "header_compression",
    "flow_control",
    "server_push"
  ],
  "streams": {
    "max_concurrent": 100,
    "initial_window_size": 65535
  }
}`)
	stream.ResponseBody = []byte(info)
	return nil
}

func handleEcho(stream *connection.Stream) error {
	stream.ResponseCode = 200
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: "200"},
		{Name: "content-type", Value: "text/plain"},
	}
	stream.ResponseBody = stream.Body
	return nil
}

// StaticFileHandler serves static files
type StaticFileHandler struct {
	RootDir string
}

// NewStaticFileHandler creates a new static file handler
func NewStaticFileHandler(rootDir string) *StaticFileHandler {
	return &StaticFileHandler{
		RootDir: rootDir,
	}
}

// Handle serves a static file
func (h *StaticFileHandler) Handle(stream *connection.Stream) error {
	var path string
	for _, header := range stream.Headers {
		if header.Name == ":path" {
			path = header.Value
			break
		}
	}

	// Security: prevent directory traversal
	if strings.Contains(path, "..") {
		stream.ResponseCode = 403
		stream.ResponseHeaders = []frame.HeaderField{
			{Name: ":status", Value: "403"},
		}
		stream.ResponseBody = []byte("Forbidden")
		return nil
	}

	// In a real implementation, this would read from the filesystem
	stream.ResponseCode = 200
	stream.ResponseHeaders = []frame.HeaderField{
		{Name: ":status", Value: "200"},
		{Name: "content-type", Value: "text/plain"},
	}
	stream.ResponseBody = []byte("Static file content would appear here")
	return nil
}
