package tests

import (
	"testing"

	"github.com/copyninja/inverted-index/internal/index"
)

func TestAddDocument(t *testing.T) {
	idx := index.NewIndexer()

	doc := index.Document{
		ID:      "doc1",
		Title:   "Test Document",
		Content: "This is a test document about programming",
	}

	err := idx.AddDocument(doc)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	stats := idx.GetStats()
	if stats.NumDocuments != 1 {
		t.Errorf("expected 1 document, got %d", stats.NumDocuments)
	}
	if stats.NumTerms == 0 {
		t.Error("expected at least 1 term")
	}
}

func TestAddDuplicateDocument(t *testing.T) {
	idx := index.NewIndexer()

	doc := index.Document{ID: "doc1", Title: "Test", Content: "content"}
	idx.AddDocument(doc)

	err := idx.AddDocument(doc)
	if err == nil {
		t.Error("expected error for duplicate document")
	}
}

func TestAddDocumentEmptyID(t *testing.T) {
	idx := index.NewIndexer()

	doc := index.Document{ID: "", Title: "Test", Content: "content"}
	err := idx.AddDocument(doc)
	if err == nil {
		t.Error("expected error for empty ID")
	}
}

func TestRemoveDocument(t *testing.T) {
	idx := index.NewIndexer()

	doc := index.Document{ID: "doc1", Title: "Test", Content: "hello world"}
	idx.AddDocument(doc)

	err := idx.RemoveDocument("doc1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	stats := idx.GetStats()
	if stats.NumDocuments != 0 {
		t.Errorf("expected 0 documents, got %d", stats.NumDocuments)
	}
}

func TestRemoveNonexistentDocument(t *testing.T) {
	idx := index.NewIndexer()

	err := idx.RemoveDocument("nonexistent")
	if err == nil {
		t.Error("expected error for nonexistent document")
	}
}

func TestGetDocument(t *testing.T) {
	idx := index.NewIndexer()

	doc := index.Document{ID: "doc1", Title: "Test", Content: "content"}
	idx.AddDocument(doc)

	retrieved, ok := idx.GetDocument("doc1")
	if !ok {
		t.Fatal("expected document to be found")
	}
	if retrieved.ID != "doc1" || retrieved.Title != "Test" {
		t.Errorf("unexpected document: %+v", retrieved)
	}

	_, ok = idx.GetDocument("nonexistent")
	if ok {
		t.Error("expected document to not be found")
	}
}

func TestSearchAND(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go is a programming language"})
	idx.AddDocument(index.Document{ID: "doc2", Title: "Python", Content: "Python is a programming language"})
	idx.AddDocument(index.Document{ID: "doc3", Title: "Web", Content: "web development with JavaScript"})

	// AND: must contain both terms
	results := idx.Search("programming language")
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}

	// Verify both docs are returned
	ids := make(map[string]bool)
	for _, r := range results {
		ids[r.DocID] = true
	}
	if !ids["doc1"] || !ids["doc2"] {
		t.Errorf("expected doc1 and doc2, got %v", ids)
	}
}

func TestSearchOR(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go programming"})
	idx.AddDocument(index.Document{ID: "doc2", Title: "Python", Content: "Python scripting"})
	idx.AddDocument(index.Document{ID: "doc3", Title: "Web", Content: "JavaScript web"})

	results := idx.Search("Go OR Python")
	if len(results) != 2 {
		t.Fatalf("expected 2 results for OR query, got %d", len(results))
	}
}

func TestSearchNOT(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go programming language"})
	idx.AddDocument(index.Document{ID: "doc2", Title: "Python", Content: "Python scripting language"})
	idx.AddDocument(index.Document{ID: "doc3", Title: "Web", Content: "JavaScript web development"})

	results := idx.Search("NOT programming")
	if len(results) != 2 {
		t.Fatalf("expected 2 results for NOT query, got %d", len(results))
	}

	// Should return doc2 and doc3 (both don't contain "programming")
	ids := make(map[string]bool)
	for _, r := range results {
		ids[r.DocID] = true
	}
	if !ids["doc2"] || !ids["doc3"] {
		t.Errorf("expected doc2 and doc3, got %v", ids)
	}
}

func TestSearchNoResults(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go programming"})

	results := idx.Search("nonexistent term")
	if len(results) != 0 {
		t.Errorf("expected 0 results, got %d", len(results))
	}
}

func TestSearchRanking(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go Go Go programming"})
	idx.AddDocument(index.Document{ID: "doc2", Title: "Overview", Content: "Go is great"})

	results := idx.Search("Go")
	if len(results) < 2 {
		t.Fatalf("expected at least 2 results, got %d", len(results))
	}

	// doc1 should rank higher because it has more occurrences of "Go"
	if results[0].DocID != "doc1" {
		t.Errorf("expected doc1 to rank first, got %s", results[0].DocID)
	}
}

func TestSearchScoresPositive(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Test", Content: "hello world"})

	results := idx.Search("hello")
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
	if results[0].Score <= 0 {
		t.Errorf("expected positive score, got %f", results[0].Score)
	}
}

func TestMultipleDocuments(t *testing.T) {
	idx := index.NewIndexer()

	docs := []index.Document{
		{ID: "doc1", Title: "Go", Content: "Go is a compiled language"},
		{ID: "doc2", Title: "Python", Content: "Python is an interpreted language"},
		{ID: "doc3", Title: "Rust", Content: "Rust is a systems programming language"},
		{ID: "doc4", Title: "JavaScript", Content: "JavaScript runs in the browser"},
		{ID: "doc5", Title: "Java", Content: "Java is used for enterprise applications"},
	}

	for _, d := range docs {
		idx.AddDocument(d)
	}

	stats := idx.GetStats()
	if stats.NumDocuments != 5 {
		t.Errorf("expected 5 documents, got %d", stats.NumDocuments)
	}

	results := idx.Search("language")
	if len(results) != 3 {
		t.Errorf("expected 3 results for 'language', got %d", len(results))
	}
}

func TestRemoveAndSearch(t *testing.T) {
	idx := index.NewIndexer()

	idx.AddDocument(index.Document{ID: "doc1", Title: "Go", Content: "Go programming"})
	idx.AddDocument(index.Document{ID: "doc2", Title: "Python", Content: "Python programming"})

	idx.RemoveDocument("doc1")

	results := idx.Search("Go")
	if len(results) != 0 {
		t.Errorf("expected 0 results after removal, got %d", len(results))
	}

	results = idx.Search("programming")
	if len(results) != 1 {
		t.Errorf("expected 1 result after removal, got %d", len(results))
	}
}
