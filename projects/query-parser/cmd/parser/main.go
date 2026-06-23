package main

import (
	"fmt"
	"os"
	"query-parser/internal/executor"
	"query-parser/internal/index"
	"query-parser/internal/lexer"
	"query-parser/internal/parser"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: parser <query>")
		fmt.Println("Examples:")
		fmt.Println(`  parser "hello world"`)
		fmt.Println(`  parser "hello AND world"`)
		fmt.Println(`  parser "hello OR world"`)
		fmt.Println(`  parser "NOT goodbye"`)
		fmt.Println(`  parser "(hello OR hi) AND world"`)
		os.Exit(1)
	}

	query := os.Args[1]

	// Create sample index
	idx := createSampleIndex()

	// Parse query
	l := lexer.New(query)
	tokens := l.Tokenize()

	p := parser.New(tokens)
	ast, err := p.Parse()
	if err != nil {
		fmt.Printf("Parse error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Query: %s\n", query)
	fmt.Printf("AST:   %s\n\n", ast.String())

	// Execute query
	ex := executor.New(idx)
	results := ex.Execute(ast)

	if len(results) == 0 {
		fmt.Println("No results found.")
	} else {
		fmt.Printf("Found %d results:\n\n", len(results))
		for i, result := range results {
			fmt.Printf("%d. [Score: %.2f] %s\n", i+1, result.Score, result.DocID)
			fmt.Printf("   %s\n\n", truncate(result.Content, 100))
		}
	}
}

func createSampleIndex() *index.Index {
	idx := index.New()

	docs := []*index.Document{
		{ID: "doc1", Content: "The quick brown fox jumps over the lazy dog"},
		{ID: "doc2", Content: "A quick brown dog outpaces the fox"},
		{ID: "doc3", Content: "The lazy cat sleeps all day long"},
		{ID: "doc4", Content: "Quick brown foxes are very fast animals"},
		{ID: "doc5", Content: "The dog and cat are friends"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	return idx
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}
