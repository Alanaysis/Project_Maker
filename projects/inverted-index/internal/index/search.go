package index

import "github.com/copyninja/inverted-index/internal/query"

// SearchResult represents a single search result.
type SearchResult struct {
	DocID   string
	Title   string
	Score   float64
	Snippet string
}

// ParseQuery re-exports the query parser for convenience.
func ParseQuery(raw string) *query.Query {
	return query.ParseQuery(raw)
}
