// Example origin server for testing the CDN service.
// This server simulates a backend origin server that the CDN fetches content from.
//
// Usage:
//   go run origin-server.go
//
// The server listens on port 9090 and serves simple HTML pages.
// It also logs all requests for debugging purposes.

package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

func main() {
	// Create a new HTTP mux
	mux := http.NewServeMux()

	// Handle all requests
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("[Origin] %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

		// Set response headers
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("X-Origin-Server", "example-origin")
		w.Header().Set("X-Request-Time", time.Now().Format(time.RFC3339))

		// Generate response based on path
		var content string
		switch r.URL.Path {
		case "/":
			content = generateHomePage()
		case "/about":
			content = generateAboutPage()
		case "/api/data":
			content = generateAPIData()
		default:
			content = generateGenericPage(r.URL.Path)
		}

		// Write response
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, content)
	})

	// Health check endpoint
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"status": "healthy", "timestamp": "`+time.Now().Format(time.RFC3339)+`"}`)
	})

	// Start server
	addr := ":9090"
	log.Printf("Origin server starting on %s", addr)
	log.Printf("Test URLs:")
	log.Printf("  http://localhost%s/", addr)
	log.Printf("  http://localhost%s/about", addr)
	log.Printf("  http://localhost%s/api/data", addr)
	log.Printf("  http://localhost%s/health", addr)

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

func generateHomePage() string {
	return `<!DOCTYPE html>
<html>
<head>
    <title>Origin Server - Home</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .info { background: #f5f5f5; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Welcome to the Origin Server</h1>
    <div class="info">
        <p>This is the origin server that the CDN fetches content from.</p>
        <p>Try accessing different paths:</p>
        <ul>
            <li><a href="/">/</a> - Home page</li>
            <li><a href="/about">/about</a> - About page</li>
            <li><a href="/api/data">/api/data</a> - API data</li>
            <li><a href="/custom/path">/custom/path</a> - Custom path</li>
        </ul>
    </div>
    <p><small>Generated at: ` + time.Now().Format(time.RFC3339) + `</small></p>
</body>
</html>`
}

func generateAboutPage() string {
	return `<!DOCTYPE html>
<html>
<head>
    <title>Origin Server - About</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>About This Server</h1>
    <p>This is a simple origin server used for testing the CDN service.</p>
    <p>The CDN will fetch content from this server and cache it for subsequent requests.</p>
    <h2>How it works:</h2>
    <ol>
        <li>Client requests content from CDN</li>
        <li>CDN checks its cache</li>
        <li>If cache miss, CDN fetches from this origin server</li>
        <li>CDN caches the response</li>
        <li>CDN returns the content to the client</li>
    </ol>
    <p><small>Generated at: ` + time.Now().Format(time.RFC3339) + `</small></p>
</body>
</html>`
}

func generateAPIData() string {
	return `{
    "status": "success",
    "data": {
        "message": "Hello from the API!",
        "timestamp": "` + time.Now().Format(time.RFC3339) + `",
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
    }
}`
}

func generateGenericPage(path string) string {
	return `<!DOCTYPE html>
<html>
<head>
    <title>Origin Server - ` + path + `</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .path { background: #e8f4f8; padding: 10px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <h1>Dynamic Page</h1>
    <p>You requested: <span class="path">` + path + `</span></p>
    <p>This page was generated dynamically by the origin server.</p>
    <p><small>Generated at: ` + time.Now().Format(time.RFC3339) + `</small></p>
</body>
</html>`
}