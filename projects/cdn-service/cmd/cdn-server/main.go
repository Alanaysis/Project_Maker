package main

import (
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"cdn-service/pkg/server"
)

func main() {
	// Parse command line flags
	addr := flag.String("addr", ":8080", "Server address")
	originURL := flag.String("origin", "http://localhost:9090", "Origin server URL")
	cacheTTL := flag.Duration("ttl", 1*time.Hour, "Default cache TTL")
	adminToken := flag.String("admin-token", "", "Bearer token for admin endpoints (required)")
	flag.Parse()

	// Create server configuration
	config := server.ServerConfig{
		Addr:           *addr,
		ReadTimeout:    30 * time.Second,
		WriteTimeout:   30 * time.Second,
		MaxHeaderBytes: 1 << 20,
		DefaultTTL:     *cacheTTL,
		OriginURL:      *originURL,
		AdminToken:     *adminToken,
	}

	// Create and start server
	srv := server.NewServer(config)

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("Received signal: %v", sig)
		if err := srv.Stop(); err != nil {
			log.Printf("Error stopping server: %v", err)
		}
		os.Exit(0)
	}()

	// Start server
	log.Printf("Starting CDN server on %s", config.Addr)
	log.Printf("Origin server: %s", config.OriginURL)
	log.Printf("Cache TTL: %v", config.DefaultTTL)

	if err := srv.Start(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}