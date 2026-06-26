// Package main demonstrates index persistence (save and load).
//
// This example shows:
//   1. Building an index from documents
//   2. Saving the index to serialized data
//   3. Loading the index from serialized data
//   4. Verifying that loaded index produces same results
//
// Run with: go run main.go
package main

import (
	"fmt"

	"inverted-index/src"
)

func main() {
	fmt.Println("=== Inverted Index - Persistence Demo ===")
	fmt.Println()

	// Step 1: Build an index
	fmt.Println("Step 1: Building index...")
	builder := invertedindex.NewIndexBuilder()

	docs := []struct {
		id      int
		content string
	}{
		{1, "The quick brown fox jumps over the lazy dog"},
		{2, "A fast red fox runs through the forest"},
		{3, "The lazy dog sleeps in the sun all day"},
		{4, "Foxes are clever animals that live in forests"},
		{5, "Dogs and foxes are both canines"},
	}

	for _, doc := range docs {
		builder.AddDocument(doc.id, doc.content)
	}

	builder.Build()
	originalIndex := builder.GetIndex()

	fmt.Printf("  Built index: %d documents, %d terms\n",
		originalIndex.TotalDocCount(), originalIndex.Size())
	fmt.Println()

	// Step 2: Search with original index
	fmt.Println("Step 2: Searching with original index...")
	searcher := invertedindex.NewSearcher(originalIndex)

	results1, err := searcher.Search("fox", 5)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
		return
	}
	fmt.Printf("  Query 'fox': %d results\n", len(results1))
	for _, r := range results1 {
		fmt.Printf("    Doc %d: score=%.4f\n", r.DocID, r.Score)
	}
	fmt.Println()

	// Step 3: Save the index
	fmt.Println("Step 3: Saving index...")
	data := originalIndex.Save()
	fmt.Printf("  Saved: %d documents, %d terms\n",
		data.Stats.DocCount, data.Stats.TermCount)
	fmt.Printf("  Average doc length: %.2f\n", data.Stats.AvgDocLen)
	fmt.Println()

	// Step 4: Load the index
	fmt.Println("Step 4: Loading index...")
	loadedIndex := invertedindex.Load(data)
	fmt.Printf("  Loaded: %d documents, %d terms\n",
		loadedIndex.TotalDocCount(), loadedIndex.Size())
	fmt.Println()

	// Step 5: Verify loaded index produces same results
	fmt.Println("Step 5: Verifying loaded index...")
	searcher2 := invertedindex.NewSearcher(loadedIndex)

	results2, err := searcher2.Search("fox", 5)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
		return
	}
	fmt.Printf("  Query 'fox': %d results\n", len(results2))
	for _, r := range results2 {
		fmt.Printf("    Doc %d: score=%.4f\n", r.DocID, r.Score)
	}
	fmt.Println()

	// Compare results
	if len(results1) == len(results2) {
		match := true
		for i := range results1 {
			if results1[i].DocID != results2[i].DocID ||
				mathAbs(results1[i].Score-results2[i].Score) > 1e-9 {
				match = false
				break
			}
		}
		if match {
			fmt.Println("  ✅ Results match! Index persistence verified.")
		} else {
			fmt.Println("  ❌ Results differ!")
		}
	} else {
		fmt.Println("  ❌ Different number of results!")
	}
	fmt.Println()

	// Step 6: Show index stats
	fmt.Println("Step 6: Index statistics")
	fmt.Printf("  Total terms: %d\n", loadedIndex.Size())
	fmt.Printf("  Total documents: %d\n", loadedIndex.TotalDocCount())
	fmt.Printf("  Terms: %v\n", loadedIndex.Terms())
}

func mathAbs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
