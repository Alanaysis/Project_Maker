package tests

import (
	"testing"

	"github.com/copyninja/inverted-index/internal/tokenizer"
)

func TestTokenize(t *testing.T) {
	tok := tokenizer.New()

	tests := []struct {
		name     string
		input    string
		expected []string
	}{
		{
			name:     "simple text",
			input:    "hello world",
			expected: []string{"hello", "world"},
		},
		{
			name:     "with stop words",
			input:    "the quick brown fox",
			expected: []string{"quick", "brown", "fox"},
		},
		{
			name:     "mixed case",
			input:    "Hello World",
			expected: []string{"hello", "world"},
		},
		{
			name:     "with punctuation",
			input:    "hello, world! how are you?",
			expected: []string{"hello", "world"},
		},
		{
			name:     "empty string",
			input:    "",
			expected: nil,
		},
		{
			name:     "only stop words",
			input:    "the a an is",
			expected: nil,
		},
		{
			name:     "with numbers",
			input:    "go 1.21 is great",
			expected: []string{"go", "1", "21", "great"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tok.Tokenize(tt.input)
			if len(result) != len(tt.expected) {
				t.Errorf("expected %d tokens, got %d: %v", len(tt.expected), len(result), result)
				return
			}
			for i, r := range result {
				if r != tt.expected[i] {
					t.Errorf("token[%d]: expected %q, got %q", i, tt.expected[i], r)
				}
			}
		})
	}
}

func TestTokenizeWithPositions(t *testing.T) {
	tok := tokenizer.New()

	result := tok.TokenizeWithPositions("the quick brown fox")
	if len(result) != 3 {
		t.Fatalf("expected 3 tokens, got %d", len(result))
	}

	expected := []tokenizer.Token{
		{Text: "quick", Position: 0},
		{Text: "brown", Position: 1},
		{Text: "fox", Position: 2},
	}

	for i, r := range result {
		if r.Text != expected[i].Text {
			t.Errorf("token[%d].Text: expected %q, got %q", i, expected[i].Text, r.Text)
		}
		if r.Position != expected[i].Position {
			t.Errorf("token[%d].Position: expected %d, got %d", i, expected[i].Position, r.Position)
		}
	}
}

func TestCustomStopWords(t *testing.T) {
	tok := tokenizer.NewWithStopWords([]string{"foo", "bar"})

	result := tok.Tokenize("foo bar baz qux")
	if len(result) != 2 {
		t.Fatalf("expected 2 tokens, got %d: %v", len(result), result)
	}
	if result[0] != "baz" || result[1] != "qux" {
		t.Errorf("unexpected tokens: %v", result)
	}
}
