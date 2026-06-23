// MQTT Broker - A learning implementation of the MQTT 3.1.1 protocol.
//
// This broker supports:
//   - MQTT 3.1.1 protocol
//   - QoS 0, 1, and 2
//   - Publish/Subscribe with wildcard topics (+, #)
//   - Retained messages
//   - Last Will and Testament (LWT)
//   - Session management
package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/user/mqtt-broker/internal/broker"
)

func main() {
	addr := ":1883"
	if envAddr := os.Getenv("MQTT_ADDR"); envAddr != "" {
		addr = envAddr
	}

	b := broker.New()
	if err := b.Start(addr); err != nil {
		log.Fatalf("Failed to start broker: %v", err)
	}

	fmt.Printf("MQTT Broker started on %s\n", addr)
	fmt.Println("Press Ctrl+C to stop")

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	fmt.Println("\nShutting down...")
	b.Stop()
}
