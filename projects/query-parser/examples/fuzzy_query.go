// Command fuzzyquery demonstrates fuzzy query parsing and matching.
//
// Fuzzy queries match terms that are "close" to the search term,
// measured by Levenshtein edit distance. This is useful for handling
// typos and spelling variations.
//
// Usage:
//
//	go run examples/fuzzy_query.go
//
// Key concepts demonstrated:
//   - Levenshtein distance calculation
//   - Fuzzy term matching
//   - Distance thresholds
//   - Match scoring
package main

import (
	"fmt"
	"sort"

	"query-parser/src"
)

func main() {
	fmt.Println("=== Fuzzy Query Demo ===")
	fmt.Println()

	// Demonstrate Levenshtein distance
	fmt.Println("--- Levenshtein Distance ---")
	distances := []struct {
		s1 string
		s2 string
	}{
		{"golang", "golan"},
		{"golang", "golng"},
		{"golang", "golgen"},
		{"golang", "golangx"},
		{"kitten", "sitting"},
		{"hello", "hello"},
		{"go", "golang"},
	}

	for _, d := range distances {
		dist := queryparser.LevenshteinDistance(d.s1, d.s2)
		fmt.Printf("  %q → %q : distance = %d\n", d.s1, d.s2, dist)
	}
	fmt.Println()

	// Demonstrate fuzzy query parsing
	fmt.Println("--- Fuzzy Query Parsing ---")
	queries := []string{
		"golan~",
		"golan~1",
		"golng~2",
		"wilcard~",
		"reciept~1",
	}

	for _, q := range queries {
		fmt.Printf("Query: %q\n", q)
		parser := queryparser.NewParser(q)
		tree, err := parser.Parse()
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		fmt.Println(tree.String())
		fmt.Println()
	}

	// Demonstrate fuzzy matching against a corpus
	fmt.Println("--- Fuzzy Matching Against Corpus ---")
	fmt.Println()

	corpus := []string{
		"golang", "golan", "golng", "golgen", "golangx",
		"python", "java", "javascript", "rust", "go",
	}

	matcher := queryparser.NewFuzzyMatcher()
	matcher.MaxDistance = 2
	matcher.MinLength = 3

	// Test various search terms
	searchTerms := []string{"golan", "golng", "reciept", "wilcard"}

	for _, term := range searchTerms {
		fmt.Printf("Searching for: %q\n", term)
		results := matcher.FindMatches(term, corpus)

		// Sort by score descending
		sort.Slice(results, func(i, j int) bool {
			return results[i].Score > results[j].Score
		})

		for _, r := range results {
			fmt.Printf("  ✓ %q (distance: %d, score: %.2f)\n", r.Candidate, r.Distance, r.Score)
		}
		if len(results) == 0 {
			fmt.Println("  (no matches)")
		}
		fmt.Println()
	}
}
