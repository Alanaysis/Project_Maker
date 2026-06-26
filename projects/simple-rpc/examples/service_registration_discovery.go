package main

import (
	"context"
	"fmt"
	"log"
	"math/rand"
	"net"
	"sync"
	"time"

	"github.com/simple-rpc/examples"
	"github.com/simple-rpc/internal/client"
	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/loadbalancer"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/server"
	"github.com/simple-rpc/internal/timeout"
)

// This example demonstrates service registration and discovery with multiple instances.
// It shows how multiple server instances register themselves and how clients discover them.
//
// Key concepts demonstrated:
// - Service registration: servers register with the registry on startup
// - Service discovery: clients query the registry for available instances
// - Multiple instances: same service running on different ports
// - Instance health: tracking healthy vs unhealthy instances
func main() {
	fmt.Println("=== Service Registration and Discovery Demo ===")
	fmt.Println()

	// Create shared registry
	reg := registry.NewMemoryRegistry()
	codec := codec.NewJSONCodec()

	// Start multiple server instances
	serverCount := 3
	servers := make([]*server.Server, serverCount)
	addresses := make([]string, serverCount)

	fmt.Printf("Starting %d Calculator service instances:\n", serverCount)
	for i := 0; i < serverCount; i++ {
		listener, err := net.Listen("tcp", "localhost:0")
		if err != nil {
			log.Fatal(err)
		}
		addr := listener.Addr().String()
		listener.Close()

		srv := server.NewServer(addr, codec, reg)
		if err := srv.Register(&examples.Calculator{}); err != nil {
			log.Fatalf("Failed to register Calculator: %v", err)
		}

		servers[i] = srv
		addresses[i] = addr

		go func(a string) {
			fmt.Printf("  [Server %d] Listening on %s\n", i+1, a)
			if err := srv.Start(a); err != nil {
				log.Printf("Server %d error: %v", i+1, err)
			}
		}(addr)

		// Wait for each server to register
		time.Sleep(100 * time.Millisecond)
	}

	// Wait for all registrations to propagate
	time.Sleep(300 * time.Millisecond)

	// Discover services
	fmt.Println("\n--- Service Discovery ---")
	services, _ := reg.ListServices()
	fmt.Printf("Registered services: %v\n", services)

	instances, _ := reg.GetService("Calculator")
	fmt.Printf("Calculator instances: %d\n", len(instances))
	for _, inst := range instances {
		fmt.Printf("  - %s at %s:%d (status: %s)\n", inst.InstanceID, inst.Address, inst.Port, inst.Status)
	}

	// Create clients with different load balancers
	fmt.Println("\n--- Load Balancing Comparison ---")

	balancerNames := []string{"random", "round_robin", "least_connections"}
	for _, balancerName := range balancerNames {
		fmt.Printf("\n[%s Balancer] Making 6 calls:\n", balancerName)

		balancerReg := loadbalancer.NewBalancerRegistry()
		balancer, _ := balancerReg.Get(balancerName)

		config := &client.ClientConfig{
			ServiceName:   "Calculator",
			BalancerName:  balancerName,
			TimeoutConfig: timeout.DefaultConfig(),
			MaxRetries:    3,
		}

		rpcClient := client.NewClient(reg, balancer, codec, config)

		var mu sync.Mutex
		instanceCounts := make(map[string]int)

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		for i := 0; i < 6; i++ {
			addReq := &examples.AddRequest{A: i, B: i}
			addResp := &examples.AddResponse{}
			if err := rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp); err != nil {
				log.Printf("Call %d failed: %v", i, err)
			} else {
				mu.Lock()
				instanceCounts[addResp.Result%3]++
				mu.Unlock()
				fmt.Printf("  Call %d: %d + %d = %d\n", i, addReq.A, addReq.B, addResp.Result)
			}
		}
		cancel()
		rpcClient.Close()
	}

	// Heartbeat demonstration
	fmt.Println("\n--- Heartbeat Test ---")
	instance := instances[0]
	fmt.Printf("Sending heartbeat for %s...\n", instance.InstanceID)
	if err := reg.Heartbeat(instance.InstanceID); err != nil {
		log.Printf("Heartbeat failed: %v", err)
	} else {
		fmt.Printf("Heartbeat sent successfully for %s\n", instance.InstanceID)
	}

	// Cleanup
	fmt.Println("\n--- Cleanup ---")
	for _, srv := range servers {
		srv.Stop()
	}
	reg.Close()

	fmt.Println("\n=== Demo Complete ===")
}
