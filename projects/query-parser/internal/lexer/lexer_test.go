package lexer

import (
	"testing"
)

func TestLexerBasic(t *testing.T) {
	tests := []struct {
		input    string
		expected []TokenType
	}{
		{
			input:    "hello",
			expected: []TokenType{TokenTerm, TokenEOF},
		},
		{
			input:    "hello world",
			expected: []TokenType{TokenTerm, TokenTerm, TokenEOF},
		},
		{
			input:    "hello AND world",
			expected: []TokenType{TokenTerm, TokenAnd, TokenTerm, TokenEOF},
		},
		{
			input:    "hello OR world",
			expected: []TokenType{TokenTerm, TokenOr, TokenTerm, TokenEOF},
		},
		{
			input:    "NOT hello",
			expected: []TokenType{TokenNot, TokenTerm, TokenEOF},
		},
		{
			input:    `"hello world"`,
			expected: []TokenType{TokenPhrase, TokenEOF},
		},
		{
			input:    "(hello AND world)",
			expected: []TokenType{TokenLParen, TokenTerm, TokenAnd, TokenTerm, TokenRParen, TokenEOF},
		},
		{
			input:    "hello AND (world OR earth)",
			expected: []TokenType{TokenTerm, TokenAnd, TokenLParen, TokenTerm, TokenOr, TokenTerm, TokenRParen, TokenEOF},
		},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := New(tt.input)
			tokens := l.Tokenize()

			if len(tokens) != len(tt.expected) {
				t.Errorf("expected %d tokens, got %d", len(tt.expected), len(tokens))
				for i, tok := range tokens {
					t.Logf("  [%d] %s: %s", i, tok.Type, tok.Literal)
				}
				return
			}

			for i, tok := range tokens {
				if tok.Type != tt.expected[i] {
					t.Errorf("token %d: expected %s, got %s (literal: %s)", i, tt.expected[i], tok.Type, tok.Literal)
				}
			}
		})
	}
}

func TestLexerLiterals(t *testing.T) {
	tests := []struct {
		input    string
		expected []string
	}{
		{
			input:    "hello",
			expected: []string{"hello", ""},
		},
		{
			input:    "Hello World",
			expected: []string{"hello", "world", ""},
		},
		{
			input:    `"quoted phrase"`,
			expected: []string{"quoted phrase", ""},
		},
		{
			input:    "AND OR NOT",
			expected: []string{"AND", "OR", "NOT", ""},
		},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := New(tt.input)
			tokens := l.Tokenize()

			if len(tokens) != len(tt.expected) {
				t.Errorf("expected %d tokens, got %d", len(tt.expected), len(tokens))
				return
			}

			for i, tok := range tokens {
				if tok.Literal != tt.expected[i] {
					t.Errorf("token %d: expected literal %q, got %q", i, tt.expected[i], tok.Literal)
				}
			}
		})
	}
}

func TestLexerComplexQuery(t *testing.T) {
	input := `(quick OR fast) AND "brown fox" NOT lazy`
	l := New(input)
	tokens := l.Tokenize()

	expectedTypes := []TokenType{
		TokenLParen, TokenTerm, TokenOr, TokenTerm, TokenRParen,
		TokenAnd, TokenPhrase, TokenNot, TokenTerm, TokenEOF,
	}

	if len(tokens) != len(expectedTypes) {
		t.Fatalf("expected %d tokens, got %d", len(expectedTypes), len(tokens))
	}

	for i, tok := range tokens {
		if tok.Type != expectedTypes[i] {
			t.Errorf("token %d: expected %s, got %s", i, expectedTypes[i], tok.Type)
		}
	}
}
