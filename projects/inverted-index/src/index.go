// Package invertedindex implements an inverted index for text search.
//
// An inverted index maps terms (words/tokens) to the documents that contain them.
// This is the core data structure used in search engines like Elasticsearch and Lucene.
//
// Core concepts:
//   - Term: A word or token extracted from text
//   - Document: A piece of text being indexed
//   - Posting: A record of a term's occurrence in a document (includes positions)
//   - Postings list: All postings for a single term across all documents
//   - TF (Term Frequency): How often a term appears in a document
//   - DF (Document Frequency): How many documents contain a term
//   - BM25: A ranking function used to score document relevance to a query
//
// The data flow is:
//   Documents → Tokenization → Index Building → Query Parsing → Scoring → Ranked Results
package invertedindex

import (
	"sort"
	"strings"
	"sync"
)

// ============================================================
// Data Structures
// ============================================================

// Posting represents a single occurrence of a term in a document.
// It stores the document ID and the positions where the term appears.
type Posting struct {
	DocID   int
	Positions []int // word positions in the document (0-based)
}

// PostingsList is the list of all postings for a given term.
// It supports efficient union, intersection, and other boolean operations.
type PostingsList struct {
	Items []*Posting
}

// NewPostingsList creates a new empty postings list.
func NewPostingsList() *PostingsList {
	return &PostingsList{Items: make([]*Posting, 0)}
}

// Add adds a posting to the list.
func (pl *PostingsList) Add(p *Posting) {
	pl.Items = append(pl.Items, p)
}

// Len returns the number of postings in the list.
func (pl *PostingsList) Len() int {
	return len(pl.Items)
}

// Intersect returns the intersection of two postings lists (for AND queries).
// Both lists should be sorted by DocID for efficient merging.
func (pl *PostingsList) Intersect(other *PostingsList) *PostingsList {
	result := NewPostingsList()
	i, j := 0, 0
	for i < len(pl.Items) && j < len(other.Items) {
		a := pl.Items[i]
		b := other.Items[j]
		if a.DocID == b.DocID {
			// Merge positions from both postings
			merged := &Posting{
				DocID:     a.DocID,
				Positions: append(a.Positions, b.Positions...),
			}
			sort.Ints(merged.Positions)
			result.Add(merged)
			i++
			j++
		} else if a.DocID < b.DocID {
			i++
		} else {
			j++
		}
	}
	return result
}

// Union returns the union of two postings lists (for OR queries).
func (pl *PostingsList) Union(other *PostingsList) *PostingsList {
	result := NewPostingsList()
	i, j := 0, 0
	for i < len(pl.Items) && j < len(other.Items) {
		a := pl.Items[i]
		b := other.Items[j]
		if a.DocID == b.DocID {
			merged := &Posting{
				DocID:     a.DocID,
				Positions: append(a.Positions, b.Positions...),
			}
			sort.Ints(merged.Positions)
			result.Add(merged)
			i++
			j++
		} else if a.DocID < b.DocID {
			result.Add(&Posting{DocID: a.DocID, Positions: a.Positions})
			i++
		} else {
			result.Add(&Posting{DocID: b.DocID, Positions: b.Positions})
			j++
		}
	}
	// Add remaining items
	for i < len(pl.Items) {
		result.Add(&Posting{DocID: pl.Items[i].DocID, Positions: pl.Items[i].Positions})
		i++
	}
	for j < len(other.Items) {
		result.Add(&Posting{DocID: other.Items[j].DocID, Positions: other.Items[j].Positions})
		j++
	}
	return result
}

// ============================================================
// Index Entry
// ============================================================

// IndexEntry represents a term in the inverted index.
// It contains the postings list and precomputed statistics.
type IndexEntry struct {
	Term        string
	Postings    *PostingsList
	TF          map[int]int // term frequency per document: docID -> count
	DocumentFreq int        // number of documents containing this term
}

// NewIndexEntry creates a new index entry for the given term.
func NewIndexEntry(term string) *IndexEntry {
	return &IndexEntry{
		Term:     term,
		Postings: NewPostingsList(),
		TF:       make(map[int]int),
	}
}

// AddPosting adds a posting for a document and updates TF.
func (ie *IndexEntry) AddPosting(docID int, positions []int) {
	// Update term frequency
	ie.TF[docID] += 1
	// Add to postings list
	ie.Postings.Add(&Posting{DocID: docID, Positions: positions})
}

// ============================================================
// Inverted Index
// ============================================================

// InvertedIndex is the main index data structure.
// It maps terms to their postings lists and provides index building and querying interfaces.
type InvertedIndex struct {
	mu      sync.RWMutex
	entries map[string]*IndexEntry // term -> IndexEntry
	docLens map[int]int            // docID -> document length (number of tokens)
	docCount int                   // total number of documents
}

// NewInvertedIndex creates a new empty inverted index.
func NewInvertedIndex() *InvertedIndex {
	return &InvertedIndex{
		entries: make(map[string]*IndexEntry),
		docLens: make(map[int]int),
	}
}

// AddDocument adds a document to the index.
// The termFreq map should contain the precomputed term frequencies for this document.
func (idx *InvertedIndex) AddDocument(docID int, termFreq map[string][]int, docLen int) {
	idx.mu.Lock()
	defer idx.mu.Unlock()

	idx.docLens[docID] = docLen

	for term, positions := range termFreq {
		entry, exists := idx.entries[term]
		if !exists {
			entry = NewIndexEntry(term)
			idx.entries[term] = entry
		}
		entry.AddPosting(docID, positions)
	}
}

// GetEntry returns the index entry for a term, or nil if not found.
func (idx *InvertedIndex) GetEntry(term string) *IndexEntry {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	return idx.entries[term]
}

// GetPostings returns the postings list for a term.
func (idx *InvertedIndex) GetPostings(term string) *PostingsList {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	if entry, ok := idx.entries[term]; ok {
		return entry.Postings
	}
	return NewPostingsList()
}

// DocumentFreq returns the document frequency for a term.
func (idx *InvertedIndex) DocumentFreq(term string) int {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	if entry, ok := idx.entries[term]; ok {
		return entry.DocumentFreq
	}
	return 0
}

// UpdateDocumentFreq updates the document frequency after all documents are added.
func (idx *InvertedIndex) UpdateDocumentFreq(term string) {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	if entry, ok := idx.entries[term]; ok {
		entry.DocumentFreq = len(entry.Postings.Items)
	}
}

// TotalDocCount returns the total number of documents in the index.
func (idx *InvertedIndex) TotalDocCount() int {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	return idx.docCount
}

// SetDocCount sets the total number of documents.
func (idx *InvertedIndex) SetDocCount(n int) {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	idx.docCount = n
}

// DocLength returns the length (number of tokens) of a document.
func (idx *InvertedIndex) DocLength(docID int) int {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	return idx.docLens[docID]
}

// Terms returns all terms in the index.
func (idx *InvertedIndex) Terms() []string {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	terms := make([]string, 0, len(idx.entries))
	for term := range idx.entries {
		terms = append(terms, term)
	}
	sort.Strings(terms)
	return terms
}

// Size returns the number of terms in the index.
func (idx *InvertedIndex) Size() int {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	return len(idx.entries)
}

// ============================================================
// Search Result
// ============================================================

// SearchResult represents a single search result with its relevance score.
type SearchResult struct {
	DocID    int
	Score    float64
	TermFreq int // TF of the query term in this document
}

// Results is a sortable list of search results.
type Results []*SearchResult

// Len, Less, Swap implement sort.Interface.
func (r Results) Len() int      { return len(r) }
func (r Results) Less(i, j int) bool { return r[i].Score > r[j].Score }
func (r Results) Swap(i, j int) { r[i], r[j] = r[j], r[i] }

// SortResults sorts results by score in descending order.
func SortResults(results Results) {
	sort.Sort(results)
}

// ============================================================
// BM25 Scoring
// ============================================================

// BM25Config holds the configuration parameters for the BM25 scoring algorithm.
//
// BM25 (Best Matching 25) is a ranking function used by search engines to estimate
// the relevance of a document to a given query. It improves upon TF-IDF by:
//   - Using term frequency saturation (diminishing returns for high TF)
//   - Normalizing for document length
//   - Using average document length for better cross-document comparison
//
// The formula is:
//   score(d,q) = Σ TF(t,d) * (k1 + 1) / (TF(t,d) + k1 * (1 - b + b * |d|/avgdl)) * IDF(t)
//
// where IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
type BM25Config struct {
	K1 float64 // Term frequency saturation parameter (typically 1.2-2.0)
	B  float64 // Document length normalization parameter (typically 0.75)
}

// DefaultBM25Config returns the standard BM25 parameters.
func DefaultBM25Config() BM25Config {
	return BM25Config{K1: 1.5, B: 0.75}
}

// BM25Score computes the BM25 score for a term in a document.
//
// Parameters:
//   - termFreq: TF(t, d) - number of times term t appears in document d
//   - docLen: length of document d (number of tokens)
//   - docFreq: DF(t) - number of documents containing term t
//   - totalDocs: total number of documents in the index
//   - avgDocLen: average document length across the index
//   - cfg: BM25 configuration parameters
func BM25Score(termFreq, docLen, docFreq, totalDocs int, avgDocLen float64, cfg BM25Config) float64 {
	if docLen == 0 || avgDocLen == 0 {
		return 0
	}

	// IDF component: log((N - df + 0.5) / (df + 0.5) + 1)
	// This gives higher weight to rarer terms
	numerator := float64(totalDocs - docFreq + 0.5)
	denominator := float64(docFreq + 0.5)
	idf := log1p(numerator / denominator)

	// TF component with saturation
	// Without saturation: score would grow linearly with term frequency
	// With saturation: additional occurrences have diminishing returns
	tf := float64(termFreq)
	k1 := cfg.K1
	b := cfg.B
	docLenNorm := 1.0 - b + b*(float64(docLen)/avgDocLen)
	tfScore := (k1 + 1.0) * tf / (tf + k1*docLenNorm)

	return tfScore * idf
}

// log1p computes log(1 + x) accurately for small x values.
func log1p(x float64) float64 {
	if x < 1e-10 {
		return x
	}
	return log(x)
}

// log computes natural logarithm using the math approximation.
// We avoid importing math to keep the project dependency-free for learning purposes.
func log(x float64) float64 {
	if x <= 0 {
		return 0
	}
	// Use the series expansion: ln(x) = 2 * sum((1/(2k+1)) * ((x-1)/(x+1))^(2k+1))
	// This converges faster than the basic Taylor series
	y := (x - 1) / (x + 1)
	y2 := y * y
	result := 0.0
	term := y
	for i := 0; i < 50; i++ {
		result += term / float64(2*i+1)
		term *= y2
	}
	return 2 * result
}

// ============================================================
// Average Document Length Computation
// ============================================================

// AverageDocLen computes the average document length across all documents.
func AverageDocLen(idx *InvertedIndex) float64 {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	totalLen := 0
	count := len(idx.docLens)
	if count == 0 {
		return 0
	}
	for _, l := range idx.docLens {
		totalLen += l
	}
	return float64(totalLen) / float64(count)
}

// ============================================================
// Tokenization
// ============================================================

// Token represents a single token from text.
type Token struct {
	Text     string
	Position int // 0-based position in the original text
}

// Tokenize splits text into tokens.
// For English: splits on whitespace and punctuation.
// For Chinese: uses character-level tokenization as a simple baseline.
// For mixed text: tries to detect Chinese characters and tokenize accordingly.
func Tokenize(text string) []Token {
	text = strings.ToLower(strings.TrimSpace(text))
	if text == "" {
		return nil
	}

	// Check if text contains Chinese characters
	hasChinese := false
	for _, r := range text {
		if r >= '\u4e00' && r <= '\u9fff' {
			hasChinese = true
			break
		}
	}

	if hasChinese {
		return tokenizeMixed(text)
	}

	return tokenizeEnglish(text)
}

// tokenizeEnglish splits English text into words.
func tokenizeEnglish(text string) []Token {
	tokens := make([]Token, 0)
	position := 0
	var current []rune

	for _, r := range text {
		if isWordChar(r) {
			current = append(current, r)
		} else {
			if len(current) > 0 {
				tokens = append(tokens, Token{
					Text:     string(current),
					Position: position,
				})
				position += len(current)
				current = nil
			}
			// Skip non-word characters
			position++
		}
	}

	// Don't forget the last word
	if len(current) > 0 {
		tokens = append(tokens, Token{
			Text:     string(current),
			Position: position,
		})
	}

	return tokens
}

// tokenizeMixed handles text containing both Chinese and non-Chinese characters.
func tokenizeMixed(text string) []Token {
	tokens := make([]Token, 0)
	position := 0
	var chineseBuf []rune
	var current []rune

	for _, r := range text {
		if r >= '\u4e00' && r <= '\u9fff' {
			// Flush any pending English word
			if len(current) > 0 {
				tokens = append(tokens, Token{
					Text:     string(current),
					Position: position,
				})
				position += len(current)
				current = nil
			}
			chineseBuf = append(chineseBuf, r)
		} else {
			// Flush Chinese characters (character-level tokenization)
			if len(chineseBuf) > 0 {
				for _, cr := range chineseBuf {
					tokens = append(tokens, Token{
						Text:     string(cr),
						Position: position,
					})
					position++
				}
				chineseBuf = nil
			}
			if isWordChar(r) {
				current = append(current, r)
			} else {
				if len(current) > 0 {
					tokens = append(tokens, Token{
						Text:     string(current),
						Position: position,
					})
					position += len(current)
					current = nil
				}
				position++
			}
		}
	}

	// Flush remaining buffers
	if len(current) > 0 {
		tokens = append(tokens, Token{
			Text:     string(current),
			Position: position,
		})
	}
	if len(chineseBuf) > 0 {
		for _, cr := range chineseBuf {
			tokens = append(tokens, Token{
				Text:     string(cr),
				Position: position,
			})
			position++
		}
	}

	return tokens
}

// isWordChar checks if a rune is a word character (letter, digit, or underscore).
func isWordChar(r rune) bool {
	return (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') ||
		(r >= '0' && r <= '9') || r == '_' ||
		(r >= '\u4e00' && r <= '\u9fff')
}

// ============================================================
// Query Types
// ============================================================

// QueryType represents the type of a query.
type QueryType int

const (
	// QueryTerm is a single term query.
	QueryTerm QueryType = iota
	// QueryAnd is a boolean AND query.
	QueryAnd
	// QueryOr is a boolean OR query.
	QueryOr
	// QueryPhrase is a phrase query (exact word sequence).
	QueryPhrase
)

// Query represents a parsed search query.
type Query struct {
	Type    QueryType
	Term    string          // For single term / phrase queries
	Terms   []string        // For AND/OR queries
	Phrase  string          // For phrase queries
	Positions map[int]int  // For phrase queries: position -> term mapping
}

// ============================================================
// Query Parser
// ============================================================

// QueryParser parses query strings into Query objects.
//
// Supported query syntax:
//   - Single term: "search"
//   - AND query: "search AND engine"
//   - OR query: "search OR engine"
//   - Phrase query: "search engine" (quoted)
//
// Examples:
//   "go programming"        -> Phrase query
//   "go AND programming"    -> AND query
//   "go OR python"          -> OR query
//   "search"                -> Single term query
type QueryParser struct{}

// NewQueryParser creates a new query parser.
func NewQueryParser() *QueryParser {
	return &QueryParser{}
}

// Parse parses a query string into a Query object.
func (qp *QueryParser) Parse(queryStr string) (*Query, error) {
	queryStr = strings.TrimSpace(queryStr)
	if queryStr == "" {
		return nil, &QueryParseError{"empty query"}
	}

	// Check for phrase query (quoted string)
	if strings.HasPrefix(queryStr, `"`) && strings.HasSuffix(queryStr, `"`) {
		phrase := queryStr[1 : len(queryStr)-1]
		return &Query{
			Type:    QueryPhrase,
			Phrase:  phrase,
			Terms:   tokenizePhrase(phrase),
			Positions: make(map[int]int),
		}, nil
	}

	// Check for AND query
	if strings.Contains(queryStr, " AND ") {
		parts := strings.Split(queryStr, " AND ")
		terms := make([]string, len(parts))
		for i, p := range parts {
			terms[i] = strings.ToLower(strings.TrimSpace(p))
		}
		return &Query{Type: QueryAnd, Terms: terms}, nil
	}

	// Check for OR query
	if strings.Contains(queryStr, " OR ") {
		parts := strings.Split(queryStr, " OR ")
		terms := make([]string, len(parts))
		for i, p := range parts {
			terms[i] = strings.ToLower(strings.TrimSpace(p))
		}
		return &Query{Type: QueryOr, Terms: terms}, nil
	}

	// Single term query
	term := strings.ToLower(queryStr)
	return &Query{Type: QueryTerm, Term: term}, nil
}

// tokenizePhrase tokenizes a phrase into terms.
func tokenizePhrase(phrase string) []string {
	tokens := Tokenize(phrase)
	terms := make([]string, len(tokens))
	for i, t := range tokens {
		terms[i] = t.Text
	}
	return terms
}

// QueryParseError represents an error during query parsing.
type QueryParseError struct {
	Message string
}

func (e *QueryParseError) Error() string {
	return "query parse error: " + e.Message
}

// ============================================================
// Index Persistence
// ============================================================

// IndexStats holds metadata about the index for persistence.
type IndexStats struct {
	DocCount    int
	TermCount   int
	AvgDocLen   float64
	TotalTokens int
}

// IndexData holds the serializable data for the inverted index.
type IndexData struct {
	Stats    IndexStats
	Docs     map[int]DocData
	Terms    map[string]TermData
}

// DocData holds document data for serialization.
type DocData struct {
	Length int
}

// TermData holds term data for serialization.
type TermData struct {
	DocumentFreq int
	Postings     []PostingData
}

// PostingData holds posting data for serialization.
type PostingData struct {
	DocID     int
	Positions []int
}

// Save serializes the index to IndexData.
func (idx *InvertedIndex) Save() *IndexData {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	data := &IndexData{
		Stats: IndexStats{
			DocCount:  idx.docCount,
			TermCount: len(idx.entries),
			Docs:      make(map[int]DocData),
			Terms:     make(map[string]TermData),
		},
		Docs:  make(map[int]DocData),
		Terms: make(map[string]TermData),
	}

	// Save document lengths
	for docID, length := range idx.docLens {
		data.Docs[docID] = DocData{Length: length}
	}

	// Save index entries
	for term, entry := range idx.entries {
		termData := TermData{
			DocumentFreq: entry.DocumentFreq,
			Postings:     make([]PostingData, len(entry.Postings.Items)),
		}
		for i, p := range entry.Postings.Items {
			termData.Postings[i] = PostingData{
				DocID:     p.DocID,
				Positions: p.Positions,
			}
		}
		data.Terms[term] = termData
	}

	return data
}

// Load reconstructs an index from serialized data.
func Load(data *IndexData) *InvertedIndex {
	idx := NewInvertedIndex()
	idx.SetDocCount(data.Stats.DocCount)

	// Restore document lengths
	for docID, docData := range data.Docs {
		idx.docLens[docID] = docData.Length
	}

	// Restore index entries
	for term, termData := range data.Terms {
		entry := NewIndexEntry(term)
		entry.DocumentFreq = termData.DocumentFreq
		for _, p := range termData.Postings {
			entry.AddPosting(p.DocID, p.Positions)
		}
		idx.entries[term] = entry
	}

	return idx
}
