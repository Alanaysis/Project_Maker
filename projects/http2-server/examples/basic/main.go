// Example: Basic HTTP/2 Server
//
// This example demonstrates how to use the HTTP/2 server library
// to create a simple server with multiple endpoints.
package main

import (
	"fmt"
	"log"
	"net"
	"os"

	"github.com/anthropic/http2-server/internal/connection"
	"github.com/anthropic/http2-server/internal/frame"
)

func main() {
	// Create a simple handler
	handler := func(stream *connection.Stream) error {
		// Extract path from headers
		var path string
		for _, h := range stream.Headers {
			if h.Name == ":path" {
				path = h.Value
				break
			}
		}

		log.Printf("Request: %s", path)

		// Set response based on path
		switch path {
		case "/":
			stream.ResponseCode = 200
			stream.ResponseHeaders = []frame.HeaderField{
				{Name: ":status", Value: "200"},
				{Name: "content-type", Value: "text/plain"},
			}
			stream.ResponseBody = []byte("Hello from HTTP/2!")

		case "/json":
			stream.ResponseCode = 200
			stream.ResponseHeaders = []frame.HeaderField{
				{Name: ":status", Value: "200"},
				{Name: "content-type", Value: "application/json"},
			}
			stream.ResponseBody = []byte(`{"message": "Hello from HTTP/2!", "protocol": "h2"}`)

		default:
			stream.ResponseCode = 404
			stream.ResponseHeaders = []frame.HeaderField{
				{Name: ":status", Value: "404"},
				{Name: "content-type", Value: "text/plain"},
			}
			stream.ResponseBody = []byte("Not Found")
		}

		return nil
	}

	// Create listener (plain TCP for this example)
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatalf("Failed to create listener: %v", err)
	}
	defer listener.Close()

	fmt.Println("HTTP/2 example server listening on :8080")
	fmt.Println("Note: This example uses plain TCP, not TLS")
	fmt.Println("For production, use TLS with HTTP/2")

	// Accept connections
	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Printf("Failed to accept connection: %v", err)
			continue
		}

		go handleConnection(conn, handler)
	}
}

func handleConnection(conn net.Conn, handler connection.RequestHandler) {
	defer conn.Close()

	log.Printf("New connection from %s", conn.RemoteAddr())

	// Create HTTP/2 connection
	http2Conn := connection.NewConnection(conn, handler)

	// Start processing
	if err := http2Conn.Start(); err != nil {
		log.Printf("Connection error: %v", err)
	}

	log.Printf("Connection closed from %s", conn.RemoteAddr())
}

func init() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.SetOutput(os.Stdout)

	fmt.Println("╔═══════════════════════════════════════════════════════════╗")
	fmt.Println("║           HTTP/2 Server - Basic Example                   ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   This example demonstrates:                              ║")
	fmt.Println("║   • Simple HTTP/2 server setup                            ║")
	fmt.Println("║   • Request routing                                       ║")
	fmt.Println("║   • Response generation                                   ║")
	fmt.Println("║                                                           ║")
	fmt.Println("║   Endpoints:                                              ║")
	fmt.Println("║     GET /        - Plain text response                    ║")
	fmt.Println("║     GET /json    - JSON response                          ║")
	fmt.Println("║     GET /*       - 404 Not Found                          ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════╝")
}
