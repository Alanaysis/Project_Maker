package source

import (
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

func TestFileSource(t *testing.T) {
	// Create a temporary test file
	tmpDir := t.TempDir()
	testFile := filepath.Join(tmpDir, "test.txt")

	content := "line1\nline2\nline3\nline4\nline5\n"
	if err := os.WriteFile(testFile, []byte(content), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	t.Run("BasicRead", func(t *testing.T) {
		src := NewFileSource(testFile)
		stream, err := src.Open()
		if err != nil {
			t.Fatalf("Failed to open source: %v", err)
		}

		var events []core.Event
		for e := range stream.Events() {
			events = append(events, e)
		}

		if len(events) != 5 {
			t.Errorf("Expected 5 events, got %d", len(events))
		}

		if events[0].Value.(string) != "line1" {
			t.Errorf("Expected 'line1', got '%s'", events[0].Value.(string))
		}
	})

	t.Run("WithKeyFunc", func(t *testing.T) {
		src := NewFileSource(testFile,
			WithKeyFunc(func(line string, lineNum int) string {
				return "key"
			}),
		)
		stream, err := src.Open()
		if err != nil {
			t.Fatalf("Failed to open source: %v", err)
		}

		for e := range stream.Events() {
			if e.Key != "key" {
				t.Errorf("Expected key 'key', got '%s'", e.Key)
			}
		}
	})

	t.Run("WithValueFunc", func(t *testing.T) {
		src := NewFileSource(testFile,
			WithValueFunc(func(line string) interface{} {
				return len(line)
			}),
		)
		stream, err := src.Open()
		if err != nil {
			t.Fatalf("Failed to open source: %v", err)
		}

		for e := range stream.Events() {
			if _, ok := e.Value.(int); !ok {
				t.Errorf("Expected int value, got %T", e.Value)
			}
		}
	})

	t.Run("Stop", func(t *testing.T) {
		src := NewFileSource(testFile)
		stream, err := src.Open()
		if err != nil {
			t.Fatalf("Failed to open source: %v", err)
		}

		// Read first event
		<-stream.Events()

		// Stop the source
		if err := src.Stop(); err != nil {
			t.Fatalf("Failed to stop source: %v", err)
		}

		// Wait a bit for the goroutine to finish
		time.Sleep(100 * time.Millisecond)
	})

	t.Run("FileNotFound", func(t *testing.T) {
		src := NewFileSource("/nonexistent/file.txt")
		_, err := src.Open()
		if err == nil {
			t.Error("Expected error for nonexistent file")
		}
	})
}

func TestSocketSource(t *testing.T) {
	t.Run("Name", func(t *testing.T) {
		src := NewSocketSource("tcp", "localhost:9999")
		if src.Name() != "socket:tcp://localhost:9999" {
			t.Errorf("Expected 'socket:tcp://localhost:9999', got '%s'", src.Name())
		}
	})
}

func TestKafkaSource(t *testing.T) {
	t.Run("MockConsumer", func(t *testing.T) {
		messages := []KafkaMessage{
			{Topic: "test", Key: "key1", Value: "value1", Timestamp: time.Now()},
			{Topic: "test", Key: "key2", Value: "value2", Timestamp: time.Now()},
			{Topic: "test", Key: "key3", Value: "value3", Timestamp: time.Now()},
		}

		consumer := NewMockKafkaConsumer(messages)
		src := NewKafkaSource(consumer, []string{"test"})

		if src.Name() != "kafka:[test]" {
			t.Errorf("Expected 'kafka:[test]', got '%s'", src.Name())
		}
	})
}

func TestParseCSVLine(t *testing.T) {
	tests := []struct {
		line      string
		delimiter string
		expected  []string
	}{
		{"a,b,c", ",", []string{"a", "b", "c"}},
		{"a|b|c", "|", []string{"a", "b", "c"}},
		{"single", ",", []string{"single"}},
	}

	for _, tt := range tests {
		result := ParseCSVLine(tt.line, tt.delimiter)
		if len(result) != len(tt.expected) {
			t.Errorf("ParseCSVLine(%q, %q): expected %d fields, got %d",
				tt.line, tt.delimiter, len(tt.expected), len(result))
		}
	}
}

func TestParseKeyValueLine(t *testing.T) {
	tests := []struct {
		line      string
		delimiter string
		expKey    string
		expValue  string
	}{
		{"key:value", ":", "key", "value"},
		{"name=John", "=", "name", "John"},
		{"no delimiter", ":", "default", "no delimiter"},
	}

	for _, tt := range tests {
		key, value := ParseKeyValueLine(tt.line, tt.delimiter)
		if key != tt.expKey || value != tt.expValue {
			t.Errorf("ParseKeyValueLine(%q, %q): expected (%q, %q), got (%q, %q)",
				tt.line, tt.delimiter, tt.expKey, tt.expValue, key, value)
		}
	}
}
