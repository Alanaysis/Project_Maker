package collector

import (
	"strings"
	"testing"
)

func TestCollectFromReader(t *testing.T) {
	input := "line one\nline two\nline three\n"
	reader := strings.NewReader(input)

	logs := CollectFromReader(reader, "test-source")

	if len(logs) != 3 {
		t.Fatalf("expected 3 logs, got %d", len(logs))
	}

	tests := []struct {
		line    string
		source  string
		lineNum int
	}{
		{"line one", "test-source", 1},
		{"line two", "test-source", 2},
		{"line three", "test-source", 3},
	}

	for i, tt := range tests {
		if logs[i].Line != tt.line {
			t.Errorf("log[%d].Line = %q, want %q", i, logs[i].Line, tt.line)
		}
		if logs[i].Source != tt.source {
			t.Errorf("log[%d].Source = %q, want %q", i, logs[i].Source, tt.source)
		}
		if logs[i].LineNum != tt.lineNum {
			t.Errorf("log[%d].LineNum = %d, want %d", i, logs[i].LineNum, tt.lineNum)
		}
	}
}

func TestCollectFromReaderSkipsEmptyLines(t *testing.T) {
	input := "line one\n\n\nline two\n\n"
	reader := strings.NewReader(input)

	logs := CollectFromReader(reader, "test")

	if len(logs) != 2 {
		t.Fatalf("expected 2 logs (empty lines skipped), got %d", len(logs))
	}
}

func TestCollectFromReaderEmpty(t *testing.T) {
	reader := strings.NewReader("")
	logs := CollectFromReader(reader, "test")

	if len(logs) != 0 {
		t.Fatalf("expected 0 logs, got %d", len(logs))
	}
}

func TestCollectorStartStop(t *testing.T) {
	rawCh := make(chan RawLog, 100)
	sources := []Source{
		{Name: "test", Path: "-"},
	}

	c := New(sources, rawCh)
	if err := c.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}

	// Done channel should eventually close
	c.Stop()
}

func TestCollectorNoSources(t *testing.T) {
	rawCh := make(chan RawLog, 100)
	c := New(nil, rawCh)

	if err := c.Start(); err == nil {
		t.Fatal("expected error for no sources")
	}
}

func TestCollectorFromReader(t *testing.T) {
	input := "2024-01-01 12:00:00 [INFO] server started\n2024-01-01 12:00:01 [ERROR] connection failed\n"
	reader := strings.NewReader(input)

	logs := CollectFromReader(reader, "app.log")

	if len(logs) != 2 {
		t.Fatalf("expected 2 logs, got %d", len(logs))
	}

	if !strings.Contains(logs[0].Line, "server started") {
		t.Error("first log should contain 'server started'")
	}
	if !strings.Contains(logs[1].Line, "connection failed") {
		t.Error("second log should contain 'connection failed'")
	}
}

func TestRawLogFields(t *testing.T) {
	log := RawLog{
		Line:    "test line",
		Source:  "file.log",
		LineNum: 42,
	}

	if log.Line != "test line" {
		t.Errorf("Line = %q, want %q", log.Line, "test line")
	}
	if log.Source != "file.log" {
		t.Errorf("Source = %q, want %q", log.Source, "file.log")
	}
	if log.LineNum != 42 {
		t.Errorf("LineNum = %d, want %d", log.LineNum, 42)
	}
}
