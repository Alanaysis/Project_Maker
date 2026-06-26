package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"time"

	"github.com/simple-rpc/examples"
	"github.com/simple-rpc/internal/client"
	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/server"
	"github.com/simple-rpc/internal/timeout"
)

// This example demonstrates a basic RPC call flow:
// 1. Create and start a server with a registered service
// 2. Create a client that discovers the service
// 3. Call the remote method
// 4. Receive and process the response
//
// This is the simplest possible RPC example, showing the core client-server interaction.
func main() {
	fmt.Println("=== Basic RPC Call Demo ===")
	fmt.Println()

	// Step 1: Create a shared registry (in real systems, this would be a separate service)
	reg := registry.NewMemoryRegistry()

	// Step 2: Create a JSON codec for serialization
	codec := codec.NewJSONCodec()

	// Step 3: Get an available port for the server
	listener, err := net.Listen("tcp", "localhost:0")
	if err != nil {
		log.Fatal(err)
	}
	addr := listener.Addr().String()
	listener.Close()

	// Step 4: Create and register the service
	srv := server.NewServer(addr, codec, reg)
	if err := srv.Register(&examples.Calculator{}); err != nil {
		log.Fatalf("Failed to register service: %v", err)
	}
	fmt.Printf("[Server] Registering Calculator service on %s\n", addr)

	// Step 5: Start the server in a goroutine
	go func() {
		if err := srv.Start(addr); err != nil {
			log.Printf("Server error: %v", err)
		}
	}()

	// Give server time to start and register
	time.Sleep(200 * time.Millisecond)

	// Step 6: Create a client with load balancing
	balancer := loadbalancer.NewRoundRobinBalancer()
	config := &client.ClientConfig{
		ServiceName:   "Calculator",
		BalancerName:  "round_robin",
		TimeoutConfig: timeout.DefaultConfig(),
		MaxRetries:    3,
	}
	rpcClient := client.NewClient(reg, balancer, codec, config)
	defer rpcClient.Close()

	// Step 7: Make RPC calls
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Add operation
	fmt.Println("\n--- Add Operation ---")
	addReq := &examples.AddRequest{A: 10, B: 20}
	addResp := &examples.AddResponse{}
	if err := rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp); err != nil {
		log.Printf("Add failed: %v", err)
	} else {
		fmt.Printf("  %d + %d = %d\n", addReq.A, addReq.B, addResp.Result)
	}

	// Multiply operation
	fmt.Println("\n--- Multiply Operation ---")
	mulReq := &examples.MultiplyRequest{A: 5, B: 6}
	mulResp := &examples.MultiplyResponse{}
	if err := rpcClient.Call(ctx, "Calculator", "Multiply", mulReq, mulResp); err != nil {
		log.Printf("Multiply failed: %v", err)
	} else {
		fmt.Printf("  %d * %d = %d\n", mulReq.A, mulReq.B, mulResp.Result)
	}

	// Step 8: Verify service registration
	instances, _ := reg.GetService("Calculator")
	fmt.Printf("\n[Discovery] Found %d instance(s) for Calculator service\n", len(instances))

	fmt.Println("\n=== Demo Complete ===")
}
