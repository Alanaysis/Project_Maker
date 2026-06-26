// Package main demonstrates key migration during node join/leave operations.
//
// This example shows:
// 1. Initial key distribution
// 2. Key migration when a node leaves
// 3. Key redistribution when new nodes join
// 4. Verification of data integrity throughout
package main

import (
	"fmt"
	"dht/src"
)

func main() {
	fmt.Println("=== Chord DHT - Key Migration Demo ===")
	fmt.Println()
	
	// Create a new ring simulator
	sim := chord.NewRingSimulator()
	
	// Phase 1: Start with few nodes
	fmt.Println("Phase 1: Initial setup with 2 nodes")
	fmt.Println("------------------------------------")
	
	nodes1 := []string{"node-10.0.0.1", "node-10.0.0.100"}
	for _, addr := range nodes1 {
		sim.JoinNode(addr)
	}
	sim.PrintStatus()
	
	// Store keys - all will be on one node (or split between two)
	fmt.Println("Storing 20 keys:")
	for i := 0; i < 20; i++ {
		key := fmt.Sprintf("data-%d", i)
		sim.StoreKey(key, fmt.Sprintf("value-%d", i))
	}
	sim.PrintStatus()
	
	// Phase 2: Add middle node
	fmt.Println("\nPhase 2: Adding a node in the middle")
	fmt.Println("-------------------------------------")
	
	sim.JoinNode("node-10.0.0.50")
	sim.PrintStatus()
	sim.PrintMigrations()
	
	// Phase 3: Add more nodes
	fmt.Println("\nPhase 3: Adding more nodes")
	fmt.Println("---------------------------")
	
	moreNodes := []string{
		"node-10.0.0.25",
		"node-10.0.0.75",
		"node-10.0.0.150",
	}
	
	for _, addr := range moreNodes {
		sim.JoinNode(addr)
	}
	sim.PrintStatus()
	sim.PrintMigrations()
	
	// Phase 4: Remove a node
	fmt.Println("\nPhase 4: Removing a node")
	fmt.Println("-------------------------")
	
	sim.LeaveNode("node-10.0.0.25")
	sim.PrintStatus()
	sim.PrintMigrations()
	
	// Verify all data
	fmt.Println("\nVerifying all data:")
	allFound := true
	for i := 0; i < 20; i++ {
		key := fmt.Sprintf("data-%d", i)
		value, found := sim.RetrieveKey(key)
		if found {
			fmt.Printf("  %s = %s (OK)\n", key, value)
		} else {
			fmt.Printf("  %s = NOT FOUND (MISSING!)\n", key)
			allFound = false
		}
	}
	
	if allFound {
		fmt.Println("\nAll data preserved through migrations!")
	}
	
	// Final integrity check
	fmt.Println("\nFinal ring integrity check:")
	sim.Verify()
	
	fmt.Println("\n=== Demo Complete ===")
}
