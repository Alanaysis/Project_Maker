package query

import (
	"strings"
)

// Operator represents a boolean query operator.
type Operator int

const (
	OpAND Operator = iota
	OpOR
	OpNOT
)

// Query represents a parsed boolean query.
type Query struct {
	Operator Operator
	Terms    []string
	Raw      string
}

// ParseQuery parses a query string into a Query object.
//
// Supported syntax:
//   - "term1 term2"      -> AND query (default)
//   - "term1 OR term2"   -> OR query
//   - "NOT term1"        -> NOT query (exclude documents with term)
//   - "term1 AND term2"  -> explicit AND query
func ParseQuery(raw string) *Query {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return &Query{Operator: OpAND, Raw: raw}
	}

	// Check for NOT at the beginning
	upper := strings.ToUpper(raw)
	if strings.HasPrefix(upper, "NOT ") {
		terms := tokenizeQuery(raw[4:])
		return &Query{
			Operator: OpNOT,
			Terms:    terms,
			Raw:      raw,
		}
	}

	// Check for OR operator
	if strings.Contains(upper, " OR ") {
		parts := strings.Split(upper, " OR ")
		var terms []string
		for _, p := range parts {
			t := tokenizeQuery(p)
			terms = append(terms, t...)
		}
		return &Query{
			Operator: OpOR,
			Terms:    terms,
			Raw:      raw,
		}
	}

	// Check for explicit AND
	if strings.Contains(upper, " AND ") {
		parts := strings.Split(upper, " AND ")
		var terms []string
		for _, p := range parts {
			t := tokenizeQuery(p)
			terms = append(terms, t...)
		}
		return &Query{
			Operator: OpAND,
			Terms:    terms,
			Raw:      raw,
		}
	}

	// Default: AND query
	terms := tokenizeQuery(raw)
	return &Query{
		Operator: OpAND,
		Terms:    terms,
		Raw:      raw,
	}
}

func tokenizeQuery(s string) []string {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	words := strings.Fields(s)
	var terms []string
	for _, w := range words {
		w = strings.ToLower(w)
		if w != "and" && w != "or" && w != "not" {
			terms = append(terms, w)
		}
	}
	return terms
}
