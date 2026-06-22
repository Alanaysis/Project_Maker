package tokenizer

import (
	"strings"
	"unicode"
)

// Tokenizer handles text tokenization for the inverted index.
type Tokenizer struct {
	stopWords map[string]bool
}

// New creates a new Tokenizer with default English stop words.
func New() *Tokenizer {
	return &Tokenizer{
		stopWords: defaultStopWords(),
	}
}

// NewWithStopWords creates a Tokenizer with custom stop words.
func NewWithStopWords(stopWords []string) *Tokenizer {
	sw := make(map[string]bool, len(stopWords))
	for _, w := range stopWords {
		sw[strings.ToLower(w)] = true
	}
	return &Tokenizer{stopWords: sw}
}

// Tokenize splits text into normalized tokens, removing stop words.
func (t *Tokenizer) Tokenize(text string) []string {
	words := strings.FieldsFunc(text, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsDigit(r)
	})

	var tokens []string
	for _, w := range words {
		w = strings.ToLower(w)
		if len(w) > 0 && !t.stopWords[w] {
			tokens = append(tokens, w)
		}
	}
	return tokens
}

// TokenizeWithPositions returns tokens with their positions in the text.
func (t *Tokenizer) TokenizeWithPositions(text string) []Token {
	lower := strings.ToLower(text)
	words := strings.FieldsFunc(lower, func(r rune) bool {
		return !unicode.IsLetter(r) && !unicode.IsDigit(r)
	})

	var tokens []Token
	pos := 0
	offset := 0
	for _, w := range words {
		if len(w) > 0 && !t.stopWords[w] {
			tokens = append(tokens, Token{
				Text:     w,
				Position: pos,
				Offset:   offset,
			})
			pos++
		}
		offset += len(w) + 1 // +1 for the separator
	}
	return tokens
}

// Token represents a token with its position information.
type Token struct {
	Text     string
	Position int
	Offset   int
}

func defaultStopWords() map[string]bool {
	words := []string{
		"a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
		"for", "of", "with", "by", "from", "is", "it", "that", "this",
		"was", "are", "be", "has", "had", "have", "do", "does", "did",
		"will", "would", "could", "should", "may", "might", "can",
		"not", "no", "nor", "so", "if", "then", "than", "too", "very",
		"just", "about", "above", "after", "again", "all", "also",
		"am", "any", "as", "because", "been", "before", "being",
		"between", "both", "during", "each", "few", "get", "got",
		"he", "her", "here", "him", "his", "how", "i", "into", "its",
		"let", "like", "make", "me", "more", "most", "my", "new", "now",
		"only", "our", "out", "over", "own", "re", "same", "she",
		"some", "such", "their", "them", "there", "these", "they",
		"those", "through", "under", "up", "us", "want", "we", "what",
		"when", "where", "which", "while", "who", "whom", "why", "you",
		"your",
	}
	sw := make(map[string]bool, len(words))
	for _, w := range words {
		sw[w] = true
	}
	return sw
}
