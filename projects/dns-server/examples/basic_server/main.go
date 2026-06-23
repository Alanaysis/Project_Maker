// Basic DNS Server Example
//
// Demonstrates the minimal setup to run a DNS server with local zone records.
//
// Usage:
//
//	go run examples/basic_server/main.go
//	# In another terminal:
//	dig @127.0.0.1 -p 5353 myapp.local A
package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropic/dns-server/internal/server"
)

func main() {
	// Create server with default configuration
	cfg := server.DefaultConfig()
	srv := server.New(cfg)

	// Add local zone records
	// These are served authoritatively without forwarding to upstream DNS
	srv.Resolver().AddARecord("myapp.local", net.ParseIP("127.0.0.1"))
	srv.Resolver().AddARecord("api.local", net.ParseIP("192.168.1.10"))
	srv.Resolver().AddARecord("api.local", net.ParseIP("192.168.1.11")) // Multiple IPs

	fmt.Println("=== Basic DNS Server Example ===")
	fmt.Println("Local zone records:")
	fmt.Println("  myapp.local  -> 127.0.0.1")
	fmt.Println("  api.local    -> 192.168.1.10, 192.168.1.11")
	fmt.Println()
	fmt.Println("Try: dig @127.0.0.1 -p 5353 myapp.local A")

	// Handle graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigCh
		fmt.Println("\nShutting down...")
		srv.Stop()
	}()

	if err := srv.Start(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}
