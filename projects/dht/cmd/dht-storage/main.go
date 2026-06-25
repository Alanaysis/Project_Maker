package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/dht-chord/internal"
)

func main() {
	// Command line flags
	serverAddr := flag.String("server", "localhost:8000", "DHT server address")
	action := flag.String("action", "demo", "Action: put, get, delete, list, demo")
	key := flag.String("key", "", "Key for put/get/delete")
	value := flag.String("value", "", "Value for put")
	ttl := flag.Int64("ttl", 0, "Time to live in seconds (0 = no expiry)")
	flag.Parse()

	fmt.Println("=== Distributed Storage Client ===")

	// Create network node for client
	node := internal.NewNetworkNode("localhost:0") // Random port
	if err := node.Start(); err != nil {
		log.Fatalf("Failed to start client node: %v", err)
	}
	defer node.Stop()

	// Connect to server
	if err := node.Ping(*serverAddr); err != nil {
		log.Fatalf("Failed to connect to server: %v", err)
	}
	fmt.Printf("Connected to server: %s\n", *serverAddr)

	// Create distributed storage
	storage := internal.NewDistributedStorage(node, 3)

	switch *action {
	case "put":
		if *key == "" || *value == "" {
			log.Fatal("Key and value required for put action")
		}
		if err := storage.Put(*key, *value, *ttl); err != nil {
			log.Fatalf("Failed to put: %v", err)
		}
		fmt.Printf("Stored: %s = %s\n", *key, *value)

	case "get":
		if *key == "" {
			log.Fatal("Key required for get action")
		}
		value, err := storage.Get(*key)
		if err != nil {
			log.Fatalf("Failed to get: %v", err)
		}
		fmt.Printf("Got: %s = %s\n", *key, value)

	case "delete":
		if *key == "" {
			log.Fatal("Key required for delete action")
		}
		if err := storage.Delete(*key); err != nil {
			log.Fatalf("Failed to delete: %v", err)
		}
		fmt.Printf("Deleted: %s\n", *key)

	case "list":
		keys := storage.List()
		if len(keys) == 0 {
			fmt.Println("No keys in storage")
		} else {
			fmt.Printf("Keys in storage (%d):\n", len(keys))
			for _, k := range keys {
				item, _ := storage.GetItem(k)
				if item != nil {
					fmt.Printf("  %s = %s\n", k, item.Value)
				}
			}
		}

	case "demo":
		runDemo(storage)

	default:
		fmt.Printf("Unknown action: %s\n", *action)
		os.Exit(1)
	}
}

func runDemo(storage *internal.DistributedStorage) {
	fmt.Println("\n--- Distributed Storage Demo ---")

	// Store some data
	testData := map[string]string{
		"user:1":    "Alice",
		"user:2":    "Bob",
		"user:3":    "Charlie",
		"config:1":  "debug=true",
		"config:2":  "log_level=info",
		"session:1": "active",
	}

	fmt.Println("\n1. Storing key-value pairs...")
	for key, value := range testData {
		if err := storage.Put(key, value, 0); err != nil {
			log.Printf("Failed to store %s: %v", key, err)
		} else {
			fmt.Printf("   Stored: %s = %s\n", key, value)
		}
	}

	// Retrieve data
	fmt.Println("\n2. Retrieving key-value pairs...")
	for key := range testData {
		value, err := storage.Get(key)
		if err != nil {
			log.Printf("Failed to get %s: %v", key, err)
		} else {
			fmt.Printf("   Got: %s = %s\n", key, value)
		}
	}

	// Delete a key
	fmt.Println("\n3. Deleting key 'session:1'...")
	if err := storage.Delete("session:1"); err != nil {
		log.Printf("Failed to delete: %v", err)
	} else {
		fmt.Println("   Deleted successfully")
	}

	// Verify deletion
	fmt.Println("\n4. Verifying deletion...")
	_, err := storage.Get("session:1")
	if err != nil {
		fmt.Println("   Key 'session:1' not found (expected)")
	} else {
		fmt.Println("   Key 'session:1' still exists (unexpected)")
	}

	// Show stats
	fmt.Println("\n5. Storage statistics:")
	stats := storage.Stats()
	for k, v := range stats {
		fmt.Printf("   %s: %v\n", k, v)
	}

	// Batch operations
	fmt.Println("\n6. Batch operations...")
	batchData := map[string]string{
		"batch:1": "value1",
		"batch:2": "value2",
		"batch:3": "value3",
	}
	if err := storage.BatchPut(batchData, 60); err != nil {
		log.Printf("Batch put failed: %v", err)
	} else {
		fmt.Printf("   Stored %d items with TTL=60s\n", len(batchData))
	}

	keys := []string{"batch:1", "batch:2", "batch:3"}
	results, err := storage.BatchGet(keys)
	if err != nil {
		log.Printf("Batch get failed: %v", err)
	} else {
		fmt.Printf("   Retrieved %d items\n", len(results))
		for k, v := range results {
			fmt.Printf("     %s = %s\n", k, v)
		}
	}

	fmt.Println("\n--- Demo Complete ---")
}
