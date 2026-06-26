// Package main demonstrates node join and leave operations in a Chord DHT.
//
// This example shows:
// 1. Nodes joining the ring
// 2. Key distribution across nodes
// 3. Nodes leaving the ring
// 4. Key migration during departure
// 5. Ring recovery after node departure
package main

import (
	"fmt"
	"dht/src"
)

func main() {
	fmt.Println("=== Chord DHT - Node Join/Leave Demo ===")
	fmt.Println()
	
	// Create a new ring simulator
	sim := chord.NewRingSimulator()
	
	// Phase 1: Join nodes
	fmt.Println("Phase 1: Joining nodes")
	fmt.Println("----------------------")
	
	joinNodes := []string{
		"node-10.0.0.1",
		"node-10.0.0.5",
		"node-10.0.0.10",
		"node-10.0.0.15",
	}
	
	for _, addr := range joinNodes {
		sim.JoinNode(addr)
	}
	sim.PrintStatus()
	
	// Store some data
	fmt.Println("Storing data:")
	keys := []string{"key:a", "key:b", "key:c", "key:d", "key:e", "key:f", "key:g", "key:h"}
	for _, k := range keys {
		sim.StoreKey(k, "value-"+k)
		fmt.Printf("  Stored: %s = value-%s\n", k, k[4:])
	}
	sim.PrintStatus()
	
	// Phase 2: Join more nodes
	fmt.Println("\nPhase 2: Adding more nodes")
	fmt.Println("--------------------------")
	
	moreNodes := []string{
		"node-10.0.0.3",
		"node-10.0.0.7",
		"node-10.0.0.12",
	}
	
	for _, addr := range moreNodes {
		sim.JoinNode(addr)
	}
	sim.PrintStatus()
	
	// Phase 3: Nodes leave
	fmt.Println("\nPhase 3: Nodes leaving")
	fmt.Println("----------------------")
	
	leaveNodes := []string{
		"node-10.0.0.5",
		"node-10.0.0.15",
	}
	
	for _, addr := range leaveNodes {
		fmt.Printf("\nRemoving %s:\n", addr)
		sim.LeaveNode(addr)
	}
	
	sim.PrintStatus()
	
	// Show key migrations
	sim.PrintMigrations()
	
	// Verify data integrity
	fmt.Println("Verifying data after departures:")
	allFound := true
	for _, k := range keys {
		value, found := sim.RetrieveKey(k)
		if found {
			fmt.Printf("  %s = %s (OK)\n", k, value)
		} else {
			fmt.Printf("  %s = NOT FOUND (MISSING!)\n", k)
			allFound = false
		}
	}
	
	if allFound {
		fmt.Println("\nAll data preserved! Data migration successful.")
	}
	
	// Final verification
	fmt.Println("\nFinal ring integrity check:")
	sim.Verify()
	
	fmt.Println("\n=== Demo Complete ===")
}
