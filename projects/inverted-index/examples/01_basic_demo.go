// Package main demonstrates basic index building and search.
//
// This example shows:
//   1. Creating an inverted index
//   2. Adding documents to the index
//   3. Searching the index
//   4. Understanding the index structure
//
// Run with: go run main.go
package main

import (
	"fmt"
	"sort"

	"inverted-index/src"
)

func main() {
	fmt.Println("=== Inverted Index - Basic Demo ===")
	fmt.Println()

	// Step 1: Create an index builder
	builder := invertedindex.NewIndexBuilder()

	// Step 2: Add documents
	docs := []struct {
		id      int
		content string
	}{
		{
			id: 1,
			content: "Go is a programming language. Go is fast and simple.",
		},
		{
			id: 2,
			content: "Python is also a programming language. Python is easy to learn.",
		},
		{
			id: 3,
			content: "Rust is a systems programming language. Rust focuses on safety.",
		},
		{
			id: 4,
			content: "Java is an object-oriented programming language. Java is widely used.",
		},
		{
			id: 5,
			content: "The Go programming language was created at Google.",
		},
	}

	for _, doc := range docs {
		err := builder.AddDocument(doc.id, doc.content)
		if err != nil {
			fmt.Printf("Error adding document %d: %v\n", doc.id, err)
		}
	}

	// Step 3: Build the index (computes document frequencies)
	builder.Build()
	index := builder.GetIndex()

	fmt.Printf("Index built: %d documents, %d terms\n", index.TotalDocCount(), index.Size())
	fmt.Println()

	// Step 4: Show index structure
	fmt.Println("=== Index Structure ===")
	terms := index.Terms()
	fmt.Printf("Terms in index (sorted): %v\n", terms)
	fmt.Println()

	// Show term frequencies for a specific term
	term := "programming"
	entry := index.GetEntry(term)
	if entry != nil {
		fmt.Printf("=== Term: '%s' ===\n", term)
		fmt.Printf("Document Frequency (DF): %d\n", entry.DocumentFreq)
		fmt.Printf("Term Frequencies (TF):\n")
		for docID, tf := range entry.TF {
			fmt.Printf("  Document %d: TF=%d\n", docID, tf)
		}
		fmt.Printf("Postings list (%d entries):\n", entry.Postings.Len())
		for _, p := range entry.Postings.Items {
			fmt.Printf("  Doc %d: positions %v\n", p.DocID, p.Positions)
		}
	}
	fmt.Println()

	// Step 5: Search
	fmt.Println("=== Search Results ===")
	searcher := invertedindex.NewSearcher(index)

	queries := []string{
		"go",
		"programming",
		"language",
	}

	for _, q := range queries {
		fmt.Printf("\nQuery: \"%s\"\n", q)
		results, err := searcher.Search(q, 5)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		if len(results) == 0 {
			fmt.Println("  No results")
			continue
		}
		for i, r := range results {
			fmt.Printf("  [%d] Doc %d: score=%.4f (TF=%d)\n", i+1, r.DocID, r.Score, r.TermFreq)
		}
	}

	// Step 6: Show BM25 score breakdown
	fmt.Println("\n=== BM25 Score Breakdown ===")
	bm25Demo(index)
}

// bm25Demo shows how BM25 scoring works.
func bm25Demo(index *invertedindex.InvertedIndex) {
	// Get all documents
	docLengths := make(map[int]int)
	for _, r := range index.PostingsForTerm("go") {
		docLengths[r.DocID] = index.DocLength(r.DocID)
	}

	avgDocLen := invertedindex.AverageDocLen(index)
	totalDocs := index.TotalDocCount()
	cfg := invertedindex.DefaultBM25Config()

	fmt.Printf("Average document length: %.2f\n", avgDocLen)
	fmt.Printf("Total documents: %d\n", totalDocs)
	fmt.Printf("BM25 config: k1=%.2f, b=%.2f\n", cfg.K1, cfg.B)
	fmt.Println()

	// Show BM25 scores for "go" in each document
	entry := index.GetEntry("go")
	if entry == nil {
		return
	}

	fmt.Printf("BM25 scores for term 'go':\n")
	for _, p := range entry.Postings.Items {
		tf := entry.TF[p.DocID]
		docLen := index.DocLength(p.DocID)
		df := entry.DocumentFreq
		score := invertedindex.BM25Score(tf, docLen, df, totalDocs, avgDocLen, cfg)
		fmt.Printf("  Doc %d: TF=%d, docLen=%d, score=%.4f\n", p.DocID, tf, docLen, score)
	}
}

// PostingsForTerm is a helper to iterate postings (for demo purposes).
func (idx *invertedindex.InvertedIndex) PostingsForTerm(term string) []*invertedindex.Posting {
	if entry := idx.GetEntry(term); entry != nil {
		return entry.Postings.Items
	}
	return nil
}

// TermsSorted returns sorted terms.
func (idx *invertedindex.InvertedIndex) TermsSorted() []string {
	terms := idx.Terms()
	sort.Strings(terms)
	return terms
}
