package tests

import (
	"query-parser/internal/executor"
	"query-parser/internal/index"
	"query-parser/internal/lexer"
	"query-parser/internal/parser"
	"testing"
)

// createTestIndex creates a test index with sample documents
func createTestIndex() *index.Index {
	idx := index.New()

	docs := []*index.Document{
		{ID: "doc1", Content: "The quick brown fox jumps over the lazy dog"},
		{ID: "doc2", Content: "A quick brown dog outpaces the fox"},
		{ID: "doc3", Content: "The lazy cat sleeps all day long"},
		{ID: "doc4", Content: "Quick brown foxes are very fast animals"},
		{ID: "doc5", Content: "The dog and cat are friends"},
		{ID: "doc6", Content: "Python is a popular programming language"},
		{ID: "doc7", Content: "Go is a statically typed compiled language"},
		{ID: "doc8", Content: "JavaScript is widely used for web development"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	return idx
}

// parseAndExecute is a helper function to parse and execute a query
func parseAndExecute(t *testing.T, idx *index.Index, query string) []executor.SearchResult {
	t.Helper()

	l := lexer.New(query)
	tokens := l.Tokenize()

	p := parser.New(tokens)
	ast, err := p.Parse()
	if err != nil {
		t.Fatalf("parse error for query %q: %v", query, err)
	}

	ex := executor.New(idx)
	return ex.Execute(ast)
}

// TestE2ESimpleTermQuery tests simple term queries
func TestE2ESimpleTermQuery(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "single term fox",
			query:    "fox",
			expected: 2, // doc1, doc2
		},
		{
			name:     "case insensitive",
			query:    "FOX",
			expected: 2, // doc1, doc2
		},
		{
			name:     "term cat",
			query:    "cat",
			expected: 2, // doc3, doc5
		},
		{
			name:     "term dog",
			query:    "dog",
			expected: 3, // doc1, doc2, doc5
		},
		{
			name:     "term quick",
			query:    "quick",
			expected: 3, // doc1, doc2, doc4
		},
		{
			name:     "no results",
			query:    "nonexistent",
			expected: 0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2EBooleanAndQuery tests AND queries
func TestE2EBooleanAndQuery(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "explicit AND quick fox",
			query:    "quick AND fox",
			expected: 2, // doc1, doc2 (both have quick and fox)
		},
		{
			name:     "implicit AND quick fox",
			query:    "quick fox",
			expected: 2, // doc1, doc2 (implicit AND)
		},
		{
			name:     "AND with no overlap",
			query:    "fox AND cat",
			expected: 0, // no doc has both
		},
		{
			name:     "AND dog cat",
			query:    "dog AND cat",
			expected: 1, // doc5 has both
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2EBooleanOrQuery tests OR queries
func TestE2EBooleanOrQuery(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "simple OR cat dog",
			query:    "cat OR dog",
			expected: 4, // doc1, doc2, doc3, doc5
		},
		{
			name:     "OR fox cat",
			query:    "fox OR cat",
			expected: 4, // doc1, doc2, doc3, doc5
		},
		{
			name:     "OR with overlapping",
			query:    "quick OR fox",
			expected: 3, // doc1, doc2, doc4 (doc1 and doc2 have both)
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2ENotQuery tests NOT queries
func TestE2ENotQuery(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
		excluded []string
	}{
		{
			name:     "simple NOT lazy",
			query:    "NOT lazy",
			expected: 6, // all docs except doc1 and doc3
			excluded: []string{"doc1", "doc3"},
		},
		{
			name:     "AND NOT",
			query:    "quick AND NOT fox",
			expected: 1, // doc4 (quick but not fox)
			excluded: []string{"doc1", "doc2"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}

			resultIDs := make(map[string]bool)
			for _, r := range results {
				resultIDs[r.DocID] = true
			}

			for _, excludedID := range tt.excluded {
				if resultIDs[excludedID] {
					t.Errorf("expected %s to be excluded from results", excludedID)
				}
			}
		})
	}
}

// TestE2EPhraseQuery tests phrase queries
func TestE2EPhraseQuery(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "simple phrase brown fox",
			query:    `"brown fox"`,
			expected: 1, // doc1
		},
		{
			name:     "phrase lazy dog",
			query:    `"lazy dog"`,
			expected: 1, // doc1
		},
		{
			name:     "phrase substring match",
			query:    `"quick brown fox"`,
			expected: 1, // doc1 contains "quick brown fox" as substring
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s (content: %s)", r.DocID, r.Content)
				}
			}
		})
	}
}

// TestE2EComplexQueries tests complex query combinations
func TestE2EComplexQueries(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "parentheses grouping",
			query:    "(quick OR fast) AND fox",
			expected: 2, // doc1, doc2
		},
		{
			name:     "nested parentheses",
			query:    "(quick OR fast) AND (fox OR cat)",
			expected: 2, // doc1, doc2 (quick AND fox)
		},
		{
			name:     "phrase with boolean",
			query:    `"brown fox" OR cat`,
			expected: 3, // doc1, doc3, doc5
		},
		{
			name:     "complex with NOT",
			query:    "(quick OR lazy) AND NOT cat",
			expected: 3, // doc1, doc2, doc4 (quick docs without cat)
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2ERelevanceSorting tests that results are sorted by relevance
func TestE2ERelevanceSorting(t *testing.T) {
	idx := createTestIndex()

	results := parseAndExecute(t, idx, "quick")

	if len(results) < 2 {
		t.Fatal("expected at least 2 results")
	}

	// Results should be sorted by score (descending)
	for i := 1; i < len(results); i++ {
		if results[i].Score > results[i-1].Score {
			t.Errorf("results not sorted by score: result %d has score %f, result %d has score %f",
				i-1, results[i-1].Score, i, results[i].Score)
		}
	}
}

// TestE2EEdgeCases tests edge cases
func TestE2EEdgeCases(t *testing.T) {
	tests := []struct {
		name        string
		query       string
		expectError bool
	}{
		{
			name:        "empty query",
			query:       "",
			expectError: true,
		},
		{
			name:        "whitespace only",
			query:       "   ",
			expectError: true,
		},
		{
			name:        "single term",
			query:       "fox",
			expectError: false,
		},
		{
			name:        "unmatched parenthesis open",
			query:       "(fox",
			expectError: true,
		},
		{
			name:        "unmatched parenthesis close",
			query:       "fox)",
			expectError: true,
		},
		{
			name:        "valid complex query",
			query:       "(quick OR fast) AND fox",
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			l := lexer.New(tt.query)
			tokens := l.Tokenize()

			p := parser.New(tokens)
			_, err := p.Parse()

			if tt.expectError && err == nil {
				t.Error("expected error but got none")
			}
			if !tt.expectError && err != nil {
				t.Errorf("unexpected error: %v", err)
			}
		})
	}
}

// TestE2ELexerTokenTypes tests lexer token type detection
func TestE2ELexerTokenTypes(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected []string
	}{
		{
			name:     "keywords",
			input:    "AND OR NOT",
			expected: []string{"AND", "OR", "NOT", "EOF"},
		},
		{
			name:     "terms",
			input:    "hello world",
			expected: []string{"TERM", "TERM", "EOF"},
		},
		{
			name:     "phrase",
			input:    `"hello world"`,
			expected: []string{"PHRASE", "EOF"},
		},
		{
			name:     "parentheses",
			input:    "(hello)",
			expected: []string{"LPAREN", "TERM", "RPAREN", "EOF"},
		},
		{
			name:     "mixed",
			input:    `"hello" AND (world OR earth)`,
			expected: []string{"PHRASE", "AND", "LPAREN", "TERM", "OR", "TERM", "RPAREN", "EOF"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()

			if len(tokens) != len(tt.expected) {
				t.Fatalf("expected %d tokens, got %d", len(tt.expected), len(tokens))
			}

			for i, tok := range tokens {
				if tok.Type.String() != tt.expected[i] {
					t.Errorf("token %d: expected %s, got %s (literal: %s)", i, tt.expected[i], tok.Type.String(), tok.Literal)
				}
			}
		})
	}
}

// TestE2EParserASTStructure tests parser AST structure
func TestE2EParserASTStructure(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "simple term",
			input:    "hello",
			expected: "hello",
		},
		{
			name:     "phrase",
			input:    `"hello world"`,
			expected: `"hello world"`,
		},
		{
			name:     "AND operation",
			input:    "hello AND world",
			expected: "(hello AND world)",
		},
		{
			name:     "implicit AND",
			input:    "hello world",
			expected: "(hello AND world)",
		},
		{
			name:     "OR operation",
			input:    "hello OR world",
			expected: "(hello OR world)",
		},
		{
			name:     "NOT operation",
			input:    "NOT hello",
			expected: "(NOT hello)",
		},
		{
			name:     "parentheses",
			input:    "(hello OR world) AND foo",
			expected: "((hello OR world) AND foo)",
		},
		{
			name:     "complex query",
			input:    `(quick OR fast) AND "brown fox" AND NOT lazy`,
			expected: `(((quick OR fast) AND "brown fox") AND (NOT lazy))`,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()

			p := parser.New(tokens)
			node, err := p.Parse()
			if err != nil {
				t.Fatalf("parse error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

// TestE2EIndexOperations tests index operations
func TestE2EIndexOperations(t *testing.T) {
	idx := index.New()

	// Test adding documents
	docs := []*index.Document{
		{ID: "doc1", Content: "Hello World"},
		{ID: "doc2", Content: "World of Warcraft"},
		{ID: "doc3", Content: "Hello Kitty"},
	}

	for _, doc := range docs {
		idx.AddDocument(doc)
	}

	// Test document count
	if idx.DocumentCount() != 3 {
		t.Errorf("expected 3 documents, got %d", idx.DocumentCount())
	}

	// Test search
	results := idx.Search("hello")
	if len(results) != 2 {
		t.Errorf("expected 2 results for 'hello', got %d", len(results))
	}

	// Test case insensitive search
	results = idx.Search("HELLO")
	if len(results) != 2 {
		t.Errorf("expected 2 results for 'HELLO', got %d", len(results))
	}

	// Test get document
	doc := idx.GetDocument("doc1")
	if doc == nil {
		t.Fatal("expected document, got nil")
	}
	if doc.Content != "Hello World" {
		t.Errorf("expected 'Hello World', got %s", doc.Content)
	}

	// Test get nonexistent document
	doc = idx.GetDocument("nonexistent")
	if doc != nil {
		t.Error("expected nil for nonexistent document")
	}

	// Test all documents
	allDocs := idx.AllDocuments()
	if len(allDocs) != 3 {
		t.Errorf("expected 3 documents, got %d", len(allDocs))
	}
}

// TestE2EFullPipeline tests the complete pipeline from query to results
func TestE2EFullPipeline(t *testing.T) {
	idx := createTestIndex()

	// Test complete pipeline
	query := `(quick OR fast) AND "brown fox" AND NOT lazy`

	l := lexer.New(query)
	tokens := l.Tokenize()

	p := parser.New(tokens)
	ast, err := p.Parse()
	if err != nil {
		t.Fatalf("parse error: %v", err)
	}

	// Verify AST structure
	expectedAST := `(((quick OR fast) AND "brown fox") AND (NOT lazy))`
	if ast.String() != expectedAST {
		t.Errorf("expected AST %s, got %s", expectedAST, ast.String())
	}

	// Execute query
	ex := executor.New(idx)
	results := ex.Execute(ast)

	// Should find no results because doc1 has "brown fox" but also has "lazy"
	if len(results) != 0 {
		t.Errorf("expected 0 results, got %d", len(results))
		for _, r := range results {
			t.Logf("  result: %s", r.DocID)
		}
	}
}

// TestE2EMultipleQueries tests multiple queries in sequence
func TestE2EMultipleQueries(t *testing.T) {
	idx := createTestIndex()

	queries := []struct {
		query    string
		expected int
	}{
		{"fox", 2},       // doc1, doc2
		{"cat", 2},       // doc3, doc5
		{"dog", 3},       // doc1, doc2, doc5
		{"language", 2},  // doc6, doc7
		{"programming", 1}, // doc6
	}

	for _, q := range queries {
		t.Run(q.query, func(t *testing.T) {
			results := parseAndExecute(t, idx, q.query)
			if len(results) != q.expected {
				t.Errorf("expected %d results, got %d", q.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2EScoreCalculation tests score calculation
func TestE2EScoreCalculation(t *testing.T) {
	idx := createTestIndex()

	results := parseAndExecute(t, idx, "quick")

	if len(results) == 0 {
		t.Fatal("expected results")
	}

	// All results should have positive scores
	for _, r := range results {
		if r.Score <= 0 {
			t.Errorf("expected positive score, got %f for %s", r.Score, r.DocID)
		}
	}

	// doc1 should have higher score than doc4 because it has more occurrences of "quick"
	// doc1: "The quick brown fox" - 1 occurrence
	// doc2: "A quick brown dog" - 1 occurrence
	// doc4: "Quick brown foxes" - 1 occurrence
	// All have same TF, so scores should be equal
}

// TestE2EBooleanOperatorPrecedence tests operator precedence
func TestE2EBooleanOperatorPrecedence(t *testing.T) {
	idx := createTestIndex()

	tests := []struct {
		name     string
		query    string
		expected int
	}{
		{
			name:     "AND has higher precedence than OR",
			query:    "cat OR quick AND fox",
			expected: 4, // cat docs (2) + (quick AND fox) docs (2) = 4
		},
		{
			name:     "explicit parentheses override precedence",
			query:    "(cat OR quick) AND fox",
			expected: 2, // (cat OR quick) = 5 docs, AND fox = 2 docs
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := parseAndExecute(t, idx, tt.query)

			if len(results) != tt.expected {
				t.Errorf("expected %d results, got %d", tt.expected, len(results))
				for _, r := range results {
					t.Logf("  result: %s", r.DocID)
				}
			}
		})
	}
}

// TestE2EIndexSearchConsistency tests that search results are consistent
func TestE2EIndexSearchConsistency(t *testing.T) {
	idx := createTestIndex()

	// Search multiple times for the same term
	term := "fox"
	firstResults := idx.Search(term)

	for i := 0; i < 10; i++ {
		results := idx.Search(term)
		if len(results) != len(firstResults) {
			t.Errorf("inconsistent results on iteration %d: expected %d, got %d", i, len(firstResults), len(results))
		}
	}
}
