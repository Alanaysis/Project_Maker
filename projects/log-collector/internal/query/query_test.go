package query

import (
	"testing"
	"time"

	"github.com/project/log-collector/internal/storage"
)

func setupStore() *storage.Storage {
	s := storage.New()

	now := time.Now()
	s.Store(storage.Entry{
		Timestamp: now.Add(-2 * time.Hour),
		Level:     storage.LevelInfo,
		Message:   "server started",
		Source:    "app.log",
		Fields:    map[string]string{"port": "8080"},
	})
	s.Store(storage.Entry{
		Timestamp: now.Add(-1 * time.Hour),
		Level:     storage.LevelWarn,
		Message:   "high memory usage",
		Source:    "app.log",
		Fields:    map[string]string{"memory": "90%"},
	})
	s.Store(storage.Entry{
		Timestamp: now.Add(-30 * time.Minute),
		Level:     storage.LevelError,
		Message:   "database connection timeout",
		Source:    "error.log",
		Fields:    map[string]string{"host": "db.example.com"},
	})
	s.Store(storage.Entry{
		Timestamp: now,
		Level:     storage.LevelError,
		Message:   "request failed: connection refused",
		Source:    "error.log",
		Fields:    map[string]string{"endpoint": "/api/users"},
	})

	return s
}

func TestSearch(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results := e.Search("connection", 10)
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestSearchNoResults(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results := e.Search("nonexistent", 10)
	if len(results) != 0 {
		t.Fatalf("expected 0 results, got %d", len(results))
	}
}

func TestByLevel(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results := e.ByLevel(storage.LevelError, 10)
	if len(results) != 2 {
		t.Fatalf("expected 2 error results, got %d", len(results))
	}
}

func TestByTimeRange(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	now := time.Now()
	start := now.Add(-90 * time.Minute)
	end := now.Add(-20 * time.Minute)

	results := e.ByTimeRange(start, end, 10)
	if len(results) != 2 {
		t.Fatalf("expected 2 results in range, got %d", len(results))
	}
}

func TestRecent(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results := e.Recent(2)
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	// Should contain the two most recent entries (both from "now")
	found := map[string]bool{}
	for _, r := range results {
		found[r.Message] = true
	}
	if !found["request failed: connection refused"] {
		t.Error("expected 'request failed: connection refused' in recent results")
	}
	if !found["database connection timeout"] && !found["high memory usage"] {
		t.Error("expected second recent entry in results")
	}
}

func TestErrors(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results := e.Errors(10)
	if len(results) != 2 {
		t.Fatalf("expected 2 error results, got %d", len(results))
	}
}

func TestAdvancedQueryLevel(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("level:error")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestAdvancedQuerySource(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("source:app")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestAdvancedQueryMessage(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("message:timeout")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
}

func TestAdvancedQueryFreeText(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("connection")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestAdvancedQueryDateRange(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	yesterday := time.Now().AddDate(0, 0, -1).Format("2006-01-02")
	tomorrow := time.Now().AddDate(0, 0, 1).Format("2006-01-02")

	results, err := e.AdvancedQuery("after:" + yesterday + " before:" + tomorrow)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 4 {
		t.Fatalf("expected 4 results, got %d", len(results))
	}
}

func TestAdvancedQueryInvalidDate(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	_, err := e.AdvancedQuery("after:not-a-date")
	if err == nil {
		t.Fatal("expected error for invalid date")
	}
}

func TestAdvancedQueryCombined(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("level:error source:error.log")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
}

func TestAdvancedQueryLimit(t *testing.T) {
	s := setupStore()
	e := NewEngine(s)

	results, err := e.AdvancedQuery("level:error limit:1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("expected 1 result, got %d", len(results))
	}
}

func TestFormatEntries(t *testing.T) {
	entries := []storage.Entry{
		{
			Timestamp: time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC),
			Level:     storage.LevelInfo,
			Message:   "test message",
			Source:    "app.log",
			LineNum:   1,
		},
	}

	output := FormatEntries(entries)
	if output == "" {
		t.Fatal("expected non-empty output")
	}
	if output == "No entries found." {
		t.Fatal("expected formatted entries, got 'no entries'")
	}
}

func TestFormatEntriesEmpty(t *testing.T) {
	output := FormatEntries(nil)
	if output != "No entries found." {
		t.Errorf("expected 'No entries found.', got %q", output)
	}
}

func TestFormatEntriesWithFields(t *testing.T) {
	entries := []storage.Entry{
		{
			Timestamp: time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC),
			Level:     storage.LevelInfo,
			Message:   "test",
			Source:    "app.log",
			LineNum:   1,
			Fields:    map[string]string{"user": "alice"},
		},
	}

	output := FormatEntries(entries)
	if output == "" || output == "No entries found." {
		t.Fatal("expected formatted output with fields")
	}
}

func TestFormatStats(t *testing.T) {
	stats := storage.Stats{
		TotalEntries: 100,
		LevelCounts:  map[string]int{"INFO": 80, "ERROR": 20},
		SourceCounts: map[string]int{"app.log": 60, "error.log": 40},
		OldestEntry:  time.Now().Add(-time.Hour),
		NewestEntry:  time.Now(),
	}

	output := FormatStats(stats)
	if output == "" {
		t.Fatal("expected non-empty output")
	}
}
