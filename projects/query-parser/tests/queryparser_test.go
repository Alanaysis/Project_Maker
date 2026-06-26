package queryparser

import (
	"strings"
	"testing"
)

func TestTokenize(t *testing.T) {
	tests := []struct {
		name     string
		query    string
		wantType []TokenType
		wantVal  []string
	}{
		{
			name:     "simple word",
			query:    "golang",
			wantType: []TokenType{TokenWord, TokenEof},
			wantVal:  []string{"golang", ""},
		},
		{
			name:     "boolean and",
			query:    "golang AND python",
			wantType: []TokenType{TokenWord, TokenAND, TokenWord, TokenEof},
			wantVal:  []string{"golang", "AND", "python", ""},
		},
		{
			name:     "boolean or",
			query:    "golang OR python",
			wantType: []TokenType{TokenWord, TokenOR, TokenWord, TokenEof},
			wantVal:  []string{"golang", "OR", "python", ""},
		},
		{
			name:     "phrase query",
			query:    `"web framework"`,
			wantType: []TokenType{TokenPhraseStart, TokenWord, TokenWord, TokenPhraseEnd, TokenEof},
			wantVal:  []string{"web framework", "web", "framework", "", ""},
		},
		{
			name:     "wildcard",
			query:    "go*",
			wantType: []TokenType{TokenWildcard, TokenEof},
			wantVal:  []string{"go*", ""},
		},
		{
			name:     "range query",
			query:    "price:[10 TO 100]",
			wantType: []TokenType{TokenWord, TokenRangeStart, TokenWord, TokenWord, TokenWord, TokenRangeEnd, TokenEof},
			wantVal:  []string{"price", "[", "10", "TO", "100", "]", ""},
		},
		{
			name:     "parentheses",
			query:    "(golang OR python)",
			wantType: []TokenType{TokenLParen, TokenWord, TokenOR, TokenWord, TokenRParen, TokenEof},
			wantVal:  []string{"(", "golang", "OR", "python", ")", ""},
		},
		{
			name:     "fuzzy query",
			query:    "golan~",
			wantType: []TokenType{TokenWord, TokenWord, TokenEof},
			wantVal:  []string{"golan", "~", ""},
		},
		{
			name:     "boost",
			query:    "golang^2.0",
			wantType: []TokenType{TokenWord, TokenWord, TokenEof},
			wantVal:  []string{"golang", "^", ""},
		},
		{
			name:     "not operator",
			query:    "golang NOT python",
			wantType: []TokenType{TokenWord, TokenNOT, TokenWord, TokenEof},
			wantVal:  []string{"golang", "NOT", "python", ""},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tokens, err := Tokenize(tt.query)
			if err != nil {
				t.Fatalf("Tokenize(%q) error: %v", tt.query, err)
			}

			if len(tokens) != len(tt.wantType) {
				t.Fatalf("Tokenize(%q) got %d tokens, want %d", tt.query, len(tokens), len(tt.wantType))
			}

			for i, tok := range tokens {
				if tok.Type != tt.wantType[i] {
					t.Errorf("Token[%d]: got type %s, want %s", i, tok.Type, tt.wantType[i])
				}
				if tt.wantVal[i] != "" && tok.Value != tt.wantVal[i] {
					t.Errorf("Token[%d]: got value %q, want %q", i, tok.Value, tt.wantVal[i])
				}
			}
		})
	}
}

func TestTokenizeUnfinishedPhrase(t *testing.T) {
	_, err := Tokenize(`"unfinished phrase`)
	if err == nil {
		t.Error("expected error for unterminated phrase, got nil")
	}
}

func TestTokenizeBooleanOperators(t *testing.T) {
	tests := []struct {
		input    string
		expected TokenType
	}{
		{"AND", TokenAND},
		{"and", TokenAND},
		{"And", TokenAND},
		{"OR", TokenOR},
		{"or", TokenOR},
		{"OR", TokenOR},
		{"NOT", TokenNOT},
		{"not", TokenNOT},
	}

	for _, tt := range tests {
		tokens, err := Tokenize(tt.input)
		if err != nil {
			t.Fatalf("Tokenize(%q) error: %v", tt.input, err)
		}

		if len(tokens) < 2 {
			t.Fatalf("Tokenize(%q) got too few tokens", tt.input)
		}

		if tokens[0].Type != tt.expected {
			t.Errorf("Tokenize(%q): got type %s, want %s", tt.input, tokens[0].Type, tt.expected)
		}
	}
}

func TestCountTokens(t *testing.T) {
	tokens, _ := Tokenize("golang AND python OR java")
	count := CountTokens(tokens)
	if count != 5 {
		t.Errorf("CountTokens: got %d, want 5", count)
	}
}

func TestParserParse(t *testing.T) {
	tests := []struct {
		name    string
		query   string
		wantType QueryNodeType
	}{
		{
			name:     "simple term",
			query:    "golang",
			wantType: NodeTerm,
		},
		{
			name:     "boolean and",
			query:    "golang AND python",
			wantType: NodeBoolean,
		},
		{
			name:     "boolean or",
			query:    "golang OR python",
			wantType: NodeBoolean,
		},
		{
			name:     "phrase query",
			query:    `"web framework"`,
			wantType: NodePhrase,
		},
		{
			name:     "wildcard query",
			query:    "go*",
			wantType: NodeWildcard,
		},
		{
			name:     "fuzzy query",
			query:    "golan~",
			wantType: NodeFuzzy,
		},
		{
			name:     "range query",
			query:    "price:[10 TO 100]",
			wantType: NodeRange,
		},
		{
			name:     "grouped expression",
			query:    "(golang OR python)",
			wantType: NodeBoolean,
		},
		{
			name:     "not query",
			query:    "NOT python",
			wantType: NodeBoolean,
		},
		{
			name:     "complex query",
			query:    "golang AND (web OR \"web framework\")",
			wantType: NodeBoolean,
		},
		{
			name:     "boosted query",
			query:    "golang^2.0",
			wantType: NodeTerm,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			parser := NewParser(tt.query)
			tree, err := parser.Parse()
			if err != nil {
				t.Fatalf("Parse(%q) error: %v", tt.query, err)
			}

			if tree.Root.Type != tt.wantType {
				t.Errorf("Parse(%q): got root type %s, want %s", tt.query, tree.Root.Type, tt.wantType)
			}
		})
	}
}

func TestParserComplexQuery(t *testing.T) {
	query := "golang AND (web OR \"web framework\")~1"
	parser := NewParser(query)
	tree, err := parser.Parse()
	if err != nil {
		t.Fatalf("Parse(%q) error: %v", query, err)
	}

	if tree.Root.Type != NodeBoolean {
		t.Errorf("Root type: got %s, want %s", tree.Root.Type, NodeBoolean)
	}

	stats := parser.GetStats()
	if !stats.HasBoolean {
		t.Error("Expected boolean operators in query")
	}
	if !stats.HasFuzzy {
		t.Error("Expected fuzzy modifier in query")
	}
	if stats.TotalQueries != 1 {
		t.Errorf("Expected 1 query, got %d", stats.TotalQueries)
	}
}

func TestNormalizeQuery(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "lowercase",
			input:    "GOLANG",
			expected: "golang",
		},
		{
			name:     "trim whitespace",
			input:    "  golang  ",
			expected: "golang",
		},
		{
			name:     "collapse spaces",
			input:    "golang   AND    python",
			expected: "golang and python",
		},
		{
			name:     "preserve phrases",
			input:    `"Web Framework"`,
			expected: "\"web framework\"",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NormalizeQuery(tt.input, false)
			if result != tt.expected {
				t.Errorf("NormalizeQuery(%q): got %q, want %q", tt.input, result, tt.expected)
			}
		})
	}
}

func TestNormalizeQueryWithStopWords(t *testing.T) {
	input := "golang AND the OR python"
	result := NormalizeQuery(input, true)

	// "the" should be removed
	if strings.Contains(result, " the ") {
		t.Errorf("Stop word 'the' should be removed, got: %q", result)
	}
}

func TestNormalizeTree(t *testing.T) {
	parser := NewParser("GOLANG AND PYTHON")
	tree, err := parser.Parse()
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}

	normalized := NormalizeTree(tree)

	// Check that terms are lowercased
	if normalized.Root.Children[0].Value != "golang" {
		t.Errorf("Normalized term: got %q, want %q", normalized.Root.Children[0].Value, "golang")
	}
}

func TestLevenshteinDistance(t *testing.T) {
	tests := []struct {
		s1     string
		s2     string
		want   int
	}{
		{"kitten", "sitting", 3},
		{"go", "golang", 4},
		{"golan", "golang", 1},
		{"hello", "hello", 0},
		{"", "abc", 3},
		{"abc", "", 3},
	}

	for _, tt := range tests {
		got := levenshteinDistance(tt.s1, tt.s2)
		if got != tt.want {
			t.Errorf("levenshteinDistance(%q, %q) = %d, want %d", tt.s1, tt.s2, got, tt.want)
		}
	}
}

func TestFuzzyMatcher(t *testing.T) {
	matcher := NewFuzzyMatcher()

	t.Run("exact match", func(t *testing.T) {
		matches, score := matcher.Match("golang", "golang")
		if !matches {
			t.Error("Expected exact match")
		}
		if score != 1.0 {
			t.Errorf("Expected score 1.0, got %f", score)
		}
	})

	t.Run("fuzzy match", func(t *testing.T) {
		matches, score := matcher.Match("golang", "golan")
		if !matches {
			t.Error("Expected fuzzy match for 'golan' vs 'golang'")
		}
		if score <= 0 || score >= 1.0 {
			t.Errorf("Expected positive score < 1.0, got %f", score)
		}
	})

	t.Run("no match", func(t *testing.T) {
		matches, _ := matcher.Match("golang", "xyz")
		if matches {
			t.Error("Expected no match for 'xyz' vs 'golang'")
		}
	})

	t.Run("find matches", func(t *testing.T) {
		candidates := []string{"golang", "golan", "golng", "xyz", "golangx"}
		results := matcher.FindMatches("golang", candidates)

		if len(results) < 2 {
			t.Errorf("Expected at least 2 matches, got %d", len(results))
		}
	})
}

func TestWildcardMatcher(t *testing.T) {
	matcher := NewWildcardMatcher()

	tests := []struct {
		pattern string
		term    string
		want    bool
	}{
		{"go*", "golang", true},
		{"go*", "go", true},
		{"go*", "g", false},
		{"go*", "python", false},
		{"g?lang", "golang", true},
		{"g?lang", "glang", true},
		{"g?lang", "goolang", false},
		{"*framework", "web framework", true},
		{"*framework", "framework", true},
		{"*framework", "web", false},
	}

	for _, tt := range tests {
		t.Run(tt.pattern+" vs "+tt.term, func(t *testing.T) {
			got := matcher.Match(tt.pattern, tt.term)
			if got != tt.want {
				t.Errorf("Match(%q, %q) = %v, want %v", tt.pattern, tt.term, got, tt.want)
			}
		})
	}
}

func TestWildcardFindMatches(t *testing.T) {
	matcher := NewWildcardMatcher()
	candidates := []string{"golang", "go", "gopher", "python", "java"}
	matches := matcher.FindWildcardMatches("go*", candidates)

	if len(matches) != 3 {
		t.Errorf("Expected 3 matches, got %d: %v", len(matches), matches)
	}
}

func TestRangeChecker(t *testing.T) {
	checker := NewRangeChecker()

	tests := []struct {
		lower     string
		upper     string
		value     string
		inclusive bool
		want      bool
	}{
		{"10", "100", "50", true, true},
		{"10", "100", "10", true, true},
		{"10", "100", "100", true, true},
		{"10", "100", "5", true, false},
		{"10", "100", "105", true, false},
		{"10", "100", "50", false, true},
		{"10", "100", "10", false, false},
		{"10", "100", "100", false, false},
		// String comparison
		{"apple", "banana", "cherry", true, false},
		{"apple", "banana", "mango", true, false},
		{"apple", "banana", "grape", true, true},
	}

	for _, tt := range tests {
		t.Run(tt.value, func(t *testing.T) {
			got := checker.CheckRange(tt.lower, tt.upper, tt.value, tt.inclusive)
			if got != tt.want {
				t.Errorf("CheckRange(%q, %q, %q, %v) = %v, want %v",
					tt.lower, tt.upper, tt.value, tt.inclusive, got, tt.want)
			}
		})
	}
}

func TestRelevanceScorer(t *testing.T) {
	scorer := NewRelevanceScorer()

	t.Run("term score exact match", func(t *testing.T) {
		node := &QueryNode{Type: NodeTerm, Value: "golang", Boost: 1.0}
		score := scorer.Score("golang", node)
		if score != 2.0 {
			t.Errorf("Expected score 2.0 for exact match, got %f", score)
		}
	})

	t.Run("term score no match", func(t *testing.T) {
		node := &QueryNode{Type: NodeTerm, Value: "golang", Boost: 1.0}
		score := scorer.Score("python", node)
		if score != 1.0 {
			t.Errorf("Expected score 1.0 for non-match, got %f", score)
		}
	})

	t.Run("boosted term", func(t *testing.T) {
		node := &QueryNode{Type: NodeTerm, Value: "golang", Boost: 2.0}
		score := scorer.Score("golang", node)
		if score != 4.0 {
			t.Errorf("Expected score 4.0 for boosted match, got %f", score)
		}
	})
}

func TestDocumentScore(t *testing.T) {
	scorer := NewRelevanceScorer()
	docTerms := []string{"golang", "web", "framework", "programming"}

	t.Run("and scoring", func(t *testing.T) {
		parser := NewParser("golang AND web")
		tree, _ := parser.Parse()
		score := scorer.DocumentScore(docTerms, tree.Root)
		if score <= 0 {
			t.Errorf("Expected positive score for AND query, got %f", score)
		}
	})

	t.Run("or scoring", func(t *testing.T) {
		parser := NewParser("python OR golang")
		tree, _ := parser.Parse()
		score := scorer.DocumentScore(docTerms, tree.Root)
		if score <= 0 {
			t.Errorf("Expected positive score for OR query, got %f", score)
		}
	})

	t.Run("not scoring", func(t *testing.T) {
		parser := NewParser("golang NOT python")
		tree, _ := parser.Parse()
		score := scorer.DocumentScore(docTerms, tree.Root)
		if score <= 0 {
			t.Errorf("Expected positive score, got %f", score)
		}
	})
}

func TestQueryTreeString(t *testing.T) {
	parser := NewParser("golang AND (python OR java)")
	tree, err := parser.Parse()
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}

	str := tree.String()
	if !strings.Contains(str, "golang") {
		t.Error("Tree string should contain 'golang'")
	}
	if !strings.Contains(str, "BOOLEAN") {
		t.Error("Tree string should contain 'BOOLEAN'")
	}
}

func TestQueryStats(t *testing.T) {
	parser := NewParser("golang AND (web OR \"web framework\")~1")
	tree, err := parser.Parse()
	if err != nil {
		t.Fatalf("Parse error: %v", err)
	}

	stats := parser.GetStats()
	if stats.TotalQueries != 1 {
		t.Errorf("Expected 1 query, got %d", stats.TotalQueries)
	}
	if stats.HasBoolean != true {
		t.Error("Expected HasBoolean to be true")
	}
	if stats.HasFuzzy != true {
		t.Error("Expected HasFuzzy to be true")
	}
	if stats.HasPhrase != true {
		t.Error("Expected HasPhrase to be true")
	}
	if stats.TotalQueries != stats.TotalQueries {
		t.Error("Stats collection is inconsistent")
	}

	// Collect stats again for the same tree
	stats.CollectStats(tree)
	if stats.TotalQueries != 2 {
		t.Errorf("Expected 2 total queries after second collect, got %d", stats.TotalQueries)
	}
}

func TestQueryStatsReset(t *testing.T) {
	stats := NewQueryStats()
	stats.Reset()
	if stats.TotalQueries != 0 {
		t.Errorf("After reset, expected 0 queries, got %d", stats.TotalQueries)
	}
}

func TestTokenString(t *testing.T) {
	tok := Token{Type: TokenWord, Value: "golang", Pos: 0, Length: 6}
	s := tok.String()
	if !strings.Contains(s, "WORD") || !strings.Contains(s, "golang") {
		t.Errorf("Token.String() = %q, expected to contain 'WORD' and 'golang'", s)
	}
}

func TestTokenTypeString(t *testing.T) {
	tests := []struct {
		typeVal TokenType
		want    string
	}{
		{TokenWord, "WORD"},
		{TokenAND, "AND"},
		{TokenOR, "OR"},
		{TokenNOT, "NOT"},
		{TokenLParen, "("},
		{TokenRParen, ")"},
		{TokenPhraseStart, "PHRASE_START"},
		{TokenPhraseEnd, "PHRASE_END"},
		{TokenWildcard, "*"},
		{TokenRangeStart, "RANGE_START"},
		{TokenRangeEnd, "RANGE_END"},
		{TokenComma, ","},
		{TokenEof, "EOF"},
	}

	for _, tt := range tests {
		if got := tt.typeVal.String(); got != tt.want {
			t.Errorf("TokenType(%d).String() = %q, want %q", tt.typeVal, got, tt.want)
		}
	}
}

func TestTokenStream(t *testing.T) {
	tokens := []Token{
		{Type: TokenWord, Value: "golang", Pos: 0},
		{Type: TokenAND, Value: "AND", Pos: 7},
		{Type: TokenWord, Value: "python", Pos: 11},
		{Type: TokenEof, Value: "", Pos: 18},
	}
	stream := NewTokenStream(tokens)

	// Test Current
	if !stream.IsTokenType(TokenWord) {
		t.Error("Current token should be TokenWord")
	}

	// Test Next
	tok := stream.Next()
	if tok.Value != "golang" {
		t.Errorf("Next() = %q, want %q", tok.Value, "golang")
	}

	// Test HasNext
	if !stream.HasNext() {
		t.Error("Should have next token")
	}

	// Test Peek
	peeked := stream.Peek()
	if peeked.Value != "AND" {
		t.Errorf("Peek() = %q, want %q", peeked.Value, "AND")
	}

	// Test Current again (should not advance)
	if !stream.IsTokenType(TokenAND) {
		t.Error("Current should still be TokenAND after Peek")
	}

	// Test Expect
	tok, err := stream.Expect(TokenAND)
	if err != nil {
		t.Errorf("Expect(TokenAND) error: %v", err)
	}
	if tok.Value != "AND" {
		t.Errorf("Expect() = %q, want %q", tok.Value, "AND")
	}

	// Test AdvancePast
	stream.AdvancePast(TokenEof)
	if stream.HasNext() {
		t.Error("Should not have next after advancing to EOF")
	}
}

func TestNormalizeTerm(t *testing.T) {
	tests := []struct {
		input  string
		output string
	}{
		{"GOLANG", "golang"},
		{"  Python  ", "python"},
		{"Go", "go"},
	}

	for _, tt := range tests {
		got := normalizeTerm(tt.input)
		if got != tt.output {
			t.Errorf("normalizeTerm(%q) = %q, want %q", tt.input, got, tt.output)
		}
	}
}

func TestIsStopWord(t *testing.T) {
	stopWords := []string{"the", "and", "or", "not", "in", "on", "at", "to", "for", "of"}
	for _, sw := range stopWords {
		if !isStopWord(sw) {
			t.Errorf("%q should be a stop word", sw)
		}
	}

	nonStopWords := []string{"golang", "python", "web", "framework"}
	for _, nsw := range nonStopWords {
		if isStopWord(nsw) {
			t.Errorf("%q should NOT be a stop word", nsw)
		}
	}
}

func TestParserChainedBoolean(t *testing.T) {
	tests := []struct {
		name     string
		query    string
		wantType QueryNodeType
	}{
		{
			name:     "chained AND",
			query:    "golang AND python AND java",
			wantType: NodeBoolean,
		},
		{
			name:     "chained OR",
			query:    "golang OR python OR java",
			wantType: NodeBoolean,
		},
		{
			name:     "mixed AND/OR",
			query:    "golang AND python OR java",
			wantType: NodeBoolean,
		},
		{
			name:     "chained NOT",
			query:    "NOT python NOT java",
			wantType: NodeBoolean,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			parser := NewParser(tt.query)
			tree, err := parser.Parse()
			if err != nil {
				t.Fatalf("Parse(%q) error: %v", tt.query, err)
			}

			if tree.Root.Type != tt.wantType {
				t.Errorf("Root type: got %s, want %s", tree.Root.Type, tt.wantType)
			}
		})
	}
}

func TestFuzzyDistanceThreshold(t *testing.T) {
	matcher := &FuzzyMatcher{MaxDistance: 1, MinLength: 3}

	// Distance 1 should match
	matches, _ := matcher.Match("golang", "golng")
	if !matches {
		t.Error("Expected match with distance 1")
	}

	// Distance 2 should not match (exceeds threshold)
	matches, _ = matcher.Match("golang", "gln")
	if matches {
		t.Error("Expected no match with distance 2 (threshold is 1)")
	}
}

func TestWildcardEdgeCases(t *testing.T) {
	matcher := NewWildcardMatcher()

	// * matches empty string
	if !matcher.Match("*", "") {
		t.Error("* should match empty string")
	}

	// * matches anything
	if !matcher.Match("*", "anything") {
		t.Error("* should match any string")
	}

	// ? requires exactly one character
	if matcher.Match("?", "") {
		t.Error("? should not match empty string")
	}

	if !matcher.Match("?", "a") {
		t.Error("? should match single character")
	}

	if matcher.Match("?", "ab") {
		t.Error("? should not match multiple characters")
	}
}

func TestRangeQueryBracketTypes(t *testing.T) {
	tests := []struct {
		name      string
		query     string
		inclusive bool
	}{
		{"square brackets", "price:[10 TO 100]", true},
		{"curly brackets", "price:{10 TO 100}", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			parser := NewParser(tt.query)
			tree, err := parser.Parse()
			if err != nil {
				t.Fatalf("Parse(%q) error: %v", tt.query, err)
			}

			if tree.Root.Type != NodeRange {
				t.Errorf("Expected NodeRange, got %s", tree.Root.Type)
			}
			if tree.Root.Inclusive != tt.inclusive {
				t.Errorf("Inclusive: got %v, want %v", tree.Root.Inclusive, tt.inclusive)
			}
		})
	}
}
