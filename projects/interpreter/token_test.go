package main

import "testing"

func TestLookupIdentKeywords(t *testing.T) {
	tests := []struct {
		input    string
		expected TokenType
	}{
		{"let", LET},
		{"fn", FN},
		{"if", IF},
		{"else", ELSE},
		{"while", WHILE},
		{"return", RETURN},
		{"print", PRINT},
		{"true", TRUE},
		{"false", FALSE},
		{"and", AND},
		{"or", OR},
		{"not", NOT},
	}

	for _, tt := range tests {
		result := LookupIdent(tt.input)
		if result != tt.expected {
			t.Errorf("LookupIdent(%q) = %s, expected %s", tt.input, result, tt.expected)
		}
	}
}

func TestLookupIdentUserDefined(t *testing.T) {
	tests := []string{"x", "foo", "myVar", "count", "hello_world", "_private"}

	for _, name := range tests {
		result := LookupIdent(name)
		if result != IDENT {
			t.Errorf("LookupIdent(%q) = %s, expected IDENT", name, result)
		}
	}
}

func TestTokenTypeString(t *testing.T) {
	tests := []struct {
		tt       TokenType
		expected string
	}{
		{ILLEGAL, "ILLEGAL"},
		{EOF, "EOF"},
		{NUMBER, "NUMBER"},
		{STRING, "STRING"},
		{IDENT, "IDENT"},
		{LET, "LET"},
		{FN, "FN"},
		{IF, "IF"},
		{ELSE, "ELSE"},
		{WHILE, "WHILE"},
		{RETURN, "RETURN"},
		{PRINT, "PRINT"},
		{TRUE, "TRUE"},
		{FALSE, "FALSE"},
		{AND, "AND"},
		{OR, "OR"},
		{NOT, "NOT"},
		{PLUS, "PLUS"},
		{MINUS, "MINUS"},
		{STAR, "STAR"},
		{SLASH, "SLASH"},
		{PERCENT, "PERCENT"},
		{ASSIGN, "ASSIGN"},
		{EQ, "EQ"},
		{NEQ, "NEQ"},
		{LT, "LT"},
		{GT, "GT"},
		{LTE, "LTE"},
		{GTE, "GTE"},
		{LPAREN, "LPAREN"},
		{RPAREN, "RPAREN"},
		{LBRACE, "LBRACE"},
		{RBRACE, "RBRACE"},
		{COMMA, "COMMA"},
		{SEMICOL, "SEMICOL"},
	}

	for _, tt := range tests {
		result := tt.tt.String()
		if result != tt.expected {
			t.Errorf("TokenType(%d).String() = %q, expected %q", tt.tt, result, tt.expected)
		}
	}
}

func TestTokenTypeStringUnknown(t *testing.T) {
	var unknown TokenType = 999
	result := unknown.String()
	if result != "UNKNOWN" {
		t.Errorf("unknown TokenType.String() = %q, expected %q", result, "UNKNOWN")
	}
}

func TestTokenStruct(t *testing.T) {
	tok := Token{Type: NUMBER, Literal: "42", Line: 1, Col: 5}
	if tok.Type != NUMBER {
		t.Errorf("expected type NUMBER, got %s", tok.Type)
	}
	if tok.Literal != "42" {
		t.Errorf("expected literal %q, got %q", "42", tok.Literal)
	}
	if tok.Line != 1 {
		t.Errorf("expected line 1, got %d", tok.Line)
	}
	if tok.Col != 5 {
		t.Errorf("expected col 5, got %d", tok.Col)
	}
}
