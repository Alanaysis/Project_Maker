package main

// Lexer performs lexical analysis on source code, converting it into tokens.
type Lexer struct {
	input   string
	pos     int    // current position in input (points to current char)
	readPos int    // current reading position (after current char)
	ch      byte   // current char under examination
	line    int    // current line number
	col     int    // current column number
}

// NewLexer creates a new Lexer for the given input string.
func NewLexer(input string) *Lexer {
	l := &Lexer{input: input, line: 1, col: 0}
	l.readChar()
	return l
}

// readChar reads the next character and advances the position.
func (l *Lexer) readChar() {
	if l.readPos >= len(l.input) {
		l.ch = 0 // ASCII NUL = EOF
	} else {
		l.ch = l.input[l.readPos]
	}
	l.pos = l.readPos
	l.readPos++
	if l.ch == '\n' {
		l.line++
		l.col = 0
	} else {
		l.col++
	}
}

// peekChar returns the next character without advancing.
func (l *Lexer) peekChar() byte {
	if l.readPos >= len(l.input) {
		return 0
	}
	return l.input[l.readPos]
}

// NextToken scans the input and returns the next token.
func (l *Lexer) NextToken() Token {
	var tok Token

	l.skipWhitespace()

	// Track token start position
	line := l.line
	col := l.col

	switch l.ch {
	case '+':
		tok = Token{Type: PLUS, Literal: string(l.ch), Line: line, Col: col}
	case '-':
		tok = Token{Type: MINUS, Literal: string(l.ch), Line: line, Col: col}
	case '*':
		tok = Token{Type: STAR, Literal: string(l.ch), Line: line, Col: col}
	case '/':
		if l.peekChar() == '/' {
			// Single-line comment
			l.skipComment()
			return l.NextToken()
		}
		tok = Token{Type: SLASH, Literal: string(l.ch), Line: line, Col: col}
	case '%':
		tok = Token{Type: PERCENT, Literal: string(l.ch), Line: line, Col: col}
	case '(':
		tok = Token{Type: LPAREN, Literal: string(l.ch), Line: line, Col: col}
	case ')':
		tok = Token{Type: RPAREN, Literal: string(l.ch), Line: line, Col: col}
	case '{':
		tok = Token{Type: LBRACE, Literal: string(l.ch), Line: line, Col: col}
	case '}':
		tok = Token{Type: RBRACE, Literal: string(l.ch), Line: line, Col: col}
	case ',':
		tok = Token{Type: COMMA, Literal: string(l.ch), Line: line, Col: col}
	case ';':
		tok = Token{Type: SEMICOL, Literal: string(l.ch), Line: line, Col: col}
	case '=':
		if l.peekChar() == '=' {
			ch := l.ch
			l.readChar()
			tok = Token{Type: EQ, Literal: string(ch) + string(l.ch), Line: line, Col: col}
		} else {
			tok = Token{Type: ASSIGN, Literal: string(l.ch), Line: line, Col: col}
		}
	case '!':
		if l.peekChar() == '=' {
			ch := l.ch
			l.readChar()
			tok = Token{Type: NEQ, Literal: string(ch) + string(l.ch), Line: line, Col: col}
		} else {
			tok = Token{Type: ILLEGAL, Literal: string(l.ch), Line: line, Col: col}
		}
	case '<':
		if l.peekChar() == '=' {
			ch := l.ch
			l.readChar()
			tok = Token{Type: LTE, Literal: string(ch) + string(l.ch), Line: line, Col: col}
		} else {
			tok = Token{Type: LT, Literal: string(l.ch), Line: line, Col: col}
		}
	case '>':
		if l.peekChar() == '=' {
			ch := l.ch
			l.readChar()
			tok = Token{Type: GTE, Literal: string(ch) + string(l.ch), Line: line, Col: col}
		} else {
			tok = Token{Type: GT, Literal: string(l.ch), Line: line, Col: col}
		}
	case '"':
		tok.Type = STRING
		tok.Literal = l.readString()
		tok.Line = line
		tok.Col = col
	case 0:
		tok = Token{Type: EOF, Literal: "", Line: line, Col: col}
	default:
		if isLetter(l.ch) {
			tok.Literal = l.readIdentifier()
			tok.Type = LookupIdent(tok.Literal)
			tok.Line = line
			tok.Col = col
			return tok
		} else if isDigit(l.ch) {
			tok.Type = NUMBER
			tok.Literal = l.readNumber()
			tok.Line = line
			tok.Col = col
			return tok
		} else {
			tok = Token{Type: ILLEGAL, Literal: string(l.ch), Line: line, Col: col}
		}
	}

	l.readChar()
	return tok
}

// readIdentifier reads an identifier and advances the position.
func (l *Lexer) readIdentifier() string {
	pos := l.pos
	for isLetter(l.ch) || isDigit(l.ch) {
		l.readChar()
	}
	return l.input[pos:l.pos]
}

// readNumber reads a number (integer or float) and advances the position.
func (l *Lexer) readNumber() string {
	pos := l.pos
	for isDigit(l.ch) {
		l.readChar()
	}
	if l.ch == '.' && isDigit(l.peekChar()) {
		l.readChar() // consume '.'
		for isDigit(l.ch) {
			l.readChar()
		}
	}
	return l.input[pos:l.pos]
}

// readString reads a string literal and advances the position.
func (l *Lexer) readString() string {
	l.readChar() // consume opening "
	pos := l.pos
	for l.ch != '"' && l.ch != 0 {
		if l.ch == '\\' {
			l.readChar() // skip escape char
		}
		l.readChar()
	}
	str := l.input[pos:l.pos]
	// Process escape sequences
	result := ""
	for i := 0; i < len(str); i++ {
		if str[i] == '\\' && i+1 < len(str) {
			switch str[i+1] {
			case 'n':
				result += "\n"
			case 't':
				result += "\t"
			case '\\':
				result += "\\"
			case '"':
				result += "\""
			default:
				result += string(str[i]) + string(str[i+1])
			}
			i++ // skip next char
		} else {
			result += string(str[i])
		}
	}
	return result
}

// skipWhitespace skips whitespace characters.
func (l *Lexer) skipWhitespace() {
	for l.ch == ' ' || l.ch == '\t' || l.ch == '\n' || l.ch == '\r' {
		l.readChar()
	}
}

// skipComment skips a single-line comment (// to end of line).
func (l *Lexer) skipComment() {
	for l.ch != '\n' && l.ch != 0 {
		l.readChar()
	}
}

// isLetter checks if a byte is a letter, underscore, or non-ASCII character.
func isLetter(ch byte) bool {
	return 'a' <= ch && ch <= 'z' || 'A' <= ch && ch <= 'Z' || ch == '_'
}

// isDigit checks if a byte is a digit.
func isDigit(ch byte) bool {
	return '0' <= ch && ch <= '9'
}

// Tokenize returns all tokens from the input.
func Tokenize(input string) []Token {
	lexer := NewLexer(input)
	var tokens []Token
	for {
		tok := lexer.NextToken()
		tokens = append(tokens, tok)
		if tok.Type == EOF {
			break
		}
	}
	return tokens
}
