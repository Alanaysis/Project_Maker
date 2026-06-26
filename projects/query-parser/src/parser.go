package queryparser

import (
	"fmt"
	"strconv"
	"strings"
)

// Parser implements a recursive descent parser for query strings.
//
// # Grammar
//
//	Query      → OrExpr
//	OrExpr     → AndExpr (OR AndExpr)*
//	AndExpr    → NotExpr (AND NotExpr)*
//	NotExpr    → Primary | NOT NotExpr
//	Primary    → Phrase | Range | Grouped | FuzzyTerm | WildcardTerm | BoostedTerm
//	FuzzyTerm  → Term ~ [LevDistance]
//	WildcardTerm → Term *
//	BoostedTerm → Term ^ Number
//	Phrase     → " PhraseContent "
//	Range      → [ Lower TO Upper ] | { Lower TO Upper }
//	Grouped    → ( OrExpr )
//
// # Operator Precedence (highest to lowest)
//
//	1. Parentheses grouping
//	2. Phrase queries ("...")
//	3. Range queries ([a TO b])
//	4. Fuzzy queries (term~)
//	5. Wildcard queries (term*)
//	6. Boost (term^N)
//	7. NOT
//	8. AND
//	9. OR
//
// # Example Parse
//
//	Input:  "golang AND (web OR \"web framework\")~1"
//	Output:
//	   BOOLEAN(AND)
//	   ├── TERM(golang)
//	   └── FUZZY(1)
//	      └── BOOLEAN(OR)
//	         ├── TERM(web)
//	         └── PHRASE([web, framework])
func Parser struct {
	stream *TokenStream
	stats  *QueryStats
}

// NewParser creates a new query parser from a query string.
func NewParser(query string) *Parser {
	tokens, err := Tokenize(query)
	if err != nil {
		// Return a parser with an error token for graceful handling
		return &Parser{
			stream: NewTokenStream([]Token{
				{Type: TokenWord, Value: query, Pos: 0, Length: len([]rune(query))},
				{Type: TokenEof, Value: "", Pos: len([]rune(query)), Length: 0},
			}),
			stats: NewQueryStats(),
		}
	}
	return &Parser{
		stream: NewTokenStream(tokens),
		stats:  NewQueryStats(),
	}
}

// Parse parses the query string and returns a QueryTree.
func (p *Parser) Parse() (*QueryTree, error) {
	tree := &QueryTree{Original: p.stream.tokens[0].Value}

	// Parse the top-level expression (OR is lowest precedence)
	p.stats.Reset()
	root, err := p.parseOrExpr()
	if err != nil {
		return nil, fmt.Errorf("parse error: %w", err)
	}

	tree.Root = root
	p.stats.CollectStats(tree)
	return tree, nil
}

// parseOrExpr handles OR expressions (lowest precedence).
// OrExpr → AndExpr (OR AndExpr)*
func (p *Parser) parseOrExpr() (*QueryNode, error) {
	left, err := p.parseAndExpr()
	if err != nil {
		return nil, err
	}

	for p.stream.HasNext() && p.stream.IsTokenType(TokenOR) {
		p.stream.Next() // consume OR
		right, err := p.parseAndExpr()
		if err != nil {
			return nil, err
		}

		left = &QueryNode{
			Type:       NodeBoolean,
			Operator:   BoolOr,
			Children:   []*QueryNode{left, right},
			Boost:      1.0,
			Position:   p.stream.Current().Pos,
		}
	}

	return left, nil
}

// parseAndExpr handles AND expressions.
// AndExpr → NotExpr (AND NotExpr)*
func (p *Parser) parseAndExpr() (*QueryNode, error) {
	left, err := p.parseNotExpr()
	if err != nil {
		return nil, err
	}

	for p.stream.HasNext() && p.stream.IsTokenType(TokenAND) {
		p.stream.Next() // consume AND
		right, err := p.parseNotExpr()
		if err != nil {
			return nil, err
		}

		left = &QueryNode{
			Type:       NodeBoolean,
			Operator:   BoolAnd,
			Children:   []*QueryNode{left, right},
			Boost:      1.0,
			Position:   p.stream.Current().Pos,
		}
	}

	return left, nil
}

// parseNotExpr handles NOT expressions.
// NotExpr → NOT NotExpr | Primary
func (p *Parser) parseNotExpr() (*QueryNode, error) {
	if !p.stream.HasNext() {
		return nil, fmt.Errorf("unexpected end of query")
	}

	if p.stream.IsTokenType(TokenNOT) {
		p.stream.Next() // consume NOT
		child, err := p.parseNotExpr() // recursive for chained NOT
		if err != nil {
			return nil, err
		}

		return &QueryNode{
			Type:     NodeBoolean,
			Operator: BoolNot,
			Children: []*QueryNode{child},
			Boost:    1.0,
			Position: p.stream.Current().Pos,
		}, nil
	}

	return p.parsePrimary()
}

// parsePrimary handles the highest precedence expressions.
// Primary → Phrase | Range | Grouped | FuzzyTerm | WildcardTerm | BoostedTerm | Term
func (p *Parser) parsePrimary() (*QueryNode, error) {
	if !p.stream.HasNext() {
		return nil, fmt.Errorf("unexpected end of query")
	}

	tok := p.stream.Current()

	// Parenthesized group
	if tok.Type == TokenLParen {
		return p.parseGrouped()
	}

	// Phrase query
	if tok.Type == TokenPhraseStart {
		return p.parsePhrase()
	}

	// Range query
	if tok.Type == TokenRangeStart {
		return p.parseRange()
	}

	// Regular term - apply modifiers
	if tok.Type == TokenWord || tok.Type == TokenWildcard {
		return p.parseTermWithModifiers()
	}

	return nil, fmt.Errorf("unexpected token %s at position %d", tok.Type, tok.Pos)
}

// parseGrouped handles parenthesized expressions.
// Grouped → ( OrExpr )
func (p *Parser) parseGrouped() (*QueryNode, error) {
	p.stream.Next() // consume (

	// Check for empty group
	if p.stream.IsTokenType(TokenRParen) {
		p.stream.Next() // consume )
		return &QueryNode{
			Type:     NodeTerm,
			Value:    "",
			Boost:    1.0,
			Position: p.stream.Current().Pos,
		}, nil
	}

	node, err := p.parseOrExpr()
	if err != nil {
		return nil, err
	}

	_, err = p.stream.Expect(TokenRParen)
	if err != nil {
		return nil, err
	}

	return node, nil
}

// parsePhrase handles phrase queries.
// Phrase → " PhraseContent "
func (p *Parser) parsePhrase() (*QueryNode, error) {
	p.stream.Next() // consume phrase start

	// Collect words until phrase end
	var words []string
	for p.stream.HasNext() && !p.stream.IsTokenType(TokenPhraseEnd) {
		tok := p.stream.Current()
		if tok.Type == TokenWord {
			words = append(words, normalizeTerm(tok.Value))
		}
		p.stream.Next()
	}

	_, err := p.stream.Expect(TokenPhraseEnd)
	if err != nil {
		return nil, err
	}

	// Join words to create the phrase value
	phraseValue := strings.Join(words, " ")

	node := &QueryNode{
		Type:     NodePhrase,
		Value:    phraseValue,
		Boost:    1.0,
		Position: p.stream.Current().Pos,
	}

	// Store words as children for the phrase
	for _, w := range words {
		node.Children = append(node.Children, &QueryNode{
			Type:     NodeTerm,
			Value:    w,
			Boost:    1.0,
			Position: node.Position,
		})
	}

	return node, nil
}

// parseRange handles range queries.
// Range → [ Lower TO Upper ] | { Lower TO Upper }
func (p *Parser) parseRange() (*QueryNode, error) {
	rangeStart := p.stream.Current().Value
	p.stream.Next() // consume range start

	// Parse lower bound
	lower := ""
	if p.stream.HasNext() && !p.stream.IsTokenType(TokenRangeEnd) {
		tok := p.stream.Current()
		if tok.Type == TokenWord {
			lower = tok.Value
			p.stream.Next()
		}
	}

	// Expect TO keyword
	if !p.stream.HasNext() || p.stream.Current().Value != "TO" && p.stream.Current().Value != "to" {
		return nil, fmt.Errorf("expected 'TO' in range query at position %d", p.stream.Current().Pos)
	}
	p.stream.Next() // consume TO

	// Parse upper bound
	upper := ""
	if p.stream.HasNext() && !p.stream.IsTokenType(TokenRangeEnd) {
		tok := p.stream.Current()
		if tok.Type == TokenWord {
			upper = tok.Value
			p.stream.Next()
		}
	}

	_, err := p.stream.Expect(TokenRangeEnd)
	if err != nil {
		return nil, err
	}

	// Determine inclusivity based on bracket type
	inclusive := rangeStart == "["

	return &QueryNode{
		Type:       NodeRange,
		Value:      fmt.Sprintf("[%s TO %s]", lower, upper),
		LowerBound: lower,
		UpperBound: upper,
		Inclusive:  inclusive,
		Boost:      1.0,
		Position:   p.stream.Current().Pos,
	}, nil
}

// parseTermWithModifiers handles terms with fuzzy, wildcard, and boost modifiers.
// Term modifiers are applied in order: fuzzy → wildcard → boost
func (p *Parser) parseTermWithModifiers() (*QueryNode, error) {
	tok := p.stream.Current()
	originalValue := tok.Value
	pos := tok.Pos

	// Check for fuzzy modifier (~)
	if p.stream.HasNext() && p.stream.Peek().Value == "~" {
		p.stream.Next() // consume term
		p.stream.Next() // consume ~

		fuzzyDist := 2 // default Levenshtein distance
		// Check for explicit distance
		if p.stream.HasNext() && p.stream.Current().Type == TokenWord {
			if d, err := strconv.Atoi(p.stream.Current().Value); err == nil && d >= 0 && d <= 5 {
				fuzzyDist = d
				p.stream.Next()
			}
		}

		return &QueryNode{
			Type:      NodeFuzzy,
			Value:     normalizeTerm(originalValue),
			FuzzyDist: fuzzyDist,
			Boost:     1.0,
			Position:  pos,
		}, nil
	}

	// Check for wildcard (*)
	if tok.Type == TokenWildcard {
		// Extract the base term (without wildcards)
		baseTerm := strings.TrimRight(strings.TrimLeft(originalValue, "*"), "*")
		return &QueryNode{
			Type:     NodeWildcard,
			Value:    normalizeTerm(originalValue),
			Boost:    1.0,
			Position: pos,
		}, nil
	}

	// Regular term - consume it
	p.stream.Next()

	// Check for boost (^)
	boost := 1.0
	if p.stream.HasNext() && p.stream.Current().Value == "^" {
		p.stream.Next() // consume ^
		// Parse boost value
		if p.stream.HasNext() && p.stream.Current().Type == TokenWord {
			if b, err := strconv.ParseFloat(p.stream.Current().Value, 64); err == nil && b > 0 {
				boost = b
				p.stream.Next()
			}
		}
	}

	return &QueryNode{
		Type:     NodeTerm,
		Value:    normalizeTerm(originalValue),
		Boost:    boost,
		Position: pos,
	}, nil
}

// GetStats returns the statistics collected during parsing.
func (p *Parser) GetStats() *QueryStats {
	return p.stats
}
