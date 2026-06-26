package queryparser

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// LevenshteinDistance computes the Levenshtein (edit) distance between two strings.
// Exported version of levenshteinDistance for use by examples and external packages.
func LevenshteinDistance(s1, s2 string) int {
	return levenshteinDistance(s1, s2)
}

// levenshteinDistance computes the Levenshtein (edit) distance between two strings.
//
// The Levenshtein distance measures the minimum number of single-character edits
// (insertions, deletions, or substitutions) required to change one string into another.
//
// This is the core algorithm for fuzzy matching in query parsers.
//
// # Algorithm
//
// Uses dynamic programming with O(m*n) time and O(min(m,n)) space complexity.
//
// # Example
//
//	levenshteinDistance("kitten", "sitting") → 3
//	  (k→s, e→i, insert g)
func levenshteinDistance(s1, s2 string) int {
	// Convert to rune slices for proper Unicode handling
	r1 := []rune(s1)
	r2 := []rune(s2)

	len1 := len(r1)
	len2 := len(r2)

	// Use two rows for space optimization
	prevRow := make([]int, len2+1)
	currRow := make([]int, len2+1)

	// Initialize first row
	for j := 0; j <= len2; j++ {
		prevRow[j] = j
	}

	// Fill the table
	for i := 1; i <= len1; i++ {
		currRow[0] = i

		for j := 1; j <= len2; j++ {
			cost := 1
			if r1[i-1] == r2[j-1] {
				cost = 0
			}

			// Take minimum of deletion, insertion, substitution
			del := prevRow[j] + 1
			insert := currRow[j-1] + 1
			sub := prevRow[j-1] + cost

			currRow[j] = minInt(del, minInt(insert, sub))
		}

		// Swap rows
		prevRow, currRow = currRow, prevRow
	}

	return prevRow[len2]
}

// minInt returns the minimum of two integers.
func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// FuzzyMatcher handles fuzzy matching using Levenshtein distance.
type FuzzyMatcher struct {
	MaxDistance int // Maximum allowed edit distance (default: 2)
	MinLength   int // Minimum term length for fuzzy matching (default: 3)
}

// NewFuzzyMatcher creates a fuzzy matcher with default settings.
func NewFuzzyMatcher() *FuzzyMatcher {
	return &FuzzyMatcher{
		MaxDistance: 2,
		MinLength:   3,
	}
}

// Match checks if a term matches the query term within the fuzzy distance.
// Returns the match score (1.0 for exact match, decreasing with distance).
func (f *FuzzyMatcher) Match(queryTerm, candidateTerm string) (bool, float64) {
	// Normalize both terms
	queryTerm = strings.ToLower(strings.TrimSpace(queryTerm))
	candidateTerm = strings.ToLower(strings.TrimSpace(candidateTerm))

	// Exact match
	if queryTerm == candidateTerm {
		return true, 1.0
	}

	// Check minimum length
	if len([]rune(queryTerm)) < f.MinLength || len([]rune(candidateTerm)) < f.MinLength {
		// For short terms, be more lenient
		if len([]rune(queryTerm)) < 2 || len([]rune(candidateTerm)) < 2 {
			return false, 0.0
		}
	}

	// Compute distance
	distance := levenshteinDistance(queryTerm, candidateTerm)

	// Check within threshold
	if distance <= f.MaxDistance {
		// Score decreases with distance: 1.0 at distance 0, approaching 0 at max distance
		score := 1.0 - (float64(distance) / float64(f.MaxDistance+1))
		return true, score
	}

	return false, 0.0
}

// FindMatches finds all candidate terms that match the query term within fuzzy distance.
func (f *FuzzyMatcher) FindMatches(queryTerm string, candidates []string) []MatchResult {
	var results []MatchResult

	for _, candidate := range candidates {
		matches, score := f.Match(queryTerm, candidate)
		if matches {
			results = append(results, MatchResult{
				QueryTerm:   queryTerm,
				Candidate:   candidate,
				Distance:    levenshteinDistance(queryTerm, candidate),
				Score:       score,
				MaxDistance: f.MaxDistance,
			})
		}
	}

	return results
}

// MatchResult represents the result of a fuzzy match.
type MatchResult struct {
	QueryTerm   string
	Candidate   string
	Distance    int
	Score       float64
	MaxDistance int
}

// String returns a string representation of the match result.
func (m MatchResult) String() string {
	return fmt.Sprintf("%q → %q (distance: %d, score: %.2f)", m.QueryTerm, m.Candidate, m.Distance, m.Score)
}

// WildcardMatcher handles wildcard pattern matching.
// Supports:
//   - * matches zero or more characters
//   - ? matches exactly one character
type WildcardMatcher struct{}

// NewWildcardMatcher creates a new wildcard matcher.
func NewWildcardMatcher() *WildcardMatcher {
	return &WildcardMatcher{}
}

// Match checks if a term matches a wildcard pattern.
func (w *WildcardMatcher) Match(pattern, term string) bool {
	pattern = strings.ToLower(pattern)
	term = strings.ToLower(term)

	return w.matchRecursive(pattern, term, 0, 0)
}

// matchRecursive implements recursive wildcard matching.
func (w *WildcardMatcher) matchRecursive(pattern, term string, pi, ti int) bool {
	plen := len(pattern)
	tlen := len(term)

	for pi < plen {
		p := rune(pattern[pi])

		if p == '*' {
			// * matches zero or more characters
			// Try matching zero characters, then one, then two, etc.
			for i := ti; i <= tlen; i++ {
				if w.matchRecursive(pattern, term, pi+1, i) {
					return true
				}
			}
			return false
		}

		if p == '?' {
			// ? matches exactly one character
			if ti >= tlen {
				return false
			}
			pi++
			ti++
			continue
		}

		// Regular character match
		if ti >= tlen || rune(term[ti]) != p {
			return false
		}

		pi++
		ti++
	}

	return ti == tlen
}

// FindWildcardMatches finds all candidates matching a wildcard pattern.
func (w *WildcardMatcher) FindWildcardMatches(pattern string, candidates []string) []string {
	var matches []string

	for _, candidate := range candidates {
		if w.Match(pattern, candidate) {
			matches = append(matches, candidate)
		}
	}

	return matches
}

// RangeChecker handles range query evaluation.
type RangeChecker struct{}

// NewRangeChecker creates a new range checker.
func NewRangeChecker() *RangeChecker {
	return &RangeChecker{}
}

// CheckRange evaluates whether a value falls within a range.
// For string ranges, comparison is lexicographic.
// For numeric ranges, values are parsed and compared numerically.
func (r *RangeChecker) CheckRange(lower, upper, value string, inclusive bool) bool {
	// Try numeric comparison first
	lowerNum, lowerErr := strconv.ParseFloat(lower, 64)
	upperNum, upperErr := strconv.ParseFloat(upper, 64)
	valueNum, valueErr := strconv.ParseFloat(value, 64)

	if lowerErr == nil && upperErr == nil && valueErr == nil {
		// Numeric comparison
		if inclusive {
			return valueNum >= lowerNum && valueNum <= upperNum
		}
		return valueNum > lowerNum && valueNum < upperNum
	}

	// Lexicographic comparison
	if inclusive {
		return value >= lower && value <= upper
	}
	return value > lower && value < upper
}

// RelevanceScorer calculates relevance scores for matching documents.
type RelevanceScorer struct{}

// NewRelevanceScorer creates a new relevance scorer.
func NewRelevanceScorer() *RelevanceScorer {
	return &RelevanceScorer{}
}

// Score calculates a relevance score for a document term against a query node.
func (s *RelevanceScorer) Score(term string, node *QueryNode) float64 {
	if node == nil {
		return 0.0
	}

	score := 1.0

	// Apply boost
	score *= node.Boost

	switch node.Type {
	case NodeTerm:
		// Exact match gets full score
		if strings.EqualFold(term, node.Value) {
			score *= 2.0
		}
	case NodeFuzzy:
		// Fuzzy match score decreases with distance
		if strings.EqualFold(term, node.Value) {
			score *= 2.0
		} else {
			dist := levenshteinDistance(term, node.Value)
			if dist <= node.FuzzyDist {
				score *= float64(node.FuzzyDist-dist) / float64(node.FuzzyDist+1)
			} else {
				return 0.0
			}
		}
	case NodePhrase:
		// Phrase queries require all terms to match in order
		// Score based on term overlap
		terms := strings.Fields(node.Value)
		matched := 0
		for _, t := range terms {
			if strings.EqualFold(term, t) {
				matched++
			}
		}
		if matched > 0 {
			score *= float64(matched) / float64(len(terms))
		} else {
			return 0.0
		}
	}

	return score
}

// DocumentScore calculates the aggregate relevance score for a document.
func (s *RelevanceScorer) DocumentScore(docTerms []string, node *QueryNode) float64 {
	if node == nil {
		return 0.0
	}

	switch node.Type {
	case NodeBoolean:
		return s.scoreBoolean(docTerms, node)
	default:
		return s.scoreNode(docTerms, node)
	}
}

// scoreBoolean handles boolean query scoring.
func (s *RelevanceScorer) scoreBoolean(docTerms []string, node *QueryNode) float64 {
	switch node.Operator {
	case BoolAnd:
		// AND: all children must match; score is the minimum of child scores
		minScore := math.MaxFloat64
		for _, child := range node.Children {
			sc := s.scoreNode(docTerms, child)
			if sc < minScore {
				minScore = sc
			}
		}
		if minScore == math.MaxFloat64 {
			return 0.0
		}
		return minScore

	case BoolOr:
		// OR: at least one child must match; score is the maximum of child scores
		maxScore := 0.0
		for _, child := range node.Children {
			sc := s.scoreNode(docTerms, child)
			if sc > maxScore {
				maxScore = sc
			}
		}
		return maxScore

	case BoolNot:
		// NOT: exclude documents matching the child query
		if len(node.Children) > 0 {
			sc := s.scoreNode(docTerms, node.Children[0])
			if sc > 0 {
				return 0.0 // Document matches NOT term, exclude it
			}
		}
		return 1.0

	default:
		return 0.0
	}
}

// scoreNode calculates score for a non-boolean node.
func (s *RelevanceScorer) scoreNode(docTerms []string, node *QueryNode) float64 {
	if node == nil {
		return 0.0
	}

	var bestScore float64

	switch node.Type {
	case NodeTerm:
		for _, term := range docTerms {
			sc := s.Score(term, node)
			if sc > bestScore {
				bestScore = sc
			}
		}

	case NodeFuzzy:
		for _, term := range docTerms {
			sc := s.Score(term, node)
			if sc > bestScore {
				bestScore = sc
			}
		}

	case NodePhrase:
		// For phrase queries, check if all phrase terms exist in the document
		phraseTerms := strings.Fields(node.Value)
		termSet := make(map[string]bool)
		for _, t := range docTerms {
			termSet[strings.ToLower(t)] = true
		}
		allMatch := true
		for _, pt := range phraseTerms {
			if !termSet[strings.ToLower(pt)] {
				allMatch = false
				break
			}
		}
		if allMatch {
			bestScore = 1.0 * node.Boost
		}

	case NodeWildcard:
		for _, term := range docTerms {
			if NewWildcardMatcher().Match(node.Value, term) {
				sc := s.Score(term, node)
				if sc > bestScore {
					bestScore = sc
				}
			}
		}

	case NodeRange:
		// Range queries typically match on numeric fields
		// For term-based scoring, check if any document term is a number in range
		for _, term := range docTerms {
			if NewRangeChecker().CheckRange(node.LowerBound, node.UpperBound, term, node.Inclusive) {
				sc := s.Score(term, node)
				if sc > bestScore {
					bestScore = sc
				}
			}
		}
	}

	return bestScore
}
