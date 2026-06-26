// Command phrasequery demonstrates phrase query parsing.
//
// Phrase queries find documents where terms appear in a specific order
// and proximity. This is more precise than individual term searches.
//
// Usage:
//
//	go run examples/phrase_query.go
//
// Key concepts demonstrated:
//   - Exact phrase matching ("web framework")
//   - Phrase tokenization
//   - Position-based matching
package main

import (
	"fmt"

	"query-parser/src"
)

func main() {
	fmt.Println("=== Phrase Query Demo ===")
	fmt.Println()

	queries := []string{
		`"web framework"`,
		`"machine learning"`,
		`"go programming language"`,
		`"golang" AND "web framework"`,
	}

	for _, q := range queries {
		fmt.Printf("Query: %q\n", q)
		parseAndShow(q)
		fmt.Println()
	}

	// Simulate phrase matching against document terms
	fmt.Println("=== Phrase Matching Against Documents ===")
	fmt.Println()

	documents := []struct {
		id    string
		terms []string
	}{
		{"doc1", []string{"golang", "is", "a", "great", "web", "framework"}},
		{"doc2", []string{"web", "framework", "built", "on", "go"}},
		{"doc3", []string{"python", "is", "also", "a", "web", "framework"}},
		{"doc4", []string{"web", "go", "framework"}},
	}

	phraseQuery := "web framework"
	phraseTerms := []string{"web", "framework"}

	fmt.Printf("Searching for phrase: %q\n", phraseQuery)
	fmt.Println()

	for _, doc := range documents {
		matches := phraseMatches(doc.terms, phraseTerms)
		status := "✗"
		if matches {
			status = "✓"
		}
		fmt.Printf("  %s %s: %v\n", status, doc.id, doc.terms)
	}
}

func parseAndShow(query string) {
	parser := queryparser.NewParser(query)
	tree, err := parser.Parse()
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
		return
	}

	fmt.Println(tree.String())
}

// phraseMatches checks if all phrase terms appear in the document.
func phraseMatches(docTerms []string, phraseTerms []string) bool {
	// Create a set of document terms for lookup
	termSet := make(map[string]bool)
	for _, t := range docTerms {
		termSet[t] = true
	}

	// Check all phrase terms exist
	for _, pt := range phraseTerms {
		if !termSet[pt] {
			return false
		}
	}

	// Check order is preserved
	docIndices := make([]int, len(phraseTerms))
	lastIdx := -1
	for i, pt := range phraseTerms {
		found := false
		for j, dt := range docTerms {
			if dt == pt && j > lastIdx {
				docIndices[i] = j
				lastIdx = j
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	// Verify order
	for i := 1; i < len(docIndices); i++ {
		if docIndices[i-1] >= docIndices[i] {
			return false
		}
	}

	return true
}
