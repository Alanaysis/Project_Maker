// Package bloomfilter_test contains example programs demonstrating Bloom filter usage.
package main

import (
	"fmt"
	"math/rand"

	"bloom-filter/src"
)

func main() {
	fmt.Println("=== Counting Bloom Filter Demo ===")
	fmt.Println()

	// Create a counting Bloom filter
	cbf, err := bloomfilter.NewCountingBloomSimple(5000, 0.01)
	if err != nil {
		panic(err)
	}

	fmt.Printf("Created: %s\n", cbf.Info())
	fmt.Println()

	// Insert a set of elements
	words := []string{
		"the", "quick", "brown", "fox", "jumps",
		"over", "the", "lazy", "dog", "and",
		"the", "cat", "sat", "on", "the", "mat",
	}

	fmt.Println("Inserting words:")
	for _, word := range words {
		cbf.AddString(word)
		fmt.Printf("  + '%s'\n", word)
	}
	fmt.Printf("\nFilter state: %s\n", cbf.Info())

	// Verify all words are found
	fmt.Println("\nVerifying all words:")
	for _, word := range words {
		if cbf.ContainsString(word) {
			fmt.Printf("  '%s': FOUND\n", word)
		} else {
			fmt.Printf("  '%s': NOT FOUND (ERROR!)\n", word)
		}
	}

	// Remove some words
	fmt.Println("\nRemoving 'fox' and 'dog'...")
	cbf.Remove("fox")
	cbf.Remove("dog")

	fmt.Println("\nAfter removal:")
	allWords := []string{"the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "cat", "mat"}
	for _, word := range allWords {
		found := cbf.ContainsString(word)
		shouldBeFound := word != "fox" && word != "dog"
		status := "OK"
		if found != shouldBeFound {
			status = "ERROR"
		}
		fmt.Printf("  '%s': %v (expected: %v) [%s]\n", word, found, shouldBeFound, status)
	}

	// Test with duplicate words (counting Bloom filter tracks counts)
	fmt.Println("\n--- Duplicate handling ---")
	cbf2, _ := bloomfilter.NewCountingBloomSimple(1000, 0.01)

	duplicates := []string{"a", "b", "a", "c", "a", "b", "a"}
	for _, word := range duplicates {
		cbf2.AddString(word)
	}

	// Check that 'a' is still found (even after removing one instance)
	fmt.Printf("After inserting a,b,a,c,a,b,a:\n")
	fmt.Printf("  'a' found: %v\n", cbf2.ContainsString("a"))
	fmt.Printf("  'b' found: %v\n", cbf2.ContainsString("b"))
	fmt.Printf("  'c' found: %v\n", cbf2.ContainsString("c"))
	fmt.Printf("  'd' found: %v\n", cbf2.ContainsString("d"))

	// Remove 'a' once - should still be found
	fmt.Println("\nRemoving 'a' once:")
	cbf2.Remove("a")
	fmt.Printf("  'a' found: %v (should be true, still has count > 0)\n", cbf2.ContainsString("a"))

	// Remove 'a' remaining times
	fmt.Println("Removing 'a' three more times:")
	for i := 0; i < 3; i++ {
		cbf2.Remove("a")
	}
	fmt.Printf("  'a' found: %v (should be false, all counts removed)\n", cbf2.ContainsString("a"))

	// Stress test: many insertions and deletions
	fmt.Println("\n--- Stress test: random insert/delete/verify ---")
	rng := rand.New(rand.NewSource(42))
	stressCBF, _ := bloomfilter.NewCountingBloomSimple(10000, 0.01)

	// Insert 1000 elements
	elements := make([]string, 1000)
	for i := 0; i < 1000; i++ {
		elements[i] = fmt.Sprintf("elem_%d", rng.Intn(5000))
		stressCBF.AddString(elements[i])
	}

	// Delete 500 elements
	for i := 0; i < 500; i++ {
		stressCBF.Remove(elements[i])
	}

	// Verify: first 500 should NOT be found, last 500 should be found
	correct := 0
	total := 1000
	for i := 0; i < 500; i++ {
		if stressCBF.ContainsString(elements[i]) {
			// False positive (expected, counting BF still has some FP)
		} else {
			correct++ // Correctly removed
		}
	}
	for i := 500; i < 1000; i++ {
		if stressCBF.ContainsString(elements[i]) {
			correct++ // Correctly found
		}
	}

	fmt.Printf("Stress test: %d/%d correct (%.1f%%)\n", correct, total, float64(correct)/float64(total)*100)
	fmt.Printf("Final state: %s\n", stressCBF.Info())
}
