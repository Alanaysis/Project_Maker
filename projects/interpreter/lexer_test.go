package main

import "testing"

func TestNextToken(t *testing.T) {
	tests := []struct {
		input    string
		expected []struct {
			typ     TokenType
			literal string
		}
	}{
		{
			input: `let x = 5;`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{LET, "let"},
				{IDENT, "x"},
				{ASSIGN, "="},
				{NUMBER, "5"},
				{SEMICOL, ";"},
				{EOF, ""},
			},
		},
		{
			input: `let y = 10;`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{LET, "let"},
				{IDENT, "y"},
				{ASSIGN, "="},
				{NUMBER, "10"},
				{SEMICOL, ";"},
				{EOF, ""},
			},
		},
		{
			input: `fn add(a, b) { return a + b; }`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{FN, "fn"},
				{IDENT, "add"},
				{LPAREN, "("},
				{IDENT, "a"},
				{COMMA, ","},
				{IDENT, "b"},
				{RPAREN, ")"},
				{LBRACE, "{"},
				{RETURN, "return"},
				{IDENT, "a"},
				{PLUS, "+"},
				{IDENT, "b"},
				{SEMICOL, ";"},
				{RBRACE, "}"},
				{EOF, ""},
			},
		},
		{
			input: `if x > 5 { print "big"; }`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{IF, "if"},
				{IDENT, "x"},
				{GT, ">"},
				{NUMBER, "5"},
				{LBRACE, "{"},
				{PRINT, "print"},
				{STRING, "big"},
				{SEMICOL, ";"},
				{RBRACE, "}"},
				{EOF, ""},
			},
		},
		{
			input: `x == y != z`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{IDENT, "x"},
				{EQ, "=="},
				{IDENT, "y"},
				{NEQ, "!="},
				{IDENT, "z"},
				{EOF, ""},
			},
		},
		{
			input: `true and false or not true`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{TRUE, "true"},
				{AND, "and"},
				{FALSE, "false"},
				{OR, "or"},
				{NOT, "not"},
				{TRUE, "true"},
				{EOF, ""},
			},
		},
		{
			input: `3.14 + 2.0`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{NUMBER, "3.14"},
				{PLUS, "+"},
				{NUMBER, "2.0"},
				{EOF, ""},
			},
		},
		{
			input: `"hello world"`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{STRING, "hello world"},
				{EOF, ""},
			},
		},
		{
			input: `// this is a comment
let x = 1;`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{LET, "let"},
				{IDENT, "x"},
				{ASSIGN, "="},
				{NUMBER, "1"},
				{SEMICOL, ";"},
				{EOF, ""},
			},
		},
		{
			input: `<= >= < >`,
			expected: []struct {
				typ     TokenType
				literal string
			}{
				{LTE, "<="},
				{GTE, ">="},
				{LT, "<"},
				{GT, ">"},
				{EOF, ""},
			},
		},
	}

	for _, tt := range tests {
		lexer := NewLexer(tt.input)
		for i, exp := range tt.expected {
			tok := lexer.NextToken()
			if tok.Type != exp.typ {
				t.Errorf("test[%q] token %d - wrong type. expected=%s, got=%s",
					tt.input, i, exp.typ, tok.Type)
			}
			if tok.Literal != exp.literal {
				t.Errorf("test[%q] token %d - wrong literal. expected=%q, got=%q",
					tt.input, i, exp.literal, tok.Literal)
			}
		}
	}
}

func TestTokenize(t *testing.T) {
	input := `let x = 1 + 2;`
	tokens := Tokenize(input)

	// let, x, =, 1, +, 2, ;, EOF = 8 tokens
	expectedLen := 8
	if len(tokens) != expectedLen {
		t.Errorf("expected %d tokens, got %d", expectedLen, len(tokens))
	}
}
