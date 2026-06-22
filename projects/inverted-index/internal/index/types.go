package index

import "sync"

// Document represents a document to be indexed.
type Document struct {
	ID      string
	Title   string
	Content string
}

// Posting represents an entry in a posting list for a specific document.
type Posting struct {
	DocID     string
	Positions []int // positions of the term in the document
	TermFreq  int   // frequency of the term in the document
}

// PostingList is a sorted list of postings for a single term.
type PostingList struct {
	Term     string
	Postings []Posting
}

// IndexStats holds statistics about the index.
type IndexStats struct {
	NumDocuments int
	NumTerms     int
	TotalTokens  int
}

// InvertedIndex is the core data structure for the search engine.
type InvertedIndex struct {
	mu sync.RWMutex

	// term -> posting list
	index map[string]*PostingList

	// docID -> document metadata
	documents map[string]*Document

	// docID -> number of tokens in document
	docLengths map[string]int

	// total number of tokens across all documents
	totalTokens int
}

// New creates a new empty InvertedIndex.
func New() *InvertedIndex {
	return &InvertedIndex{
		index:      make(map[string]*PostingList),
		documents:  make(map[string]*Document),
		docLengths: make(map[string]int),
	}
}
