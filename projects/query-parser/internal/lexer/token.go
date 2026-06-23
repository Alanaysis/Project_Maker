package lexer

// TokenType represents the type of token
type TokenType int

const (
	TokenTerm     TokenType = iota // A word/term
	TokenPhrase                    // "quoted phrase"
	TokenAnd                       // AND
	TokenOr                        // OR
	TokenNot                       // NOT
	TokenLParen                    // (
	TokenRParen                    // )
	TokenEOF                       // End of input
)

// Token represents a lexical token
type Token struct {
	Type    TokenType
	Literal string
}

// String returns a string representation of the token type
func (t TokenType) String() string {
	switch t {
	case TokenTerm:
		return "TERM"
	case TokenPhrase:
		return "PHRASE"
	case TokenAnd:
		return "AND"
	case TokenOr:
		return "OR"
	case TokenNot:
		return "NOT"
	case TokenLParen:
		return "LPAREN"
	case TokenRParen:
		return "RPAREN"
	case TokenEOF:
		return "EOF"
	default:
		return "UNKNOWN"
	}
}
