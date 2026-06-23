package executor

import (
	"query-parser/internal/ast"
	"query-parser/internal/index"
	"sort"
	"strings"
)

// SearchResult represents a search result with relevance score
type SearchResult struct {
	DocID   string
	Score   float64
	Content string
}

// Executor executes queries against an index
type Executor struct {
	index *index.Index
}

// New creates a new Executor
func New(idx *index.Index) *Executor {
	return &Executor{index: idx}
}

// Execute executes a query AST and returns search results
func (e *Executor) Execute(node *ast.Node) []SearchResult {
	if node == nil {
		return nil
	}

	// Get all matching document IDs
	docIDs := e.executeNode(node)

	// Calculate scores and build results
	results := make([]SearchResult, 0, len(docIDs))
	for _, docID := range docIDs {
		doc := e.index.GetDocument(docID)
		if doc != nil {
			score := e.calculateScore(node, doc)
			results = append(results, SearchResult{
				DocID:   docID,
				Score:   score,
				Content: doc.Content,
			})
		}
	}

	// Sort by score (descending)
	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	return results
}

// executeNode returns a set of document IDs matching the node
func (e *Executor) executeNode(node *ast.Node) []string {
	if node == nil {
		return nil
	}

	switch node.Type {
	case ast.NodeTerm:
		return e.executeTerm(node.Value)
	case ast.NodePhrase:
		return e.executePhrase(node.Value)
	case ast.NodeAnd:
		return e.executeAnd(node.Left, node.Right)
	case ast.NodeOr:
		return e.executeOr(node.Left, node.Right)
	case ast.NodeNot:
		return e.executeNot(node.Children[0])
	default:
		return nil
	}
}

// executeTerm searches for documents containing a term
func (e *Executor) executeTerm(term string) []string {
	return e.index.Search(term)
}

// executePhrase searches for documents containing a phrase
func (e *Executor) executePhrase(phrase string) []string {
	words := strings.Fields(phrase)
	if len(words) == 0 {
		return nil
	}

	// Get documents containing all words
	result := e.index.Search(words[0])
	if len(words) == 1 {
		return result
	}

	// Intersect with documents containing other words
	for _, word := range words[1:] {
		docs := e.index.Search(word)
		result = intersect(result, docs)
	}

	// Filter to only documents that contain the exact phrase
	var filtered []string
	for _, docID := range result {
		doc := e.index.GetDocument(docID)
		if doc != nil && strings.Contains(strings.ToLower(doc.Content), strings.ToLower(phrase)) {
			filtered = append(filtered, docID)
		}
	}

	return filtered
}

// executeAnd returns documents in both left and right
func (e *Executor) executeAnd(left, right *ast.Node) []string {
	leftDocs := e.executeNode(left)
	rightDocs := e.executeNode(right)
	return intersect(leftDocs, rightDocs)
}

// executeOr returns documents in either left or right
func (e *Executor) executeOr(left, right *ast.Node) []string {
	leftDocs := e.executeNode(left)
	rightDocs := e.executeNode(right)
	return union(leftDocs, rightDocs)
}

// executeNot returns documents NOT in the child
func (e *Executor) executeNot(child *ast.Node) []string {
	childDocs := e.executeNode(child)
	allDocs := e.index.AllDocuments()
	return difference(allDocs, childDocs)
}

// calculateScore calculates relevance score for a document
func (e *Executor) calculateScore(node *ast.Node, doc *index.Document) float64 {
	terms := node.CollectTerms()
	if len(terms) == 0 {
		return 0
	}

	score := 0.0
	content := strings.ToLower(doc.Content)

	for _, term := range terms {
		termLower := strings.ToLower(term)

		// Count occurrences
		count := strings.Count(content, termLower)
		if count == 0 {
			continue
		}

		// TF (Term Frequency) score
		tf := float64(count)

		// IDF-like score (simplified)
		docCount := len(e.index.Search(term))
		totalDocs := e.index.DocumentCount()
		idf := 1.0
		if docCount > 0 && totalDocs > 0 {
			idf = 1.0 + float64(totalDocs)/float64(docCount)
		}

		score += tf * idf
	}

	return score
}

// intersect returns the intersection of two sorted string slices
func intersect(a, b []string) []string {
	set := make(map[string]bool)
	for _, s := range a {
		set[s] = true
	}

	var result []string
	for _, s := range b {
		if set[s] {
			result = append(result, s)
			delete(set, s)
		}
	}
	return result
}

// union returns the union of two string slices
func union(a, b []string) []string {
	set := make(map[string]bool)
	for _, s := range a {
		set[s] = true
	}
	for _, s := range b {
		set[s] = true
	}

	result := make([]string, 0, len(set))
	for s := range set {
		result = append(result, s)
	}
	return result
}

// difference returns elements in a but not in b
func difference(a, b []string) []string {
	set := make(map[string]bool)
	for _, s := range b {
		set[s] = true
	}

	var result []string
	for _, s := range a {
		if !set[s] {
			result = append(result, s)
		}
	}
	return result
}
