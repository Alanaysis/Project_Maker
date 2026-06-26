// Package main demonstrates phrase queries on the inverted index.
//
// This example shows:
//   1. How phrase queries work (exact word sequence matching)
//   2. Comparison with AND queries
//   3. Phrase matching with positions
//
// Run with: go run main.go
package main

import (
	"fmt"

	"inverted-index/src"
)

func main() {
	fmt.Println("=== Inverted Index - Phrase Query Demo ===")
	fmt.Println()

	// Create index builder
	builder := invertedindex.NewIndexBuilder()

	docs := []struct {
		id      int
		content string
	}{
		{1, "Machine learning is a subset of artificial intelligence"},
		{2, "Deep learning is a subset of machine learning"},
		{3, "Artificial intelligence and machine learning are related fields"},
		{4, "Neural networks are used in machine learning applications"},
		{5, "Deep neural networks have revolutionized machine learning"},
		{6, "Learning machine tools are different from machine learning"},
		{7, "The field of artificial intelligence includes machine learning"},
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

	// Demo phrase queries
	fmt.Println("=== Phrase Queries ===")
	phraseQueries := []string{
		`"machine learning"`,
		`"deep learning"`,
		`"artificial intelligence"`,
		`"neural networks"`,
	}

	for _, q := range phraseQueries {
		fmt.Printf("\nPhrase Query: %s\n", q)
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

	// Compare phrase query with AND query
	fmt.Println("\n=== Phrase vs AND Comparison ===")
	compareQueries := []struct {
		phrase string
		andQ   string
	}{
		{`"machine learning"`, "machine AND learning"},
		{`"deep learning"`, "deep AND learning"},
		{`"artificial intelligence"`, "artificial AND intelligence"},
	}

	for _, c := range compareQueries {
		fmt.Printf("\nPhrase: %s\n", c.phrase)
		phraseResults, _ := searcher.Search(c.phrase, 10)
		fmt.Printf("  Results: %d\n", len(phraseResults))
		for _, r := range phraseResults {
			fmt.Printf("    Doc %d: score=%.4f\n", r.DocID, r.Score)
		}

		fmt.Printf("AND: %s\n", c.andQ)
		andResults, _ := searcher.Search(c.andQ, 10)
		fmt.Printf("  Results: %d\n", len(andResults))
		for _, r := range andResults {
			fmt.Printf("    Doc %d: score=%.4f\n", r.DocID, r.Score)
		}
	}

	// Demo tokenization
	fmt.Println("\n=== Tokenization Demo ===")
	demoTokenization()
}

// demoTokenization shows how text is tokenized.
func demoTokenization() {
	testTexts := []string{
		"Hello world this is a test",
		"Go is great. Go is fast!",
		"机器学习是一种人工智能",
		"Machine learning 机器学习 AI",
	}

	for _, text := range testTexts {
		tokens := invertedindex.Tokenize(text)
		fmt.Printf("Text: %q\n", text)
		fmt.Printf("Tokens: ")
		for _, t := range tokens {
			fmt.Printf("[%s@%d] ", t.Text, t.Position)
		}
		fmt.Println()
		fmt.Println()
	}
}
