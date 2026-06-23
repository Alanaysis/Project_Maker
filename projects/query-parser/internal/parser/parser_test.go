package parser

import (
	"query-parser/internal/lexer"
	"testing"
)

func TestParserTerm(t *testing.T) {
	l := lexer.New("hello")
	tokens := l.Tokenize()
	p := New(tokens)
	node, err := p.Parse()

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if node.String() != "hello" {
		t.Errorf("expected 'hello', got %s", node.String())
	}
}

func TestParserPhrase(t *testing.T) {
	l := lexer.New(`"hello world"`)
	tokens := l.Tokenize()
	p := New(tokens)
	node, err := p.Parse()

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if node.String() != `"hello world"` {
		t.Errorf("expected '\"hello world\"', got %s", node.String())
	}
}

func TestParserAnd(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"hello AND world", "(hello AND world)"},
		{"hello world", "(hello AND world)"}, // implicit AND
		{"a AND b AND c", "((a AND b) AND c)"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()
			p := New(tokens)
			node, err := p.Parse()

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

func TestParserOr(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"hello OR world", "(hello OR world)"},
		{"a OR b OR c", "((a OR b) OR c)"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()
			p := New(tokens)
			node, err := p.Parse()

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

func TestParserNot(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"NOT hello", "(NOT hello)"},
		{"NOT (hello OR world)", "(NOT (hello OR world))"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()
			p := New(tokens)
			node, err := p.Parse()

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

func TestParserPrecedence(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"a OR b AND c", "(a OR (b AND c))"},      // AND has higher precedence
		{"a AND b OR c", "((a AND b) OR c)"},
		{"NOT a OR b", "((NOT a) OR b)"},
		{"NOT a AND b", "((NOT a) AND b)"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()
			p := New(tokens)
			node, err := p.Parse()

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

func TestParserParentheses(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"(hello)", "hello"},
		{"(hello AND world)", "(hello AND world)"},
		{"(a OR b) AND c", "((a OR b) AND c)"},
		{"((a OR b) AND c)", "((a OR b) AND c)"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			l := lexer.New(tt.input)
			tokens := l.Tokenize()
			p := New(tokens)
			node, err := p.Parse()

			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}

			if node.String() != tt.expected {
				t.Errorf("expected %s, got %s", tt.expected, node.String())
			}
		})
	}
}

func TestParserComplexQuery(t *testing.T) {
	input := `(quick OR fast) AND "brown fox" AND NOT lazy`
	expected := "(((quick OR fast) AND \"brown fox\") AND (NOT lazy))"

	l := lexer.New(input)
	tokens := l.Tokenize()
	p := New(tokens)
	node, err := p.Parse()

	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if node.String() != expected {
		t.Errorf("expected %s, got %s", expected, node.String())
	}
}

func TestParserEmptyQuery(t *testing.T) {
	l := lexer.New("")
	tokens := l.Tokenize()
	p := New(tokens)
	_, err := p.Parse()

	if err == nil {
		t.Error("expected error for empty query")
	}
}

func TestParserMismatchedParentheses(t *testing.T) {
	l := lexer.New("(hello")
	tokens := l.Tokenize()
	p := New(tokens)
	_, err := p.Parse()

	if err == nil {
		t.Error("expected error for mismatched parentheses")
	}
}
