package index

import (
	"testing"
)

func TestIndexAddDocument(t *testing.T) {
	idx := New()

	doc := &Document{
		ID:      "doc1",
		Content: "Hello World",
	}

	idx.AddDocument(doc)

	if idx.DocumentCount() != 1 {
		t.Errorf("expected 1 document, got %d", idx.DocumentCount())
	}
}

func TestIndexSearch(t *testing.T) {
	idx := New()

	docs := []*Document{
		{ID: "doc1", Content: "The quick brown fox"},
		{ID: "doc2", Content: "The lazy dog"},
		{ID: "doc3", Content: "Quick and fast"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	tests := []struct {
		term     string
		expected int
	}{
		{"quick", 2},
		{"fox", 1},
		{"the", 2},
		{"nonexistent", 0},
	}

	for _, tt := range tests {
		t.Run(tt.term, func(t *testing.T) {
			results := idx.Search(tt.term)
			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
			}
		})
	}
}

func TestIndexGetDocument(t *testing.T) {
	idx := New()

	doc := &Document{
		ID:      "doc1",
		Content: "Hello World",
	}

	idx.AddDocument(doc)

	got := idx.GetDocument("doc1")
	if got == nil {
		t.Fatal("expected document, got nil")
	}

	if got.ID != "doc1" {
		t.Errorf("expected ID 'doc1', got %s", got.ID)
	}

	if got.Content != "Hello World" {
		t.Errorf("expected Content 'Hello World', got %s", got.Content)
	}
}

func TestIndexGetDocumentNotFound(t *testing.T) {
	idx := New()

	got := idx.GetDocument("nonexistent")
	if got != nil {
		t.Error("expected nil for nonexistent document")
	}
}

func TestIndexAllDocuments(t *testing.T) {
	idx := New()

	docs := []*Document{
		{ID: "doc1", Content: "Hello"},
		{ID: "doc2", Content: "World"},
		{ID: "doc3", Content: "Foo Bar"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	all := idx.AllDocuments()
	if len(all) != 3 {
		t.Errorf("expected 3 documents, got %d", len(all))
	}
}

func TestIndexTokenization(t *testing.T) {
	idx := New()

	doc := &Document{
		ID:      "doc1",
		Content: "Hello, World! This is a test.",
	}

	idx.AddDocument(doc)

	// Should find "hello", "world", "this", "is", "a", "test"
	expectedTerms := []string{"hello", "world", "this", "is", "a", "test"}

	for _, term := range expectedTerms {
		results := idx.Search(term)
		if len(results) != 1 {
			t.Errorf("expected 1 result for %s, got %d", term, len(results))
		}
	}
}

func TestCaseInsensitiveSearch(t *testing.T) {
	idx := New()

	doc := &Document{
		ID:      "doc1",
		Content: "Hello WORLD",
	}

	idx.AddDocument(doc)

	// All searches should be case-insensitive
	tests := []string{"hello", "Hello", "HELLO", "world", "World", "WORLD"}

	for _, term := range tests {
		results := idx.Search(term)
		if len(results) != 1 {
			t.Errorf("expected 1 result for %s, got %d", term, len(results))
		}
	}
}

func TestIndexMultipleDocuments(t *testing.T) {
	idx := New()

	docs := []*Document{
		{ID: "doc1", Content: "apple banana cherry"},
		{ID: "doc2", Content: "banana cherry date"},
		{ID: "doc3", Content: "cherry date elderberry"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	// "cherry" appears in all 3 documents
	results := idx.Search("cherry")
	if len(results) != 3 {
		t.Errorf("expected 3 results for cherry, got %d", len(results))
	}

	// "apple" appears only in doc1
	results = idx.Search("apple")
	if len(results) != 1 {
		t.Errorf("expected 1 result for apple, got %d", len(results))
	}
}
