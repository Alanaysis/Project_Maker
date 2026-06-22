package index

import (
	"fmt"
	"sort"
	"strings"

	"github.com/copyninja/inverted-index/internal/query"
	"github.com/copyninja/inverted-index/internal/tokenizer"
)

// Indexer builds and queries the inverted index.
type Indexer struct {
	index     *InvertedIndex
	tokenizer *tokenizer.Tokenizer
}

// NewIndexer creates a new Indexer with the default tokenizer.
func NewIndexer() *Indexer {
	return &Indexer{
		index:     New(),
		tokenizer: tokenizer.New(),
	}
}

// NewIndexerWithTokenizer creates a new Indexer with a custom tokenizer.
func NewIndexerWithTokenizer(tok *tokenizer.Tokenizer) *Indexer {
	return &Indexer{
		index:     New(),
		tokenizer: tok,
	}
}

// AddDocument tokenizes and indexes a document.
func (idx *Indexer) AddDocument(doc Document) error {
	if doc.ID == "" {
		return fmt.Errorf("document ID cannot be empty")
	}

	idx.index.mu.Lock()
	defer idx.index.mu.Unlock()

	// Check for duplicate
	if _, exists := idx.index.documents[doc.ID]; exists {
		return fmt.Errorf("document %s already exists", doc.ID)
	}

	// Combine title and content for indexing
	fullText := doc.Title + " " + doc.Content
	tokens := idx.tokenizer.TokenizeWithPositions(fullText)

	// Store document metadata
	idx.index.documents[doc.ID] = &Document{
		ID:      doc.ID,
		Title:   doc.Title,
		Content: doc.Content,
	}
	idx.index.docLengths[doc.ID] = len(tokens)
	idx.index.totalTokens += len(tokens)

	// Build posting lists
	termPositions := make(map[string][]int)
	for _, tok := range tokens {
		termPositions[tok.Text] = append(termPositions[tok.Text], tok.Position)
	}

	for term, positions := range termPositions {
		pl, exists := idx.index.index[term]
		if !exists {
			pl = &PostingList{Term: term}
			idx.index.index[term] = pl
		}
		pl.Postings = append(pl.Postings, Posting{
			DocID:     doc.ID,
			Positions: positions,
			TermFreq:  len(positions),
		})
	}

	return nil
}

// RemoveDocument removes a document from the index.
func (idx *Indexer) RemoveDocument(docID string) error {
	idx.index.mu.Lock()
	defer idx.index.mu.Unlock()

	doc, exists := idx.index.documents[docID]
	if !exists {
		return fmt.Errorf("document %s not found", docID)
	}

	// Remove from all posting lists
	fullText := doc.Title + " " + doc.Content
	tokens := idx.tokenizer.Tokenize(fullText)
	seen := make(map[string]bool)
	for _, tok := range tokens {
		if seen[tok] {
			continue
		}
		seen[tok] = true
		if pl, ok := idx.index.index[tok]; ok {
			newPostings := make([]Posting, 0, len(pl.Postings))
			for _, p := range pl.Postings {
				if p.DocID != docID {
					newPostings = append(newPostings, p)
				}
			}
			if len(newPostings) == 0 {
				delete(idx.index.index, tok)
			} else {
				pl.Postings = newPostings
			}
		}
	}

	// Update stats
	idx.index.totalTokens -= idx.index.docLengths[docID]
	delete(idx.index.docLengths, docID)
	delete(idx.index.documents, docID)

	return nil
}

// GetStats returns statistics about the index.
func (idx *Indexer) GetStats() IndexStats {
	idx.index.mu.RLock()
	defer idx.index.mu.RUnlock()

	return IndexStats{
		NumDocuments: len(idx.index.documents),
		NumTerms:     len(idx.index.index),
		TotalTokens:  idx.index.totalTokens,
	}
}

// GetDocument returns a document by ID.
func (idx *Indexer) GetDocument(docID string) (*Document, bool) {
	idx.index.mu.RLock()
	defer idx.index.mu.RUnlock()

	doc, ok := idx.index.documents[docID]
	if !ok {
		return nil, false
	}
	return &Document{
		ID:      doc.ID,
		Title:   doc.Title,
		Content: doc.Content,
	}, true
}

// Search performs a boolean query and returns ranked results.
func (idx *Indexer) Search(query string) []SearchResult {
	q := ParseQuery(query)
	return idx.ExecuteQuery(q)
}

// ExecuteQuery executes a parsed query and returns ranked results.
func (idx *Indexer) ExecuteQuery(q *query.Query) []SearchResult {
	idx.index.mu.RLock()
	defer idx.index.mu.RUnlock()

	var candidateDocs map[string]bool

	switch q.Operator {
	case query.OpAND:
		candidateDocs = idx.evaluateAND(q.Terms)
	case query.OpOR:
		candidateDocs = idx.evaluateOR(q.Terms)
	case query.OpNOT:
		candidateDocs = idx.evaluateNOT(q.Terms)
	default:
		candidateDocs = idx.evaluateAND(q.Terms)
	}

	// Calculate TF-IDF scores for each candidate
	results := make([]SearchResult, 0, len(candidateDocs))
	for docID := range candidateDocs {
		score := idx.calculateScore(docID, q.Terms)
		doc := idx.index.documents[docID]
		results = append(results, SearchResult{
			DocID:   docID,
			Title:   doc.Title,
			Score:   score,
			Snippet: idx.generateSnippet(doc, q.Terms),
		})
	}

	// Sort by score descending
	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	return results
}

// evaluateAND returns documents containing ALL terms.
func (idx *Indexer) evaluateAND(terms []string) map[string]bool {
	if len(terms) == 0 {
		return nil
	}

	// Start with the posting list of the first term
	firstPL, ok := idx.index.index[terms[0]]
	if !ok {
		return map[string]bool{}
	}

	result := make(map[string]bool, len(firstPL.Postings))
	for _, p := range firstPL.Postings {
		result[p.DocID] = true
	}

	// Intersect with remaining terms
	for _, term := range terms[1:] {
		pl, ok := idx.index.index[term]
		if !ok {
			return map[string]bool{}
		}
		termDocs := make(map[string]bool, len(pl.Postings))
		for _, p := range pl.Postings {
			termDocs[p.DocID] = true
		}
		for docID := range result {
			if !termDocs[docID] {
				delete(result, docID)
			}
		}
	}

	return result
}

// evaluateOR returns documents containing ANY term.
func (idx *Indexer) evaluateOR(terms []string) map[string]bool {
	result := make(map[string]bool)
	for _, term := range terms {
		pl, ok := idx.index.index[term]
		if !ok {
			continue
		}
		for _, p := range pl.Postings {
			result[p.DocID] = true
		}
	}
	return result
}

// evaluateNOT returns documents NOT containing any of the terms.
func (idx *Indexer) evaluateNOT(terms []string) map[string]bool {
	// Get all docs containing any of the excluded terms
	excluded := idx.evaluateOR(terms)

	result := make(map[string]bool)
	for docID := range idx.index.documents {
		if !excluded[docID] {
			result[docID] = true
		}
	}
	return result
}

// calculateScore computes TF-IDF score for a document given query terms.
func (idx *Indexer) calculateScore(docID string, terms []string) float64 {
	var score float64
	docLen := float64(idx.index.docLengths[docID])
	avgDocLen := float64(idx.index.totalTokens) / float64(len(idx.index.documents))
	numDocs := float64(len(idx.index.documents))

	for _, term := range terms {
		pl, ok := idx.index.index[term]
		if !ok {
			continue
		}

		// Find posting for this document
		var tf int
		var df int
		df = len(pl.Postings)
		for _, p := range pl.Postings {
			if p.DocID == docID {
				tf = p.TermFreq
				break
			}
		}

		if tf == 0 {
			continue
		}

		// BM25-like scoring
		k1 := 1.2
		b := 0.75

		tfNorm := (float64(tf) * (k1 + 1)) / (float64(tf) + k1*(1-b+b*docLen/avgDocLen))
		idf := 1.0
		if df > 0 {
			idf = (numDocs - float64(df) + 0.5) / (float64(df) + 0.5)
			if idf < 0 {
				idf = 0
			} else {
				// Use log but ensure positive
				idf = idf + 1 // shift to ensure positive before log
			}
		}
		idf = idf + 1 // Ensure positive IDF

		score += tfNorm * idf
	}

	return score
}

// generateSnippet creates a text snippet highlighting query terms.
func (idx *Indexer) generateSnippet(doc *Document, terms []string) string {
	content := doc.Content
	if len(content) > 200 {
		content = content[:200] + "..."
	}

	termSet := make(map[string]bool, len(terms))
	for _, t := range terms {
		termSet[t] = true
	}

	words := strings.Fields(content)
	var snippet []string
	count := 0
	for _, w := range words {
		clean := strings.ToLower(strings.TrimFunc(w, func(r rune) bool {
			return !('a' <= r && r <= 'z') && !('0' <= r && r <= '9')
		}))
		if termSet[clean] {
			snippet = append(snippet, "**"+w+"**")
		} else {
			snippet = append(snippet, w)
		}
		count++
		if count >= 30 {
			break
		}
	}

	return strings.Join(snippet, " ")
}
