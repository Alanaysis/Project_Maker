// DNS Server - A simple DNS server implementation in Go.
//
// This server listens for DNS queries on UDP, resolves them through
// a configurable upstream DNS server, and caches the results.
//
// Usage:
//
//	go run cmd/server/main.go [flags]
//
// Flags:
//
//	-addr string      Listen address (default ":5353")
//	-upstream string  Upstream DNS server (default "8.8.8.8:53")
//	-cache int        Max cache entries (default 1024)
package main

import (
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropic/dns-server/internal/server"
)

func main() {
	// Parse command line flags
	addr := flag.String("addr", ":5353", "UDP address to listen on")
	upstream := flag.String("upstream", "8.8.8.8:53", "Upstream DNS server address")
	cacheSize := flag.Int("cache", 1024, "Maximum number of cache entries")
	flag.Parse()

	// Configure logging
	log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds)
	log.SetPrefix("[dns] ")

	// Print banner
	fmt.Println("========================================")
	fmt.Println("  DNS Server - Educational Implementation")
	fmt.Println("========================================")
	fmt.Printf("  Listen:    %s\n", *addr)
	fmt.Printf("  Upstream:  %s\n", *upstream)
	fmt.Printf("  Cache Max: %d entries\n", *cacheSize)
	fmt.Println("========================================")

	// Create server configuration
	cfg := server.Config{
		ListenAddr:  *addr,
		UpstreamDNS: *upstream,
		CacheSize:   *cacheSize,
	}

	// Create and configure the server
	srv := server.New(cfg)

	// Add some example local zone records
	// These will be served authoritatively without forwarding to upstream
	srv.Resolver().AddARecord("localhost.dns", net.ParseIP("127.0.0.1"))
	srv.Resolver().AddARecord("test.local", net.ParseIP("192.168.1.100"))

	log.Println("[main] local zone records configured:")
	log.Println("[main]   localhost.dns -> 127.0.0.1")
	log.Println("[main]   test.local -> 192.168.1.100")

	// Handle graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigCh
		log.Printf("[main] received signal %v, shutting down...", sig)
		srv.Stop()
	}()

	// Start the server (blocks until stopped)
	log.Println("[main] starting DNS server...")
	if err := srv.Start(); err != nil {
		log.Fatalf("[main] server error: %v", err)
	}

	log.Println("[main] server stopped")
}
