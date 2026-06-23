package executor

import (
	"query-parser/internal/ast"
	"query-parser/internal/index"
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

func TestExecuteTerm(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	node := ast.NewTerm("fox")
	results := ex.Execute(node)

	if len(results) == 0 {
		t.Fatal("expected results, got none")
	}

	// Should find doc1 and doc2
	docIDs := make(map[string]bool)
	for _, r := range results {
		docIDs[r.DocID] = true
	}

	if !docIDs["doc1"] {
		t.Error("expected doc1 in results")
	}
	if !docIDs["doc2"] {
		t.Error("expected doc2 in results")
	}
}

func TestExecutePhrase(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	node := ast.NewPhrase("brown fox")
	results := ex.Execute(node)

	if len(results) == 0 {
		t.Fatal("expected results, got none")
	}

	// Should find doc1 (contains "brown fox")
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

func TestExecuteAnd(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	// fox AND dog
	node := ast.NewAnd(ast.NewTerm("fox"), ast.NewTerm("dog"))
	results := ex.Execute(node)

	if len(results) == 0 {
		t.Fatal("expected results, got none")
	}

	// Should find doc1 (has both fox and dog)
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

func TestExecuteOr(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	// cat OR dog
	node := ast.NewOr(ast.NewTerm("cat"), ast.NewTerm("dog"))
	results := ex.Execute(node)

	if len(results) < 2 {
		t.Fatalf("expected at least 2 results, got %d", len(results))
	}

	// Should find doc3 (cat) and doc5 (dog)
	docIDs := make(map[string]bool)
	for _, r := range results {
		docIDs[r.DocID] = true
	}

	if !docIDs["doc3"] {
		t.Error("expected doc3 in results")
	}
	if !docIDs["doc5"] {
		t.Error("expected doc5 in results")
	}
}

func TestExecuteNot(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	// NOT lazy
	node := ast.NewNot(ast.NewTerm("lazy"))
	results := ex.Execute(node)

	// Should not include doc1 or doc3 (contain "lazy")
	for _, r := range results {
		if r.DocID == "doc1" || r.DocID == "doc3" {
			t.Errorf("unexpected doc in results: %s", r.DocID)
		}
	}
}

func TestExecuteComplexQuery(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	// (quick OR fast) AND fox
	query := ast.NewAnd(
		ast.NewOr(ast.NewTerm("quick"), ast.NewTerm("fast")),
		ast.NewTerm("fox"),
	)

	results := ex.Execute(query)

	// Should find doc1 (quick fox)
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

func TestExecuteRelevanceSorting(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	// Search for "fox"
	node := ast.NewTerm("fox")
	results := ex.Execute(node)

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

func TestExecuteEmptyQuery(t *testing.T) {
	idx := createTestIndex()
	ex := New(idx)

	results := ex.Execute(nil)

	if len(results) != 0 {
		t.Errorf("expected 0 results, got %d", len(results))
	}
}
