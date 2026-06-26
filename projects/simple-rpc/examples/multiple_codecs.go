package main

import (
	"bytes"
	"context"
	"encoding/json"
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

// This example demonstrates how different codecs work in the RPC framework.
// It shows JSON, Gob, and Protobuf codecs with their respective trade-offs.
//
// Key concepts:
// - Codec interface: unified API for all serialization formats
// - Codec negotiation: client and server must agree on a codec
// - Performance comparison: different codecs have different overhead
func main() {
	fmt.Println("=== Multiple Codecs Demo ===")
	fmt.Println()

	// Create shared registry
	reg := registry.NewMemoryRegistry()

	// Get an available port
	listener, err := net.Listen("tcp", "localhost:0")
	if err != nil {
		log.Fatal(err)
	}
	addr := listener.Addr().String()
	listener.Close()

	// Test each codec
	codecs := []struct {
		name  string
		codec codec.Codec
	}{
		{"JSON", codec.NewJSONCodec()},
		{"Gob", codec.NewGobCodec()},
		{"Protobuf", codec.NewProtobufCodec()},
	}

	for _, tc := range codecs {
		fmt.Printf("--- Testing %s Codec ---\n", tc.name)

		// Create server with this codec
		srv := server.NewServer(addr, tc.codec, reg)
		if err := srv.Register(&examples.Calculator{}); err != nil {
			log.Printf("Failed to register Calculator: %v", err)
			continue
		}

		go func() {
			srv.Start(addr)
		}()

		time.Sleep(150 * time.Millisecond)

		// Create client with same codec
		balancer := loadbalancer.NewRoundRobinBalancer()
		config := &client.ClientConfig{
			ServiceName:   "Calculator",
			BalancerName:  "round_robin",
			TimeoutConfig: timeout.DefaultConfig(),
			MaxRetries:    3,
		}
		rpcClient := client.NewClient(reg, balancer, tc.codec, config)

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)

		// Test with JSON-serializable data
		addReq := &examples.AddRequest{A: 10, B: 20}
		addResp := &examples.AddResponse{}

		start := time.Now()
		err := rpcClient.Call(ctx, "Calculator", "Add", addReq, addResp)
		elapsed := time.Since(start)

		cancel()
		rpcClient.Close()

		if err != nil {
			fmt.Printf("  Call failed: %v\n", err)
		} else {
			fmt.Printf("  Result: %d + %d = %d (took %v)\n", addReq.A, addReq.B, addResp.Result, elapsed)
		}

		// Show codec overhead
		showCodecOverhead(tc.name, tc.codec)

		srv.Stop()
		fmt.Println()
	}

	reg.Close()
	fmt.Println("=== Demo Complete ===")
}

// showCodecOverhead demonstrates the serialization overhead of each codec
func showCodecOverhead(name string, c codec.Codec) {
	// Create test data
	testData := map[string]interface{}{
		"service": "Calculator",
		"method":  "Add",
		"args":    map[string]int{"a": 10, "b": 20},
		"timestamp": time.Now().UnixNano(),
	}

	// Measure encoding size
	var buf bytes.Buffer
	start := time.Now()
	if err := c.Encode(&buf, testData); err != nil {
		log.Printf("Encode error: %v", err)
		return
	}
	encodeTime := time.Since(start)

	// Measure decoding time
	var decoded map[string]interface{}
	start = time.Now()
	if err := c.Decode(&buf, &decoded); err != nil {
		log.Printf("Decode error: %v", err)
		return
	}
	decodeTime := time.Since(start)

	fmt.Printf("  Overhead: %d bytes | Encode: %v | Decode: %v\n",
		buf.Len(), encodeTime, decodeTime)

	// Show raw output for JSON (human-readable)
	if name == "JSON" {
		fmt.Printf("  Raw output: %s\n", buf.String())
	}
}
