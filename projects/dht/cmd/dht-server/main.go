package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/dht-chord/internal"
)

func main() {
	// Command line flags
	addr := flag.String("addr", "localhost:8000", "Server address")
	bootstrap := flag.String("bootstrap", "", "Bootstrap node addresses (comma-separated)")
	flag.Parse()

	fmt.Println("=== DHT Server ===")
	fmt.Printf("Address: %s\n", *addr)

	// Create network node
	node := internal.NewNetworkNode(*addr)

	// Start HTTP server
	if err := node.Start(); err != nil {
		log.Fatalf("Failed to start node: %v", err)
	}
	defer node.Stop()

	// Create discovery manager
	config := internal.DefaultDiscoveryConfig()
	if *bootstrap != "" {
		config.BootstrapAddrs = strings.Split(*bootstrap, ",")
	}

	discovery := internal.NewDiscovery(node, config)
	if err := discovery.Start(); err != nil {
		log.Printf("Discovery start failed: %v", err)
	}
	defer discovery.Stop()

	fmt.Println("Server started. Press Ctrl+C to stop.")

	// Wait for interrupt signal
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	fmt.Println("\nShutting down...")
}
