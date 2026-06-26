// Package main demonstrates boolean queries (AND, OR) on the inverted index.
//
// This example shows:
//   1. AND queries: find documents containing ALL terms
//   2. OR queries: find documents containing ANY term
//   3. How postings list intersection and union work
//
// Run with: go run main.go
package main

import (
	"fmt"

	"inverted-index/src"
)

func main() {
	fmt.Println("=== Inverted Index - Boolean Query Demo ===")
	fmt.Println()

	// Create index builder
	builder := invertedindex.NewIndexBuilder()

	// Add documents about different topics
	docs := []struct {
		id      int
		content string
	}{
		{1, "Machine learning algorithms use statistical models"},
		{2, "Deep learning neural networks have many layers"},
		{3, "Natural language processing uses machine learning"},
		{4, "Computer vision uses deep learning for image recognition"},
		{5, "Reinforcement learning rewards agents for good actions"},
		{6, "Supervised learning uses labeled training data"},
		{7, "Unsupervised learning finds patterns in unlabeled data"},
		{8, "Transfer learning applies knowledge from one task to another"},
	}

	for _, doc := range docs {
		builder.AddDocument(doc.id, doc.content)
	}

	builder.Build()
	index := builder.GetIndex()

	fmt.Printf("Index: %d documents, %d terms\n", index.TotalDocCount(), index.Size())
	fmt.Println()

	// Create searcher
	searcher := invertedindex.NewSearcher(index)

	// Demo AND queries
	fmt.Println("=== AND Queries ===")
	andQueries := []string{
		"machine AND learning",
		"deep AND learning",
		"learning AND data",
		"neural AND networks",
	}

	for _, q := range andQueries {
		fmt.Printf("\nQuery: \"%s\"\n", q)
		results, err := searcher.Search(q, 10)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		if len(results) == 0 {
			fmt.Println("  No results")
			continue
		}
		for _, r := range results {
			fmt.Printf("  Doc %d: score=%.4f\n", r.DocID, r.Score)
		}
	}

	// Demo OR queries
	fmt.Println("\n=== OR Queries ===")
	orQueries := []string{
		"machine OR deep",
		"learning OR training",
		"data OR models",
		"vision OR language",
	}

	for _, q := range orQueries {
		fmt.Printf("\nQuery: \"%s\"\n", q)
		results, err := searcher.Search(q, 10)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		if len(results) == 0 {
			fmt.Println("  No results")
			continue
		}
		for _, r := range results {
			fmt.Printf("  Doc %d: score=%.4f\n", r.DocID, r.Score)
		}
	}

	// Demo postings list operations
	fmt.Println("\n=== Postings List Operations ===")
	demoPostings(index)
}

// demoPostings shows how postings lists are merged for boolean queries.
func demoPostings(index *invertedindex.InvertedIndex) {
	term1 := "learning"
	term2 := "machine"

	pl1 := index.GetPostings(term1)
	pl2 := index.GetPostings(term2)

	fmt.Printf("Postings for '%s': %d documents\n", term1, pl1.Len())
	for _, p := range pl1.Items {
		fmt.Printf("  Doc %d: TF=%d\n", p.DocID, pl1.Len())
	}

	fmt.Printf("Postings for '%s': %d documents\n", term2, pl2.Len())
	for _, p := range pl2.Items {
		fmt.Printf("  Doc %d\n", p.DocID)
	}

	// AND = Intersection
	intersection := pl1.Intersect(pl2)
	fmt.Printf("\nAND '%s' AND '%s': %d documents\n", term1, term2, intersection.Len())
	for _, p := range intersection.Items {
		fmt.Printf("  Doc %d\n", p.DocID)
	}

	// OR = Union
	union := pl1.Union(pl2)
	fmt.Printf("\nOR '%s' OR '%s': %d documents\n", term1, term2, union.Len())
	for _, p := range union.Items {
		fmt.Printf("  Doc %d\n", p.DocID)
	}
}
