package queryparser

import (
	"fmt"
	"strings"
	"unicode"
)

// Tokenizer breaks a query string into a sequence of tokens.
//
// The tokenizer handles:
// - Regular terms (words, numbers)
// - Boolean operators (AND, OR, NOT)
// - Phrase boundaries (double quotes)
// - Wildcards (* and ?)
// - Range query boundaries ([ ] and { })
// - Parentheses for grouping
// - Boost syntax (^)
//
// # Tokenization Rules
//
// 1. Double-quoted strings become phrase tokens
// 2. AND/OR/NOT are recognized as boolean operators (case-insensitive)
// 3. * and ? are recognized as wildcards within terms
// 4. [ and { start range queries; ] and } end them
// 5. ( and ) group sub-expressions
// 6. ^ indicates boost weight
// 7. Spaces separate terms (unless inside quotes)
//
// # Example
//
//	"golang AND (web OR \"web framework\")~2"
//	→ WORD(golang) AND LPAREN OR PHRASE_START(word:web,word:framework) PHRASE_END
func Tokenize(query string) ([]Token, error) {
	var tokens []Token
	runes := []rune(query)
	i := 0

	for i < len(runes) {
		r := runes[i]

		// Skip whitespace
		if unicode.IsSpace(r) {
			i++
			continue
		}

		// Double-quoted phrase
		if r == '"' {
			phraseStart := i
			i++ // skip opening quote
			var phraseBuilder strings.Builder

			for i < len(runes) && runes[i] != '"' {
				if runes[i] == '\\' && i+1 < len(runes) {
					// Handle escape sequences
					i++
					phraseBuilder.WriteRune(runes[i])
				} else {
					phraseBuilder.WriteRune(runes[i])
				}
				i++
			}

			if i >= len(runes) {
				return nil, fmt.Errorf("unterminated phrase at position %d", phraseStart)
			}

			phraseText := phraseBuilder.String()
			i++ // skip closing quote

			// Tokenize the phrase content into individual word tokens
			phraseWords := tokenizePhraseContent(phraseText)
			phrasePos := phraseStart

			tokens = append(tokens, Token{
				Type:   TokenPhraseStart,
				Value:  phraseText,
				Pos:    phrasePos,
				Length: len([]rune(phraseText)),
			})

			for _, word := range phraseWords {
				tokens = append(tokens, Token{
					Type:   TokenWord,
					Value:  word,
					Pos:    phrasePos,
					Length: len([]rune(word)),
				})
				phrasePos += len([]rune(word))
			}

			tokens = append(tokens, Token{
				Type:   TokenPhraseEnd,
				Value:  "",
				Pos:    phrasePos,
				Length: 0,
			})

			continue
		}

		// Parentheses
		if r == '(' {
			tokens = append(tokens, Token{Type: TokenLParen, Value: "(", Pos: i, Length: 1})
			i++
			continue
		}
		if r == ')' {
			tokens = append(tokens, Token{Type: TokenRParen, Value: ")", Pos: i, Length: 1})
			i++
			continue
		}

		// Range query brackets
		if r == '[' || r == '{' {
			tokens = append(tokens, Token{Type: TokenRangeStart, Value: string(r), Pos: i, Length: 1})
			i++
			continue
		}
		if r == ']' || r == '}' {
			tokens = append(tokens, Token{Type: TokenRangeEnd, Value: string(r), Pos: i, Length: 1})
			i++
			continue
		}

		// Comma (range separator)
		if r == ',' {
			tokens = append(tokens, Token{Type: TokenComma, Value: ",", Pos: i, Length: 1})
			i++
			continue
		}

		// Caret (boost)
		if r == '^' {
			tokens = append(tokens, Token{Type: TokenWord, Value: "^", Pos: i, Length: 1})
			i++
			continue
		}

		// Tilde (fuzzy)
		if r == '~' {
			tokens = append(tokens, Token{Type: TokenWord, Value: "~", Pos: i, Length: 1})
			i++
			continue
		}

		// Read a word/term
		start := i
		var termBuilder strings.Builder

		for i < len(runes) && !unicode.IsSpace(runes[i]) && runes[i] != '"' &&
			runes[i] != '(' && runes[i] != ')' && runes[i] != '[' && runes[i] != '{' &&
			runes[i] != ']' && runes[i] != '}' && runes[i] != '~' && runes[i] != '^' {
			termBuilder.WriteRune(runes[i])
			i++
		}

		term := termBuilder.String()
		if term == "" {
			i++
			continue
		}

		// Check if this is a boolean operator
		upper := strings.ToUpper(term)
		switch upper {
		case "AND":
			tokens = append(tokens, Token{Type: TokenAND, Value: "AND", Pos: start, Length: len([]rune(term))})
			continue
		case "OR":
			tokens = append(tokens, Token{Type: TokenOR, Value: "OR", Pos: start, Length: len([]rune(term))})
			continue
		case "NOT":
			tokens = append(tokens, Token{Type: TokenNOT, Value: "NOT", Pos: start, Length: len([]rune(term))})
			continue
		}

		// Check for wildcards within the term
		hasWildcard := false
		for _, cr := range term {
			if cr == '*' {
				hasWildcard = true
				break
			}
		}

		if hasWildcard {
			tokens = append(tokens, Token{Type: TokenWildcard, Value: term, Pos: start, Length: len([]rune(term))})
		} else {
			tokens = append(tokens, Token{Type: TokenWord, Value: term, Pos: start, Length: len([]rune(term))})
		}
	}

	tokens = append(tokens, Token{Type: TokenEof, Value: "", Pos: i, Length: 0})
	return tokens, nil
}

// tokenizePhraseContent splits phrase content into individual word tokens.
func tokenizePhraseContent(phrase string) []string {
	// Split by spaces but preserve the phrase as a whole
	runes := []rune(phrase)
	var words []string
	var current strings.Builder

	for _, r := range runes {
		if unicode.IsSpace(r) {
			if current.Len() > 0 {
				words = append(words, current.String())
				current.Reset()
			}
		} else {
			current.WriteRune(r)
		}
	}
	if current.Len() > 0 {
		words = append(words, current.String())
	}
	return words
}

// CountTokens returns the number of non-EOF tokens.
func CountTokens(tokens []Token) int {
	count := 0
	for _, t := range tokens {
		if t.Type != TokenEof {
			count++
		}
	}
	return count
}

// TokenStream represents a cursor over a token sequence.
type TokenStream struct {
	tokens []Token
	pos    int
}

// NewTokenStream creates a new token stream from a token slice.
func NewTokenStream(tokens []Token) *TokenStream {
	return &TokenStream{tokens: tokens, pos: 0}
}

// Current returns the current token without advancing.
func (s *TokenStream) Current() Token {
	if s.pos >= len(s.tokens) {
		return Token{Type: TokenEof, Value: ""}
	}
	return s.tokens[s.pos]
}

// Next advances and returns the next token.
func (s *TokenStream) Next() Token {
	if s.pos >= len(s.tokens) {
		return Token{Type: TokenEof, Value: ""}
	}
	tok := s.tokens[s.pos]
	s.pos++
	return tok
}

// HasNext checks if there are more tokens.
func (s *TokenStream) HasNext() bool {
	return s.pos < len(s.tokens) && s.tokens[s.pos].Type != TokenEof
}

// Peek returns the next token without advancing.
func (s *TokenStream) Peek() Token {
	if s.pos+1 >= len(s.tokens) {
		return Token{Type: TokenEof, Value: ""}
	}
	return s.tokens[s.pos+1]
}

// IsTokenType checks if the current token matches the given type.
func (s *TokenStream) IsTokenType(t TokenType) bool {
	return s.Current().Type == t
}

// Expect advances past a token and verifies it matches the expected type.
func (s *TokenStream) Expect(expected TokenType) (Token, error) {
	tok := s.Current()
	if tok.Type != expected {
		return Token{}, fmt.Errorf("expected %s but got %s at position %d", expected, tok.Type, tok.Pos)
	}
	s.pos++
	return tok, nil
}

// AdvancePast skips all tokens until we find the expected type or hit EOF.
func (s *TokenStream) AdvancePast(expected TokenType) bool {
	for s.HasNext() && !s.IsTokenType(expected) {
		s.pos++
	}
	return s.HasNext() && s.IsTokenType(expected)
}
