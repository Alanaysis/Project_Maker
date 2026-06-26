// Package queryparser implements a search query parser with support for
// boolean queries, phrase queries, fuzzy matching, wildcards, and range queries.
//
// # Query Parsing Flow
//
// The parser follows a recursive descent approach:
//
//	查询字符串 → Tokenizer → TokenStream → Parser → QueryTree → Execution → Ranking
//
// # Architecture
//
//   Tokenizer: Breaks query strings into lexical tokens (terms, operators, quotes)
//   Parser:    Converts token stream into an abstract syntax tree (AST)
//   QueryTree: Represents the parsed query as a tree of query nodes
//   Normalizer: Normalizes queries (lowercasing, stop word removal)
//   Statistics: Collects metrics about parsed queries
package queryparser

import (
	"fmt"
	"strings"
	"unicode"
	"unicode/utf8"
)

// TokenType represents the type of a lexical token.
type TokenType int

const (
	// TokenWord is a regular search term (e.g., "golang")
	TokenWord TokenType = iota
	// TokenAND is the boolean AND operator
	TokenAND
	// TokenOR is the boolean OR operator
	TokenOR
	// TokenNOT is the boolean NOT operator
	TokenNOT
	// TokenLParen is a left parenthesis
	TokenLParen
	// TokenRParen is a right parenthesis
	TokenRParen
	// TokenPhraseStart marks the beginning of a phrase (double quote)
	TokenPhraseStart
	// TokenPhraseEnd marks the end of a phrase (double quote)
	TokenPhraseEnd
	// TokenWildcard marks a wildcard (*) in a term
	TokenWildcard
	// TokenSingleWildcard marks a single-character wildcard (?)
	TokenSingleWildcard
	// TokenRangeStart marks the start of a range query ([ or {)
	TokenRangeStart
	// TokenRangeEnd marks the end of a range query (] or })
	TokenRangeEnd
	// TokenComma separates range bounds
	TokenComma
	// TokenEof marks end of input
	TokenEof
)

// String returns a human-readable name for the token type.
func (t TokenType) String() string {
	switch t {
	case TokenWord:
		return "WORD"
	case TokenAND:
		return "AND"
	case TokenOR:
		return "OR"
	case TokenNOT:
		return "NOT"
	case TokenLParen:
		return "("
	case TokenRParen:
		return ")"
	case TokenPhraseStart:
		return "PHRASE_START"
	case TokenPhraseEnd:
		return "PHRASE_END"
	case TokenWildcard:
		return "*"
	case TokenSingleWildcard:
		return "?"
	case TokenRangeStart:
		return "RANGE_START"
	case TokenRangeEnd:
		return "RANGE_END"
	case TokenComma:
		return ","
	case TokenEof:
		return "EOF"
	default:
		return "UNKNOWN"
	}
}

// Token represents a single lexical unit from the query string.
type Token struct {
	Type   TokenType
	Value  string // The actual text (e.g., "golang" for TokenWord)
	Pos    int    // Position in the original query string
	Length int    // Length of the token in runes
}

// String returns the token as a string representation.
func (t Token) String() string {
	return fmt.Sprintf("%s(%q@%d)", t.Type, t.Value, t.Pos)
}

// QueryNodeType identifies the kind of node in a query tree.
type QueryNodeType int

const (
	// NodeTerm is a single term query (e.g., "golang")
	NodeTerm QueryNodeType = iota
	// NodeBoolean is a boolean combination of queries (AND/OR/NOT)
	NodeBoolean
	// NodePhrase is an exact phrase query (e.g., "go language")
	NodePhrase
	// NodeFuzzy is a fuzzy match query (e.g., "golan~")
	NodeFuzzy
	// NodeWildcard is a wildcard query (e.g., "go*")
	NodeWildcard
	// NodeRange is a range query (e.g., "price:[10 TO 100]")
	NodeRange
	// NodeBoosted is a query with boost weight (e.g., "golang^2.0")
	NodeBoosted
)

// String returns a human-readable name for the query node type.
func (n QueryNodeType) String() string {
	switch n {
	case NodeTerm:
		return "TERM"
	case NodeBoolean:
		return "BOOLEAN"
	case NodePhrase:
		return "PHRASE"
	case NodeFuzzy:
		return "FUZZY"
	case NodeWildcard:
		return "WILDCARD"
	case NodeRange:
		return "RANGE"
	case NodeBoosted:
		return "BOOSTED"
	default:
		return "UNKNOWN"
	}
}

// BooleanOperator represents the type of boolean operation.
type BooleanOperator int

const (
	// BoolAnd requires all child queries to match
	BoolAnd BooleanOperator = iota
	// BoolOr requires at least one child query to match
	BoolOr
	// BoolNot requires the child query to NOT match
	BoolNot
)

// String returns a human-readable name for the boolean operator.
func (b BooleanOperator) String() string {
	switch b {
	case BoolAnd:
		return "AND"
	case BoolOr:
		return "OR"
	case BoolNot:
		return "NOT"
	default:
		return "UNKNOWN"
	}
}

// QueryNode represents a node in the query tree (AST).
// Each node type carries the fields relevant to that query type.
type QueryNode struct {
	Type       QueryNodeType
	Value      string            // The term or text this node represents
	Operator   BooleanOperator   // For NodeBoolean: the boolean operator
	Children   []*QueryNode      // Child nodes (for NodeBoolean)
	Boost      float64           // Boost weight (default 1.0)
	FuzzyDist  int               // Maximum Levenshtein distance for fuzzy queries
	MinChars   int               // Minimum length for wildcard/fuzzy queries
	LowerBound string            // Lower bound for range queries
	UpperBound string            // Upper bound for range queries
	Inclusive  bool              // Whether range bounds are inclusive
	Position   int               // Original position in query string
}

// String returns a string representation of the query node.
func (n *QueryNode) String() string {
	return fmt.Sprintf("%s(%q)", n.Type, n.Value)
}

// QueryTree is the root of the parsed query tree.
type QueryTree struct {
	Root     *QueryNode
	Original string // The original query string
}

// QueryStats collects statistics about parsed queries.
type QueryStats struct {
	TotalQueries   int            // Number of queries parsed
	TotalTerms     int            // Total number of term nodes
	TotalBoolean   int            // Total number of boolean nodes
	TotalPhrases   int            // Total number of phrase nodes
	TotalFuzzy     int            // Total number of fuzzy nodes
	TotalWildcard  int            // Total number of wildcard nodes
	TotalRange     int            // Total number of range nodes
	MaxDepth       int            // Maximum tree depth
	TotalTokens    int            // Total tokens in the last query
	HasWildcard    bool           // Whether the last query has wildcards
	HasFuzzy       bool           // Whether the last query has fuzzy terms
	HasPhrase      bool           // Whether the last query has phrases
	HasRange       bool           // Whether the last query has range queries
	HasBoost       bool           // Whether the last query has boosts
	HasBoolean     bool           // Whether the last query has boolean operators
}

// NewQueryStats creates a fresh QueryStats instance.
func NewQueryStats() *QueryStats {
	return &QueryStats{}
}

// Reset clears all statistics for a new query.
func (s *QueryStats) Reset() {
	*s = *NewQueryStats()
}

// CollectStats walks the query tree and populates the stats.
func (s *QueryStats) CollectStats(tree *QueryTree) {
	s.TotalQueries++
	s.Original = tree.Original
	s.collectNode(tree.Root, 0)
}

// collectNode recursively walks the tree and counts nodes.
func (s *QueryStats) collectNode(node *QueryNode, depth int) {
	if node == nil {
		return
	}

	// Track max depth
	if depth > s.MaxDepth {
		s.MaxDepth = depth
	}

	// Count by node type
	switch node.Type {
	case NodeTerm:
		s.TotalTerms++
	case NodeBoolean:
		s.TotalBoolean++
	case NodePhrase:
		s.TotalPhrases++
	case NodeFuzzy:
		s.TotalFuzzy++
	case NodeWildcard:
		s.TotalWildcard++
	case NodeRange:
		s.TotalRange++
	}

	// Collect per-query flags
	if node.Type == NodeWildcard {
		s.HasWildcard = true
	}
	if node.Type == NodeFuzzy {
		s.HasFuzzy = true
	}
	if node.Type == NodePhrase {
		s.HasPhrase = true
	}
	if node.Type == NodeRange {
		s.HasRange = true
	}
	if node.Boost != 1.0 {
		s.HasBoost = true
	}

	// Recurse into children
	for _, child := range node.Children {
		s.collectNode(child, depth+1)
	}
}

// StopWords is a set of common English stop words to filter out during normalization.
var StopWords = map[string]bool{
	"a": true, "an": true, "the": true,
	"and": true, "or": true, "not": true,
	"in": true, "on": true, "at": true,
	"to": true, "for": true, "of": true,
	"with": true, "is": true, "it": true,
	"as": true, "by": true, "from": true,
	"be": true, "are": true, "was": true,
	"were": true, "been": true, "have": true,
	"has": true, "had": true, "do": true,
	"does": true, "did": true, "will": true,
	"would": true, "could": true, "should": true,
	"may": true, "might": true, "can": true,
	"this": true, "that": true, "these": true,
	"those": true, "which": true, "who": true,
	"whom": true, "what": true, "where": true,
	"when": true, "why": true, "how": true,
}

// isStopWord checks if a term is a stop word.
func isStopWord(term string) bool {
	return StopWords[strings.ToLower(term)]
}

// normalizeTerm normalizes a term: lowercases it and strips trailing wildcards for storage.
func normalizeTerm(term string) string {
	return strings.ToLower(strings.TrimSpace(term))
}
