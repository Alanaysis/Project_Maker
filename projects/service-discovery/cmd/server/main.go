// Service Discovery Server
//
// This is the entry point for the service discovery system.
// It starts an HTTP API server that provides service registration,
// discovery, health checking, and load balancing.
//
// Usage:
//
//	service-discovery [-addr ":8500"]
//
// API Endpoints:
//
//	POST   /register     - Register a service
//	DELETE /deregister    - Deregister a service
//	GET    /services      - List all services
//	GET    /services/{name} - Get services by name
//	GET    /discover?name=X - Discover services
//	GET    /choose?name=X   - Choose a service (load balanced)
//	GET    /health         - Health check
package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropic/service-discovery/internal/server"
	"github.com/anthropic/service-discovery/internal/store"
)

func main() {
	addr := flag.String("addr", ":8500", "HTTP listen address")
	flag.Parse()

	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Printf("[main] starting service discovery server on %s", *addr)

	// Create in-memory store (in production, use etcd)
	s := store.NewMemStore()
	defer s.Close()

	// Create and start server
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	srv := server.New(s, server.Config{ListenAddr: *addr})
	if err := srv.Start(ctx); err != nil {
		log.Fatalf("[main] failed to start server: %v", err)
	}

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	<-sigCh
	log.Println("[main] shutting down...")

	srv.Stop()
	log.Println("[main] server stopped")
}
