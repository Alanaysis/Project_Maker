package queryparser

import (
	"fmt"
	"strings"
)

// NormalizeQuery normalizes a query string for consistent processing.
//
// Normalization steps:
// 1. Lowercase all terms
// 2. Remove stop words (optional)
// 3. Trim whitespace
// 4. Collapse multiple spaces
// 5. Preserve phrase boundaries
//
// # Example
//
//	Input:  "  Golang  AND  (Web   OR  \"Web Framework\")  "
//	Output: "golang and (web or \"web framework\")"
func NormalizeQuery(query string, removeStopWords bool) string {
	// First, normalize the raw string
	normalized := strings.ToLower(query)
	normalized = collapseSpaces(normalized)
	normalized = strings.TrimSpace(normalized)

	if !removeStopWords {
		return normalized
	}

	// Stop word removal requires parsing to avoid removing words inside phrases
	tokens, err := Tokenize(normalized)
	if err != nil {
		return normalized
	}

	var result strings.Builder
	inPhrase := false

	for _, tok := range tokens {
		switch tok.Type {
		case TokenPhraseStart:
			result.WriteString("\"")
			inPhrase = true
		case TokenPhraseEnd:
			result.WriteString("\"")
			inPhrase = false
		case TokenWord:
			if inPhrase {
				result.WriteString(tok.Value)
			} else if !isStopWord(tok.Value) {
				if result.Len() > 0 && !strings.HasSuffix(strings.TrimSpace(result.String()), "\"") {
					result.WriteString(" ")
				}
				result.WriteString(tok.Value)
			}
		case TokenAND, TokenOR, TokenNOT:
			if result.Len() > 0 {
				result.WriteString(" ")
			}
			result.WriteString(tok.Value)
		case TokenLParen:
			if result.Len() > 0 && !strings.HasSuffix(strings.TrimSpace(result.String()), "\"") {
				result.WriteString(" ")
			}
			result.WriteString("(")
		case TokenRParen:
			result.WriteString(")")
			if result.Len() > 0 {
				result.WriteString(" ")
			}
		default:
			if tok.Value != "" {
				if result.Len() > 0 && !strings.HasSuffix(strings.TrimSpace(result.String()), "\"") {
					result.WriteString(" ")
				}
				result.WriteString(tok.Value)
			}
		}
	}

	return strings.TrimSpace(result.String())
}

// collapseSpaces replaces multiple consecutive spaces with a single space.
func collapseSpaces(s string) string {
	var result strings.Builder
	previousWasSpace := false

	for _, r := range s {
		if r == ' ' {
			if !previousWasSpace {
				result.WriteRune(r)
			}
			previousWasSpace = true
		} else {
			result.WriteRune(r)
			previousWasSpace = false
		}
	}

	return result.String()
}

// QueryNormalizer encapsulates query normalization logic.
type QueryNormalizer struct {
	RemoveStopWords bool
	Lowercase       bool
	TrimWhitespace  bool
}

// NewQueryNormalizer creates a normalizer with default settings.
func NewQueryNormalizer() *QueryNormalizer {
	return &QueryNormalizer{
		RemoveStopWords: false,
		Lowercase:       true,
		TrimWhitespace:  true,
	}
}

// Normalize applies the configured normalization to a query string.
func (n *QueryNormalizer) Normalize(query string) string {
	result := query

	if n.TrimWhitespace {
		result = strings.TrimSpace(result)
		result = collapseSpaces(result)
		result = strings.TrimSpace(result)
	}

	if n.Lowercase {
		result = strings.ToLower(result)
	}

	if n.RemoveStopWords {
		result = NormalizeQuery(result, true)
	}

	return result
}

// NormalizeTree normalizes all terms in a query tree.
func NormalizeTree(tree *QueryTree) *QueryTree {
	if tree == nil || tree.Root == nil {
		return tree
	}

	normalized := &QueryTree{
		Original: tree.Original,
		Root:     normalizeNode(tree.Root),
	}

	return normalized
}

// normalizeNode recursively normalizes a query node and its children.
func normalizeNode(node *QueryNode) *QueryNode {
	if node == nil {
		return nil
	}

	// Create a copy with normalized value
	normalized := &QueryNode{
		Type:       node.Type,
		Value:      normalizeTerm(node.Value),
		Operator:   node.Operator,
		Boost:      node.Boost,
		FuzzyDist:  node.FuzzyDist,
		MinChars:   node.MinChars,
		LowerBound: node.LowerBound,
		UpperBound: node.UpperBound,
		Inclusive:  node.Inclusive,
		Position:   node.Position,
	}

	// Normalize children
	for _, child := range node.Children {
		normalized.Children = append(normalized.Children, normalizeNode(child))
	}

	return normalized
}

// String returns a string representation of the query tree (ASCII art style).
func (t *QueryTree) String() string {
	if t == nil || t.Root == nil {
		return "(empty query)"
	}

	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Query: %q\n", t.Original))
	sb.WriteString("Tree:\n")
	printTree(&sb, t.Root, "")
	return sb.String()
}

// printTree recursively prints the query tree with indentation.
func printTree(sb *strings.Builder, node *QueryNode, prefix string) {
	if node == nil {
		return
	}

	// Print current node
	indent := prefix + "├── "
	sb.WriteString(indent)

	nodeStr := fmt.Sprintf("[%s] %q", node.Type, node.Value)
	if node.Boost != 1.0 {
		nodeStr += fmt.Sprintf("^%.1f", node.Boost)
	}
	if node.Type == NodeFuzzy && node.FuzzyDist > 0 {
		nodeStr += fmt.Sprintf("~%d", node.FuzzyDist)
	}
	if node.Type == NodeRange {
		nodeStr = fmt.Sprintf("[%s TO %s] (inclusive: %v)", node.LowerBound, node.UpperBound, node.Inclusive)
	}
	if node.Type == NodeBoolean {
		nodeStr = fmt.Sprintf("%s", node.Operator)
	}

	sb.WriteString(nodeStr + "\n")

	// Print children with extended prefix
	childPrefix := prefix + "│   "
	for i, child := range node.Children {
		if i == len(node.Children)-1 {
			childPrefix = prefix + "    "
		}
		printTree(sb, child, childPrefix)
	}
}
