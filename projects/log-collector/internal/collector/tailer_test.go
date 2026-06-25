package collector

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestTailerReadsNewContent(t *testing.T) {
	// Create a temp file with initial content
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	if err := os.WriteFile(path, []byte("existing line\n"), 0644); err != nil {
		t.Fatal(err)
	}

	output := make(chan RawLog, 100)
	tailer := NewTailer(path, output, 50*time.Millisecond)

	if err := tailer.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}

	// Give the tailer time to start
	time.Sleep(100 * time.Millisecond)

	// Append new content
	f, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		t.Fatal(err)
	}
	f.WriteString("new line 1\n")
	f.WriteString("new line 2\n")
	f.Close()

	// Wait for the tailer to pick up new lines
	time.Sleep(200 * time.Millisecond)

	tailer.Stop()
	close(output)

	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 new lines, got %d", len(logs))
	}

	if logs[0].Line != "new line 1" {
		t.Errorf("line 1 = %q, want %q", logs[0].Line, "new line 1")
	}
	if logs[1].Line != "new line 2" {
		t.Errorf("line 2 = %q, want %q", logs[1].Line, "new line 2")
	}
}

func TestTailerSkipsEmptyLines(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	if err := os.WriteFile(path, []byte(""), 0644); err != nil {
		t.Fatal(err)
	}

	output := make(chan RawLog, 100)
	tailer := NewTailer(path, output, 50*time.Millisecond)

	if err := tailer.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}

	time.Sleep(100 * time.Millisecond)

	// Append content with empty lines
	f, _ := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)
	f.WriteString("line 1\n\n\nline 2\n\n")
	f.Close()

	time.Sleep(200 * time.Millisecond)

	tailer.Stop()
	close(output)

	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 non-empty lines, got %d", len(logs))
	}
}

func TestTailerNonExistentFile(t *testing.T) {
	output := make(chan RawLog, 100)
	tailer := NewTailer("/tmp/nonexistent_file_for_test.log", output, 50*time.Millisecond)

	err := tailer.Start()
	if err == nil {
		t.Fatal("expected error for non-existent file")
	}
}

func TestTailerSource(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "source-test.log")

	if err := os.WriteFile(path, []byte(""), 0644); err != nil {
		t.Fatal(err)
	}

	output := make(chan RawLog, 100)
	tailer := NewTailer(path, output, 50*time.Millisecond)

	if err := tailer.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}

	time.Sleep(100 * time.Millisecond)

	f, _ := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0644)
	f.WriteString("test line\n")
	f.Close()

	time.Sleep(200 * time.Millisecond)

	tailer.Stop()
	close(output)

	for log := range output {
		if log.Source != path {
			t.Errorf("Source = %q, want %q", log.Source, path)
		}
	}
}

func TestTailerDefaultInterval(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")
	os.WriteFile(path, []byte(""), 0644)

	output := make(chan RawLog, 100)
	// Zero interval should use default
	tailer := NewTailer(path, output, 0)

	if tailer.interval != 500*time.Millisecond {
		t.Errorf("default interval = %v, want %v", tailer.interval, 500*time.Millisecond)
	}
}

func TestMultiTailer(t *testing.T) {
	dir := t.TempDir()
	path1 := filepath.Join(dir, "app.log")
	path2 := filepath.Join(dir, "error.log")

	os.WriteFile(path1, []byte(""), 0644)
	os.WriteFile(path2, []byte(""), 0644)

	output := make(chan RawLog, 100)
	mt := NewMultiTailer([]string{path1, path2}, output, 50*time.Millisecond)

	if err := mt.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}

	time.Sleep(100 * time.Millisecond)

	// Write to both files
	f1, _ := os.OpenFile(path1, os.O_APPEND|os.O_WRONLY, 0644)
	f1.WriteString("app log line\n")
	f1.Close()

	f2, _ := os.OpenFile(path2, os.O_APPEND|os.O_WRONLY, 0644)
	f2.WriteString("error log line\n")
	f2.Close()

	time.Sleep(300 * time.Millisecond)

	mt.Stop()
	close(output)

	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 lines from 2 files, got %d", len(logs))
	}
}

func TestMultiTailerNoFiles(t *testing.T) {
	output := make(chan RawLog, 100)
	mt := NewMultiTailer(nil, output, 50*time.Millisecond)

	err := mt.Start()
	if err == nil {
		t.Fatal("expected error for no files")
	}
}
