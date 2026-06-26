// Package invertedindex implements an inverted index for text search.
// This file contains the IndexBuilder which handles the index building process.

package invertedindex

import "fmt"

// IndexBuilder constructs an inverted index from a collection of documents.
//
// The index building process:
//   1. For each document, tokenize the text into terms
//   2. Compute term frequencies (TF) with positions
//   3. Add each document to the inverted index
//   4. Update document frequency (DF) for each term
//   5. Compute global statistics (total docs, average document length)
type IndexBuilder struct {
	index *InvertedIndex
}

// NewIndexBuilder creates a new index builder.
func NewIndexBuilder() *IndexBuilder {
	return &IndexBuilder{
		index: NewInvertedIndex(),
	}
}

// GetIndex returns the built inverted index.
// Call this after adding all documents to get the final index.
func (ib *IndexBuilder) GetIndex() *InvertedIndex {
	return ib.index
}

// AddDocument adds a document to the index.
//
// Parameters:
//   - docID: unique document identifier
//   - content: the document text to index
//
// The method tokenizes the content, computes term frequencies,
// and adds the document to the index.
func (ib *IndexBuilder) AddDocument(docID int, content string) error {
	if content == "" {
		return fmt.Errorf("document content cannot be empty")
	}

	// Step 1: Tokenize the document
	tokens := Tokenize(content)
	if len(tokens) == 0 {
		return fmt.Errorf("document %d has no valid tokens", docID)
	}

	// Step 2: Compute term frequencies with positions
	termFreq := make(map[string][]int)
	for _, token := range tokens {
		positions := termFreq[token.Text]
		termFreq[token.Text] = append(positions, token.Position)
	}

	// Step 3: Add to index
	docLen := len(tokens)
	ib.index.AddDocument(docID, termFreq, docLen)

	return nil
}

// AddDocumentWithTokens adds a document using pre-computed tokens.
// This is useful when you want to use a custom tokenizer.
func (ib *IndexBuilder) AddDocumentWithTokens(docID int, tokens []Token) error {
	if len(tokens) == 0 {
		return fmt.Errorf("no tokens provided for document %d", docID)
	}

	termFreq := make(map[string][]int)
	for _, token := range tokens {
		positions := termFreq[token.Text]
		termFreq[token.Text] = append(positions, token.Position)
	}

	docLen := len(tokens)
	ib.index.AddDocument(docID, termFreq, docLen)

	return nil
}

// Build finalizes the index by computing document frequencies.
func (ib *IndexBuilder) Build() {
	// Update document frequency for each term
	terms := ib.index.Terms()
	for _, term := range terms {
		ib.index.UpdateDocumentFreq(term)
	}

	// Set total document count
	docCount := len(ib.index.docLens)
	ib.index.SetDocCount(docCount)
}

// BuildAndSearch is a convenience method that builds the index and performs a search.
func (ib *IndexBuilder) BuildAndSearch(queryStr string, topK int) (Results, error) {
	ib.Build()
	return ib.index.Search(queryStr, topK)
}
