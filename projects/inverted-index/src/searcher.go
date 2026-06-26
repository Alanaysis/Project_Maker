// Package invertedindex implements an inverted index for text search.
// This file contains the Searcher which handles query execution and scoring.

package invertedindex

import "sort"

// Searcher executes queries against the inverted index and returns ranked results.
type Searcher struct {
	index *InvertedIndex
	cfg   BM25Config
}

// NewSearcher creates a new searcher for the given index.
func NewSearcher(index *InvertedIndex) *Searcher {
	return &Searcher{
		index: index,
		cfg:   DefaultBM25Config(),
	}
}

// SetConfig sets the BM25 configuration.
func (s *Searcher) SetConfig(cfg BM25Config) {
	s.cfg = cfg
}

// Search executes a query and returns the top-k results.
//
// The search process:
//   1. Parse the query string
//   2. Execute based on query type (term, AND, OR, phrase)
//   3. Score each matching document using BM25
//   4. Sort by score and return top-k results
func (s *Searcher) Search(queryStr string, topK int) (Results, error) {
	parser := NewQueryParser()
	query, err := parser.Parse(queryStr)
	if err != nil {
		return nil, err
	}

	return s.searchQuery(query, topK)
}

// searchQuery executes a parsed query against the index.
func (s *Searcher) searchQuery(query *Query, topK int) (Results, error) {
	var postings *PostingsList

	switch query.Type {
	case QueryTerm:
		postings = s.index.GetPostings(query.Term)
	case QueryAnd:
		postings = s.searchAnd(query)
	case QueryOr:
		postings = s.searchOr(query)
	case QueryPhrase:
		return s.searchPhrase(query, topK)
	}

	if postings == nil || postings.Len() == 0 {
		return Results{}, nil
	}

	// Score each document using BM25
	avgDocLen := AverageDocLen(s.index)
	totalDocs := s.index.TotalDocCount()
	results := make(Results, 0)

	for _, p := range postings.Items {
		// Get term frequency for this document
		var tf int
		if query.Type == QueryTerm || query.Type == QueryPhrase {
			// For single term / phrase, get TF of the query term
			if entry := s.index.GetEntry(query.Term); entry != nil {
				tf = entry.TF[p.DocID]
			}
		} else {
			// For AND/OR queries, sum TF of all query terms
			for _, term := range query.Terms {
				if entry := s.index.GetEntry(term); entry != nil {
					tf += entry.TF[p.DocID]
				}
			}
		}

		docLen := s.index.DocLength(p.DocID)
		var df int
		if query.Type == QueryTerm || query.Type == QueryPhrase {
			df = s.index.DocumentFreq(query.Term)
		} else {
			// For boolean queries, use the postings list size as DF
			df = postings.Len()
		}

		score := BM25Score(tf, docLen, df, totalDocs, avgDocLen, s.cfg)
		if score > 0 {
			results = append(results, &SearchResult{
				DocID:    p.DocID,
				Score:    score,
				TermFreq: tf,
			})
		}
	}

	// Sort by score descending
	sort.Sort(results)

	// Return top-k
	if topK > 0 && len(results) > topK {
		results = results[:topK]
	}

	return results, nil
}

// searchAnd executes a boolean AND query.
func (s *Searcher) searchAnd(query *Query) *PostingsList {
	if len(query.Terms) == 0 {
		return nil
	}

	// Get postings for the first term
	var postings *PostingsList
	for i, term := range query.Terms {
		if i == 0 {
			postings = s.index.GetPostings(term)
			continue
		}
		// Intersect with subsequent terms
		other := s.index.GetPostings(term)
		if postings.Len() == 0 || other.Len() == 0 {
			return NewPostingsList()
		}
		postings = postings.Intersect(other)
	}

	return postings
}

// searchOr executes a boolean OR query.
func (s *Searcher) searchOr(query *Query) *PostingsList {
	if len(query.Terms) == 0 {
		return nil
	}

	var postings *PostingsList
	for i, term := range query.Terms {
		other := s.index.GetPostings(term)
		if i == 0 {
			postings = other
			continue
		}
		if postings.Len() == 0 {
			postings = other
		} else {
			postings = postings.Union(other)
		}
	}

	return postings
}

// searchPhrase executes a phrase query.
// A phrase query requires terms to appear in the exact specified order.
func (s *Searcher) searchPhrase(query *Query, topK int) (Results, error) {
	if len(query.Terms) == 0 {
		return Results{}, nil
	}

	// Get postings for each term in the phrase
	postings := make([]*PostingsList, len(query.Terms))
	for i, term := range query.Terms {
		postings[i] = s.index.GetPostings(term)
	}

	// Find documents containing the phrase
	// A document matches if it has all terms in the correct order with correct spacing
	docScores := make(map[int]float64)
	docTermFreqs := make(map[int]int)

	// Start with the first term's postings
	for _, p := range postings[0].Items {
		// Check if the phrase exists at this position
		if s.checkPhrase(p.DocID, p.Positions, query.Terms, postings) {
			docScores[p.DocID] += 1.0 // phrase match bonus
			docTermFreqs[p.DocID]++
		}
	}

	// Score documents
	if len(docScores) == 0 {
		return Results{}, nil
	}

	avgDocLen := AverageDocLen(s.index)
	totalDocs := s.index.TotalDocCount()
	results := make(Results, 0)

	for docID, phraseCount := range docScores {
		// Use phrase count as a multiplier for BM25
		bm25 := BM25Score(
			docTermFreqs[docID],
			s.index.DocLength(docID),
			s.index.DocumentFreq(query.Terms[0]),
			totalDocs,
			avgDocLen,
			s.cfg,
		)
		score := bm25 * (1.0 + phraseCount*0.5) // phrase match bonus
		results = append(results, &SearchResult{
			DocID:    docID,
			Score:    score,
			TermFreq: docTermFreqs[docID],
		})
	}

	sort.Sort(results)

	if topK > 0 && len(results) > topK {
		results = results[:topK]
	}

	return results, nil
}

// checkPhrase checks if a phrase exists in a document starting from the given positions.
func (s *Searcher) checkPhrase(docID int, startPositions []int, terms []string, postings []*PostingsList) bool {
	// For each starting position, check if the full phrase exists
	for _, startPos := range startPositions {
		if s.checkPhraseAt(docID, startPos, terms, postings) {
			return true
		}
	}
	return false
}

// checkPhraseAt checks if the phrase exists starting at a specific position.
func (s *Searcher) checkPhraseAt(docID int, startPos int, terms []string, postings []*PostingsList) bool {
	for i := 1; i < len(terms); i++ {
		expectedPos := startPos + i
		found := false
		for _, pos := range postings[i].Items {
			if pos.DocID == docID {
				for _, p := range pos.Positions {
					if p == expectedPos {
						found = true
						break
					}
				}
			}
			if found {
				break
			}
		}
		if !found {
			return false
		}
	}
	return true
}
