package internal

import (
	"query-parser/internal/executor"
	"query-parser/internal/index"
	"query-parser/internal/lexer"
	"query-parser/internal/parser"
	"testing"
)

func createTestIndex() *index.Index {
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

func parseAndExecute(t *testing.T, idx *index.Index, query string) []executor.SearchResult {
	t.Helper()

	l := lexer.New(query)
	tokens := l.Tokenize()

	p := parser.New(tokens)
	ast, err := p.Parse()
	if err != nil {
		t.Fatalf("parse error: %v", err)
	}

	ex := executor.New(idx)
	return ex.Execute(ast)
}

func TestIntegrationSimpleTerm(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "fox")

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// Should find at least doc1
	found := false
	for _, r := range results {
		if r.DocID == "doc1" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc1 in results")
	}
}

func TestIntegrationBooleanAnd(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "quick AND fox")

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// Should find doc1 (has both quick and fox)
	found := false
	for _, r := range results {
		if r.DocID == "doc1" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc1 in results")
	}
}

func TestIntegrationBooleanOr(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "cat OR dog")

	if len(results) < 2 {
		t.Fatalf("expected at least 2 results, got %d", len(results))
	}

	docIDs := make(map[string]bool)
	for _, r := range results {
		docIDs[r.DocID] = true
	}

	if !docIDs["doc3"] {
		t.Error("expected doc3 (cat)")
	}
	if !docIDs["doc5"] {
		t.Error("expected doc5 (dog)")
	}
}

func TestIntegrationNot(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "quick AND NOT fox")

	// Should find doc4 (quick but not fox)
	found := false
	for _, r := range results {
		if r.DocID == "doc4" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc4 in results")
	}

	// Should NOT find doc1 (has both quick and fox)
	for _, r := range results {
		if r.DocID == "doc1" {
			t.Error("doc1 should be excluded")
		}
	}
}

func TestIntegrationPhrase(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, `"brown fox"`)

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// Should find doc1 (has "brown fox" as substring)
	found := false
	for _, r := range results {
		if r.DocID == "doc1" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc1 in results")
	}
}

func TestIntegrationComplexQuery(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, `(quick OR fast) AND fox`)

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// Should find doc1
	found := false
	for _, r := range results {
		if r.DocID == "doc1" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc1 in results")
	}
}

func TestIntegrationImplicitAnd(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "quick fox")

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// Should find doc1 (has both quick and fox)
	found := false
	for _, r := range results {
		if r.DocID == "doc1" {
			found = true
		}
	}
	if !found {
		t.Error("expected doc1 in results")
	}
}

func TestIntegrationRelevanceOrder(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "quick")

	if len(results) < 2 {
		t.Fatal("expected at least 2 results")
	}

	// Results should be sorted by score
	for i := 1; i < len(results); i++ {
		if results[i].Score > results[i-1].Score {
			t.Error("results not sorted by score")
		}
	}
}

func TestIntegrationNoResults(t *testing.T) {
	idx := createTestIndex()
	results := parseAndExecute(t, idx, "nonexistent")

	if len(results) != 0 {
		t.Errorf("expected 0 results, got %d", len(results))
	}
}
