package main

import (
	"fmt"
	"log"
	"os"

	lsm "github.com/lsm-tree/internal"
)

func main() {
	dataDir := "/tmp/lsm-tree-demo"
	defer os.RemoveAll(dataDir)

	fmt.Println("=== LSM Tree Storage Engine Demo ===")
	fmt.Println()

	// Create engine
	engine, err := lsm.NewLSMEngine(dataDir, 1024) // 1KB MemTable size
	if err != nil {
		log.Fatalf("Failed to create engine: %v", err)
	}
	defer engine.Close()

	// === Basic Put/Get ===
	fmt.Println("--- Basic Put/Get Operations ---")
	keys := []string{"apple", "banana", "cherry", "date", "elderberry"}
	values := []string{"red", "yellow", "red", "brown", "purple"}

	for i, key := range keys {
		if err := engine.Put([]byte(key), []byte(values[i])); err != nil {
			log.Fatalf("Put failed: %v", err)
		}
		fmt.Printf("  PUT %s = %s\n", key, values[i])
	}

	fmt.Println()
	for _, key := range keys {
		val, err := engine.Get([]byte(key))
		if err != nil {
			log.Fatalf("Get failed: %v", err)
		}
		fmt.Printf("  GET %s = %s\n", key, val)
	}

	// === Update ===
	fmt.Println("\n--- Update Operation ---")
	if err := engine.Put([]byte("apple"), []byte("green")); err != nil {
		log.Fatalf("Put failed: %v", err)
	}
	fmt.Println("  PUT apple = green (update)")

	val, _ := engine.Get([]byte("apple"))
	fmt.Printf("  GET apple = %s\n", val)

	// === Delete ===
	fmt.Println("\n--- Delete Operation ---")
	if err := engine.Delete([]byte("banana")); err != nil {
		log.Fatalf("Delete failed: %v", err)
	}
	fmt.Println("  DELETE banana")

	val, _ = engine.Get([]byte("banana"))
	if val == nil {
		fmt.Println("  GET banana = (not found)")
	} else {
		fmt.Printf("  GET banana = %s\n", val)
	}

	// === Flush to SSTable ===
	fmt.Println("\n--- Flush to SSTable ---")
	// Write enough data to trigger a flush
	for i := 0; i < 100; i++ {
		key := fmt.Sprintf("key-%04d", i)
		value := fmt.Sprintf("value-%04d", i*10)
		if err := engine.Put([]byte(key), []byte(value)); err != nil {
			log.Fatalf("Put failed: %v", err)
		}
	}
	fmt.Println("  Wrote 100 key-value pairs to trigger flush")

	stats := engine.Stats()
	fmt.Printf("  MemTable: %d entries, %d bytes\n", stats.MemTableSize, stats.MemTableBytes)
	fmt.Printf("  SSTables by level: %v\n", stats.SSTableCount)

	// Verify data survives flush
	fmt.Println("\n--- Verify data after flush ---")
	for i := 0; i < 100; i++ {
		key := fmt.Sprintf("key-%04d", i)
		expected := fmt.Sprintf("value-%04d", i*10)
		val, err := engine.Get([]byte(key))
		if err != nil {
			log.Fatalf("Get failed: %v", err)
		}
		if string(val) != expected {
			log.Fatalf("Mismatch: expected %s, got %s", expected, val)
		}
	}
	fmt.Println("  All 100 entries verified successfully!")

	// Also verify original keys
	for _, key := range keys {
		if key == "banana" {
			continue // was deleted
		}
		val, err := engine.Get([]byte(key))
		if err != nil {
			log.Fatalf("Get failed: %v", err)
		}
		expected := values[indexOf(keys, key)]
			if key == "apple" {
				expected = "green"
			}
		if string(val) != expected {
			log.Fatalf("Mismatch for %s: expected %s, got %s", key, expected, val)
		}
	}
	fmt.Println("  Original entries verified (excluding deleted 'banana')")

	fmt.Println("\n=== Demo Complete ===")
}

func indexOf(slice []string, item string) int {
	for i, s := range slice {
		if s == item {
			return i
		}
	}
	return -1
}
