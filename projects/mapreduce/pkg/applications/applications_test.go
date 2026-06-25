package applications

import (
	"testing"

	"mapreduce/internal/mapreduce"
)

func TestWordCountMap(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{
			name:     "empty string",
			input:    "",
			expected: 0,
		},
		{
			name:     "single word",
			input:    "hello",
			expected: 1,
		},
		{
			name:     "multiple words",
			input:    "hello world hello",
			expected: 3,
		},
		{
			name:     "with punctuation",
			input:    "hello, world! hello.",
			expected: 3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := WordCountMap("test.txt", tt.input)
			if len(result) != tt.expected {
				t.Errorf("WordCountMap returned %d items, expected %d", len(result), tt.expected)
			}
		})
	}
}

func TestWordCountReduce(t *testing.T) {
	tests := []struct {
		name     string
		key      string
		values   []string
		expected string
	}{
		{
			name:     "single value",
			key:      "hello",
			values:   []string{"1"},
			expected: "1",
		},
		{
			name:     "multiple values",
			key:      "hello",
			values:   []string{"1", "1", "1"},
			expected: "3",
		},
		{
			name:     "empty values",
			key:      "hello",
			values:   []string{},
			expected: "0",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := WordCountReduce(tt.key, tt.values)
			if result != tt.expected {
				t.Errorf("WordCountReduce(%s, %v) = %s, expected %s", tt.key, tt.values, result, tt.expected)
			}
		})
	}
}

func TestInvertedIndexMap(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{
			name:     "empty string",
			input:    "",
			expected: 0,
		},
		{
			name:     "single word",
			input:    "hello",
			expected: 1,
		},
		{
			name:     "duplicate words",
			input:    "hello hello world",
			expected: 2, // hello 和 world
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := InvertedIndexMap("doc1.txt", tt.input)
			if len(result) != tt.expected {
				t.Errorf("InvertedIndexMap returned %d items, expected %d", len(result), tt.expected)
			}
		})
	}
}

func TestInvertedIndexReduce(t *testing.T) {
	tests := []struct {
		name     string
		key      string
		values   []string
		expected string
	}{
		{
			name:     "single file",
			key:      "hello",
			values:   []string{"doc1.txt"},
			expected: "1 doc1.txt",
		},
		{
			name:     "multiple files",
			key:      "hello",
			values:   []string{"doc1.txt", "doc2.txt", "doc1.txt"},
			expected: "2 doc1.txt,doc2.txt",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := InvertedIndexReduce(tt.key, tt.values)
			if result != tt.expected {
				t.Errorf("InvertedIndexReduce(%s, %v) = %s, expected %s", tt.key, tt.values, result, tt.expected)
			}
		})
	}
}

func TestLogAnalysisMap(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected int
	}{
		{
			name:     "empty string",
			input:    "",
			expected: 0,
		},
		{
			name:     "single log entry",
			input:    `192.168.1.1 - - [15/Jan/2024:10:30:00 +0800] "GET /api/users HTTP/1.1" 200 1234`,
			expected: 3, // url, status, method
		},
		{
			name:     "multiple log entries",
			input:    "192.168.1.1 - - [...] \"GET /api/users HTTP/1.1\" 200 1234\n192.168.1.2 - - [...] \"POST /api/orders HTTP/1.1\" 201 567",
			expected: 6,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := LogAnalysisMap("access.log", tt.input)
			if len(result) != tt.expected {
				t.Errorf("LogAnalysisMap returned %d items, expected %d", len(result), tt.expected)
			}
		})
	}
}

func TestLogAnalysisReduce(t *testing.T) {
	tests := []struct {
		name     string
		key      string
		values   []string
		expected string
	}{
		{
			name:     "single access",
			key:      "/api/users",
			values:   []string{"1"},
			expected: "1",
		},
		{
			name:     "multiple accesses",
			key:      "/api/users",
			values:   []string{"1", "1", "1", "1", "1"},
			expected: "5",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := LogAnalysisReduce(tt.key, tt.values)
			if result != tt.expected {
				t.Errorf("LogAnalysisReduce(%s, %v) = %s, expected %s", tt.key, tt.values, result, tt.expected)
			}
		})
	}
}

func BenchmarkWordCountMap(b *testing.B) {
	content := "the quick brown fox jumps over the lazy dog " +
		"the quick brown fox jumps over the lazy dog " +
		"the quick brown fox jumps over the lazy dog"

	for i := 0; i < b.N; i++ {
		WordCountMap("bench.txt", content)
	}
}

func BenchmarkWordCountReduce(b *testing.B) {
	values := make([]string, 1000)
	for i := range values {
		values[i] = "1"
	}

	for i := 0; i < b.N; i++ {
		WordCountReduce("word", values)
	}
}
