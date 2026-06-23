package index

import (
	"strings"
	"sync"
)

// Document represents a document in the index
type Document struct {
	ID      string
	Content string
}

// Index is an in-memory inverted index
type Index struct {
	mu        sync.RWMutex
	documents map[string]*Document
	index     map[string]map[string]bool // term -> docID -> exists
}

// New creates a new Index
func New() *Index {
	return &Index{
		documents: make(map[string]*Document),
		index:     make(map[string]map[string]bool),
	}
}

// AddDocument adds a document to the index
func (idx *Index) AddDocument(doc *Document) {
	idx.mu.Lock()
	defer idx.mu.Unlock()

	idx.documents[doc.ID] = doc

	// Tokenize and index
	terms := tokenize(doc.Content)
	for _, term := range terms {
		if idx.index[term] == nil {
			idx.index[term] = make(map[string]bool)
		}
		idx.index[term][doc.ID] = true
	}
}

// Search returns document IDs containing the term
func (idx *Index) Search(term string) []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	term = strings.ToLower(term)
	docs := idx.index[term]
	if docs == nil {
		return nil
	}

	result := make([]string, 0, len(docs))
	for docID := range docs {
		result = append(result, docID)
	}
	return result
}

// GetDocument returns a document by ID
func (idx *Index) GetDocument(id string) *Document {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	return idx.documents[id]
}

// AllDocuments returns all document IDs
func (idx *Index) AllDocuments() []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	ids := make([]string, 0, len(idx.documents))
	for id := range idx.documents {
		ids = append(ids, id)
	}
	return ids
}

// DocumentCount returns the number of documents
func (idx *Index) DocumentCount() int {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	return len(idx.documents)
}

// tokenize splits text into lowercase terms
func tokenize(text string) []string {
	text = strings.ToLower(text)

	// Split by whitespace and punctuation
	var terms []string
	current := make([]byte, 0, 32)

	for i := 0; i < len(text); i++ {
		ch := text[i]
		if ch >= 'a' && ch <= 'z' || ch >= '0' && ch <= '9' {
			current = append(current, ch)
		} else {
			if len(current) > 0 {
				terms = append(terms, string(current))
				current = current[:0]
			}
		}
	}

	if len(current) > 0 {
		terms = append(terms, string(current))
	}

	return terms
}
