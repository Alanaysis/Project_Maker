// Custom Resolver Example
//
// Demonstrates how to use the ZoneBuilder API to construct complex DNS zones
// with multiple record types.
//
// Usage:
//
//	go run examples/custom_resolver/main.go
//	# In another terminal:
//	dig @127.0.0.1 -p 5353 web.example.local A
//	dig @127.0.0.1 -p 5353 web.example.local AAAA
//	dig @127.0.0.1 -p 5353 mail.example.local A
package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropic/dns-server/internal/resolver"
	"github.com/anthropic/dns-server/internal/server"
)

func main() {
	// Create server with custom upstream DNS
	cfg := server.Config{
		ListenAddr:  ":5353",
		UpstreamDNS: "1.1.1.1:53", // Use Cloudflare DNS instead of Google
		CacheSize:   2048,
	}
	srv := server.New(cfg)

	// Use ZoneBuilder to create multi-record zones
	webRecords := resolver.NewZoneBuilder("web.example.local").
		A(net.ParseIP("10.0.1.1")).
		AAAA(net.ParseIP("::1")).
		Build()

	for _, rr := range webRecords {
		srv.Resolver().AddZoneRecord(rr.Name, rr)
	}

	mailRecords := resolver.NewZoneBuilder("mail.example.local").
		A(net.ParseIP("10.0.2.1")).
		Build()

	for _, rr := range mailRecords {
		srv.Resolver().AddZoneRecord(rr.Name, rr)
	}

	// Simple A records
	srv.Resolver().AddARecord("db.example.local", net.ParseIP("10.0.3.1"))

	fmt.Println("=== Custom Resolver Example ===")
	fmt.Println("Upstream DNS: 1.1.1.1:53 (Cloudflare)")
	fmt.Println("Cache size: 2048 entries")
	fmt.Println()
	fmt.Println("Local zone records:")
	fmt.Println("  web.example.local  -> A: 10.0.1.1, AAAA: ::1")
	fmt.Println("  mail.example.local -> A: 10.0.2.1")
	fmt.Println("  db.example.local   -> A: 10.0.3.1")
	fmt.Println()
	fmt.Println("Try:")
	fmt.Println("  dig @127.0.0.1 -p 5353 web.example.local A")
	fmt.Println("  dig @127.0.0.1 -p 5353 web.example.local AAAA")
	fmt.Println("  dig @127.0.0.1 -p 5353 example.com A  # forwarded to Cloudflare")

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
