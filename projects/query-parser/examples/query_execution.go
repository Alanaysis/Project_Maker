// Command queryexec demonstrates query execution against a mock document store.
//
// This example shows how parsed queries are executed against documents,
// with relevance scoring and ranking of results.
//
// Usage:
//
//	go run examples/query_execution.go
//
// Key concepts demonstrated:
//   - Query execution against documents
//   - Relevance scoring
//   - Result ranking
//   - Boolean query evaluation
package main

import (
	"fmt"
	"sort"

	"query-parser/src"
)

// Document represents a searchable document.
type Document struct {
	ID    string
	Title string
	Body  string
	Terms []string
}

// SearchResult represents a matched document with its relevance score.
type SearchResult struct {
	Document Document
	Score    float64
}

func main() {
	fmt.Println("=== Query Execution Demo ===")
	fmt.Println()

	// Create a mock document store
	docs := createMockDocuments()
	fmt.Printf("Document store: %d documents\n", len(docs))
	fmt.Println()

	// Test various queries
	queries := []string{
		"golang",
		"golang AND web",
		"python OR java",
		`"web framework"`,
		"golan~",
		"go*",
		"programming AND (web OR backend)",
		"golang NOT python",
	}

	scorer := queryparser.NewRelevanceScorer()

	for _, q := range queries {
		fmt.Printf("Query: %q\n", q)

		// Parse the query
		parser := queryparser.NewParser(q)
		tree, err := parser.Parse()
		if err != nil {
			fmt.Printf("  Parse error: %v\n", err)
			fmt.Println()
			continue
		}

		// Show parsed tree
		fmt.Println(tree.String())

		// Execute against documents
		results := executeQuery(tree.Root, docs, scorer)

		// Sort by score descending
		sort.Slice(results, func(i, j int) bool {
			return results[i].Score > results[j].Score
		})

		// Display results
		fmt.Printf("  Results (%d):\n", len(results))
		for i, r := range results {
			fmt.Printf("    %d. [%s] %q (score: %.2f)\n",
				i+1, r.Document.ID, r.Document.Title, r.Score)
		}
		fmt.Println()
	}
}

// createMockDocuments creates a set of mock documents for testing.
func createMockDocuments() []Document {
	return []Document{
		{
			ID:    "doc1",
			Title: "Introduction to Go",
			Body:  "Go is a statically typed, compiled programming language designed for simplicity and reliability.",
			Terms: []string{"go", "golang", "programming", "language", "statically", "typed", "compiled"},
		},
		{
			ID:    "doc2",
			Title: "Web Development with Go",
			Body:  "Learn how to build web applications and frameworks using the Go programming language.",
			Terms: []string{"web", "development", "go", "golang", "framework", "application", "programming"},
		},
		{
			ID:    "doc3",
			Title: "Python for Data Science",
			Body:  "Python is a popular language for data science, machine learning, and web development.",
			Terms: []string{"python", "data", "science", "machine", "learning", "web", "development", "programming"},
		},
		{
			ID:    "doc4",
			Title: "Java Enterprise Applications",
			Body:  "Java is widely used for enterprise applications, web services, and backend systems.",
			Terms: []string{"java", "enterprise", "application", "web", "service", "backend", "programming"},
		},
		{
			ID:    "doc5",
			Title: "Rust Systems Programming",
			Body:  "Rust provides memory safety without garbage collection, ideal for systems programming.",
			Terms: []string{"rust", "systems", "programming", "memory", "safety", "garbage", "collection"},
		},
		{
			ID:    "doc6",
			Title: "Go Concurrency Patterns",
			Body:  "Go has built-in concurrency with goroutines and channels for parallel programming.",
			Terms: []string{"go", "golang", "concurrency", "goroutine", "channel", "parallel", "programming"},
		},
	}
}

// executeQuery runs a parsed query against a set of documents.
func executeQuery(node *queryparser.QueryNode, docs []Document, scorer *queryparser.RelevanceScorer) []SearchResult {
	var results []SearchResult

	for _, doc := range docs {
		score := scorer.DocumentScore(doc.Terms, node)
		if score > 0 {
			results = append(results, SearchResult{
				Document: doc,
				Score:    score,
			})
		}
	}

	return results
}
