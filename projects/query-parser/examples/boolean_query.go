// Command booleanquery demonstrates boolean query parsing.
//
// This example shows how to parse AND, OR, and NOT operators
// and build a query tree from them.
//
// Usage:
//
//	go run examples/boolean_query.go
//
// Key concepts demonstrated:
//   - AND: all terms must match (intersection)
//   - OR: at least one term must match (union)
//   - NOT: exclude documents matching the term
//   - Operator precedence: NOT > AND > OR
package main

import (
	"fmt"

	"query-parser/src"
)

func main() {
	fmt.Println("=== Boolean Query Parsing Demo ===")
	fmt.Println()

	queries := []string{
		"golang AND python",
		"golang OR python OR java",
		"golang NOT python",
		"golang AND (python OR java)",
		"(golang OR python) AND (web OR framework)",
		"NOT deprecated AND golang",
	}

	for _, q := range queries {
		fmt.Printf("Query: %q\n", q)
		parseAndShow(q)
		fmt.Println()
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

	// Show statistics
	stats := parser.GetStats()
	fmt.Printf("  Tokens: %d | Terms: %d | Boolean nodes: %d | Depth: %d\n",
		queryparser "query-parser/src".CountTokens(parser.GetStats().CollectStats(tree)),
		stats.TotalTerms,
		stats.TotalBoolean,
		stats.MaxDepth,
	)
}
