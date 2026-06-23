package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/container-orchestrator/pkg/api"
	"github.com/container-orchestrator/pkg/manager"
)

func main() {
	fmt.Println("Starting Container Orchestrator...")

	// Create manager
	mgr := manager.NewManager()

	// Start manager
	mgr.Start()

	// Create API server
	server := api.NewServer(mgr)

	// Handle graceful shutdown
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigCh
		fmt.Println("\nShutting down...")
		mgr.Stop()
		os.Exit(0)
	}()

	// Start API server
	addr := ":8080"
	if port := os.Getenv("PORT"); port != "" {
		addr = ":" + port
	}

	fmt.Printf("API server listening on %s\n", addr)
	if err := server.Start(addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
