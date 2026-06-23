package lexer

import "strings"

// Lexer tokenizes a query string
type Lexer struct {
	input  string
	pos    int
	tokens []Token
}

// New creates a new Lexer
func New(input string) *Lexer {
	return &Lexer{
		input: input,
		pos:   0,
	}
}

// Tokenize returns all tokens from the input
func (l *Lexer) Tokenize() []Token {
	for l.pos < len(l.input) {
		l.skipWhitespace()
		if l.pos >= len(l.input) {
			break
		}

		ch := l.input[l.pos]

		switch {
		case ch == '"':
			l.readPhrase()
		case ch == '(':
			l.tokens = append(l.tokens, Token{Type: TokenLParen, Literal: "("})
			l.pos++
		case ch == ')':
			l.tokens = append(l.tokens, Token{Type: TokenRParen, Literal: ")"})
			l.pos++
		default:
			l.readWord()
		}
	}

	l.tokens = append(l.tokens, Token{Type: TokenEOF, Literal: ""})
	return l.tokens
}

func (l *Lexer) skipWhitespace() {
	for l.pos < len(l.input) && l.input[l.pos] == ' ' {
		l.pos++
	}
}

func (l *Lexer) readPhrase() {
	l.pos++ // skip opening quote
	start := l.pos
	for l.pos < len(l.input) && l.input[l.pos] != '"' {
		l.pos++
	}
	phrase := l.input[start:l.pos]
	if l.pos < len(l.input) {
		l.pos++ // skip closing quote
	}
	l.tokens = append(l.tokens, Token{Type: TokenPhrase, Literal: phrase})
}

func (l *Lexer) readWord() {
	start := l.pos
	for l.pos < len(l.input) && l.input[l.pos] != ' ' && l.input[l.pos] != '(' && l.input[l.pos] != ')' {
		l.pos++
	}
	word := l.input[start:l.pos]

	// Check for keywords
	upper := strings.ToUpper(word)
	switch upper {
	case "AND":
		l.tokens = append(l.tokens, Token{Type: TokenAnd, Literal: word})
	case "OR":
		l.tokens = append(l.tokens, Token{Type: TokenOr, Literal: word})
	case "NOT":
		l.tokens = append(l.tokens, Token{Type: TokenNot, Literal: word})
	default:
		l.tokens = append(l.tokens, Token{Type: TokenTerm, Literal: strings.ToLower(word)})
	}
}
