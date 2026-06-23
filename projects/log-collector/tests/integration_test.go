// Package tests provides integration tests for the log-collector system.
//
// These tests exercise the full pipeline: collector -> parser -> storage -> query,
// verifying that all components work together correctly.
package tests

import (
	"strings"
	"testing"
	"time"

	"github.com/project/log-collector/internal/collector"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/query"
	"github.com/project/log-collector/internal/storage"
)

// TestFullPipelineJSON tests the complete pipeline with JSON log format.
func TestFullPipelineJSON(t *testing.T) {
	input := `{"level":"info","msg":"server started","port":"8080"}
{"level":"error","msg":"connection timeout","host":"db.example.com"}
{"level":"warn","msg":"high memory usage","memory":"90%"}
{"level":"info","msg":"request processed","endpoint":"/api/users"}`

	// Collect
	logs := collector.CollectFromReader(strings.NewReader(input), "app.log")
	if len(logs) != 4 {
		t.Fatalf("expected 4 collected logs, got %d", len(logs))
	}

	// Parse and store
	store := storage.New()
	p := parser.New(parser.FormatJSON)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error on line %d: %v", raw.LineNum, err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	// Verify storage count
	if store.Count() != 4 {
		t.Fatalf("expected 4 stored entries, got %d", store.Count())
	}

	// Query by level
	engine := query.NewEngine(store)
	errors := engine.ByLevel(storage.LevelError, 10)
	if len(errors) != 1 {
		t.Fatalf("expected 1 error entry, got %d", len(errors))
	}
	if errors[0].Message != "connection timeout" {
		t.Errorf("expected 'connection timeout', got %q", errors[0].Message)
	}

	// Search by text
	results := engine.Search("memory", 10)
	if len(results) != 1 {
		t.Fatalf("expected 1 search result, got %d", len(results))
	}

	// Verify fields
	entry, err := store.GetByID(1)
	if err != nil {
		t.Fatalf("GetByID(1) error: %v", err)
	}
	if entry.Fields["port"] != "8080" {
		t.Errorf("expected port=8080, got %q", entry.Fields["port"])
	}
}

// TestFullPipelineLogfmt tests the complete pipeline with logfmt format.
func TestFullPipelineLogfmt(t *testing.T) {
	input := `level=info msg="server started" port=8080
level=error msg="database error" host=db.example.com
level=debug msg="processing request" id=12345`

	logs := collector.CollectFromReader(strings.NewReader(input), "service.log")
	if len(logs) != 3 {
		t.Fatalf("expected 3 collected logs, got %d", len(logs))
	}

	store := storage.New()
	p := parser.New(parser.FormatLogfmt)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error on line %d: %v", raw.LineNum, err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	if store.Count() != 3 {
		t.Fatalf("expected 3 stored entries, got %d", store.Count())
	}

	engine := query.NewEngine(store)
	debugs := engine.ByLevel(storage.LevelDebug, 10)
	if len(debugs) != 1 {
		t.Fatalf("expected 1 debug entry, got %d", len(debugs))
	}
}

// TestFullPipelineCommon tests the complete pipeline with common log format.
func TestFullPipelineCommon(t *testing.T) {
	input := `2024-01-15 10:00:00 [INFO] Application started
2024-01-15 10:00:01 [ERROR] Failed to connect to database
2024-01-15 10:00:02 [WARN] Slow query detected
2024-01-15 10:00:03 [INFO] Request handled successfully
2024-01-15 10:00:04 [FATAL] Out of memory`

	logs := collector.CollectFromReader(strings.NewReader(input), "system.log")
	if len(logs) != 5 {
		t.Fatalf("expected 5 collected logs, got %d", len(logs))
	}

	store := storage.New()
	p := parser.New(parser.FormatCommon)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error on line %d: %v", raw.LineNum, err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	// Verify all entries stored
	if store.Count() != 5 {
		t.Fatalf("expected 5 stored entries, got %d", store.Count())
	}

	engine := query.NewEngine(store)

	// Query errors and fatals
	errorsAndFatals := engine.Errors(10)
	if len(errorsAndFatals) != 2 {
		t.Fatalf("expected 2 error/fatal entries, got %d", len(errorsAndFatals))
	}

	// Verify stats
	stats := store.Stats()
	if stats.TotalEntries != 5 {
		t.Errorf("TotalEntries = %d, want 5", stats.TotalEntries)
	}
	if stats.LevelCounts["INFO"] != 2 {
		t.Errorf("INFO count = %d, want 2", stats.LevelCounts["INFO"])
	}
	if stats.LevelCounts["ERROR"] != 1 {
		t.Errorf("ERROR count = %d, want 1", stats.LevelCounts["ERROR"])
	}
	if stats.LevelCounts["FATAL"] != 1 {
		t.Errorf("FATAL count = %d, want 1", stats.LevelCounts["FATAL"])
	}
}

// TestFullPipelineAutoDetect tests auto-detection of mixed log formats.
func TestFullPipelineAutoDetect(t *testing.T) {
	input := `{"level":"info","msg":"json log"}
level=error msg=logfmt_log
2024-01-15 10:00:00 [WARN] common format log
plain text log line`

	logs := collector.CollectFromReader(strings.NewReader(input), "mixed.log")
	if len(logs) != 4 {
		t.Fatalf("expected 4 collected logs, got %d", len(logs))
	}

	store := storage.New()
	p := parser.New(parser.FormatAuto)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error on line %d: %v", raw.LineNum, err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	if store.Count() != 4 {
		t.Fatalf("expected 4 stored entries, got %d", store.Count())
	}

	// Verify auto-detection worked for each format
	entry1, _ := store.GetByID(1)
	if entry1.Level != storage.LevelInfo {
		t.Errorf("entry1 level = %v, want INFO", entry1.Level)
	}

	entry2, _ := store.GetByID(2)
	if entry2.Level != storage.LevelError {
		t.Errorf("entry2 level = %v, want ERROR", entry2.Level)
	}

	entry3, _ := store.GetByID(3)
	if entry3.Level != storage.LevelWarn {
		t.Errorf("entry3 level = %v, want WARN", entry3.Level)
	}

	entry4, _ := store.GetByID(4)
	if entry4.Level != storage.LevelUnknown {
		t.Errorf("entry4 level = %v, want UNKNOWN", entry4.Level)
	}
}

// TestAdvancedQueryIntegration tests advanced query features end-to-end.
func TestAdvancedQueryIntegration(t *testing.T) {
	input := `2024-01-15 10:00:00 [INFO] Server started on port 8080
2024-01-15 10:00:01 [INFO] Connected to database
2024-01-15 10:00:02 [ERROR] Failed to authenticate user
2024-01-15 10:00:03 [WARN] Slow query detected: 2.5s
2024-01-15 10:00:04 [ERROR] Connection refused by upstream
2024-01-15 10:00:05 [INFO] Request completed successfully
2024-01-15 10:00:06 [DEBUG] Cache miss for key user:123
2024-01-15 10:00:07 [INFO] Shutting down gracefully`

	logs := collector.CollectFromReader(strings.NewReader(input), "app.log")

	store := storage.New()
	p := parser.New(parser.FormatCommon)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error: %v", err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	engine := query.NewEngine(store)

	// Test level query
	results, err := engine.AdvancedQuery("level:error")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("level:error expected 2 results, got %d", len(results))
	}

	// Test combined level + message query
	results, err = engine.AdvancedQuery("level:info message:server")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("level:info message:server expected 1 result, got %d", len(results))
	}

	// Test source filter
	results, err = engine.AdvancedQuery("source:app")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 8 {
		t.Fatalf("source:app expected 8 results, got %d", len(results))
	}

	// Test limit
	results, err = engine.AdvancedQuery("level:info limit:2")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("limit:2 expected 2 results, got %d", len(results))
	}

	// Test free text search (case-insensitive substring match)
	results, err = engine.AdvancedQuery("connection")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("free text 'connection' expected 1 result, got %d", len(results))
	}

	// Test free text search matching multiple entries
	results, err = engine.AdvancedQuery("database")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 1 {
		t.Fatalf("free text 'database' expected 1 result, got %d", len(results))
	}
}

// TestMultipleSources tests collecting from multiple sources.
func TestMultipleSources(t *testing.T) {
	appLog := "2024-01-15 10:00:00 [INFO] App started\n2024-01-15 10:00:01 [ERROR] App error"
	dbLog := "2024-01-15 10:00:00 [INFO] DB connected\n2024-01-15 10:00:02 [WARN] DB slow query"

	store := storage.New()
	p := parser.New(parser.FormatCommon)

	// Collect from app.log
	logs1 := collector.CollectFromReader(strings.NewReader(appLog), "app.log")
	for _, raw := range logs1 {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error: %v", err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	// Collect from db.log
	logs2 := collector.CollectFromReader(strings.NewReader(dbLog), "db.log")
	for _, raw := range logs2 {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error: %v", err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	if store.Count() != 4 {
		t.Fatalf("expected 4 total entries, got %d", store.Count())
	}

	engine := query.NewEngine(store)

	// Query by source
	results, err := engine.AdvancedQuery("source:app")
	if err != nil {
		t.Fatalf("AdvancedQuery error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("source:app expected 2 results, got %d", len(results))
	}

	results2, err2 := engine.AdvancedQuery("source:db")
	if err2 != nil {
		t.Fatalf("AdvancedQuery error: %v", err2)
	}
	if len(results2) != 2 {
		t.Fatalf("source:db expected 2 results, got %d", len(results2))
	}

	// Verify stats show both sources
	stats := store.Stats()
	if stats.SourceCounts["app.log"] != 2 {
		t.Errorf("app.log count = %d, want 2", stats.SourceCounts["app.log"])
	}
	if stats.SourceCounts["db.log"] != 2 {
		t.Errorf("db.log count = %d, want 2", stats.SourceCounts["db.log"])
	}
}

// TestLargeVolume tests handling of a larger volume of logs.
func TestLargeVolume(t *testing.T) {
	store := storage.New()
	p := parser.New(parser.FormatAuto)

	// Generate 1000 log entries
	levels := []string{"INFO", "ERROR", "WARN", "DEBUG", "FATAL"}
	for i := 0; i < 1000; i++ {
		level := levels[i%len(levels)]
		line := "2024-01-15 10:00:00 [" + level + "] Log message number " + strings.Repeat("x", i%100)

		entry, err := p.Parse(line, "bulk.log", i+1)
		if err != nil {
			t.Fatalf("parse error at line %d: %v", i+1, err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	if store.Count() != 1000 {
		t.Fatalf("expected 1000 entries, got %d", store.Count())
	}

	engine := query.NewEngine(store)

	// Test limit
	recent := engine.Recent(10)
	if len(recent) != 10 {
		t.Fatalf("Recent(10) expected 10, got %d", len(recent))
	}

	// Test level query
	errors := engine.ByLevel(storage.LevelError, 1000)
	if len(errors) != 200 {
		t.Fatalf("expected 200 errors, got %d", len(errors))
	}

	// Test search for message substring
	searchResults := engine.Search("Log message number", 10)
	if len(searchResults) != 10 {
		t.Fatalf("search 'Log message number' expected 10 results (limited), got %d", len(searchResults))
	}

	// Test stats
	stats := store.Stats()
	if stats.TotalEntries != 1000 {
		t.Errorf("TotalEntries = %d, want 1000", stats.TotalEntries)
	}
}

// TestTimeRangeQueryIntegration tests time-based queries with parsed timestamps.
func TestTimeRangeQueryIntegration(t *testing.T) {
	input := `2024-01-15 08:00:00 [INFO] Morning start
2024-01-15 12:00:00 [INFO] Noon check
2024-01-15 16:00:00 [INFO] Afternoon update
2024-01-15 20:00:00 [INFO] Evening shutdown`

	logs := collector.CollectFromReader(strings.NewReader(input), "schedule.log")

	store := storage.New()
	p := parser.New(parser.FormatCommon)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			t.Fatalf("parse error: %v", err)
		}
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     storage.Level(entry.Level),
			Message:   entry.Message,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	engine := query.NewEngine(store)

	// Query entries between 10:00 and 18:00
	start := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
	end := time.Date(2024, 1, 15, 18, 0, 0, 0, time.UTC)
	results := engine.ByTimeRange(start, end, 100)

	if len(results) != 2 {
		t.Fatalf("time range query expected 2 results, got %d", len(results))
	}

	// Verify the correct entries are returned
	foundNoon := false
	foundAfternoon := false
	for _, r := range results {
		if strings.Contains(r.Message, "Noon") {
			foundNoon = true
		}
		if strings.Contains(r.Message, "Afternoon") {
			foundAfternoon = true
		}
	}
	if !foundNoon {
		t.Error("expected 'Noon check' in results")
	}
	if !foundAfternoon {
		t.Error("expected 'Afternoon update' in results")
	}
}

// TestEmptyAndEdgeCases tests various edge cases.
func TestEmptyAndEdgeCases(t *testing.T) {
	// Empty input
	logs := collector.CollectFromReader(strings.NewReader(""), "empty.log")
	if len(logs) != 0 {
		t.Fatalf("expected 0 logs from empty input, got %d", len(logs))
	}

	// Only empty lines
	logs = collector.CollectFromReader(strings.NewReader("\n\n\n"), "blank.log")
	if len(logs) != 0 {
		t.Fatalf("expected 0 logs from blank input, got %d", len(logs))
	}

	// Single line
	logs = collector.CollectFromReader(strings.NewReader("single line"), "one.log")
	if len(logs) != 1 {
		t.Fatalf("expected 1 log, got %d", len(logs))
	}

	// Parse with auto-detect on unparsable content
	p := parser.New(parser.FormatAuto)
	entry, err := p.Parse("just plain text with no structure", "test", 1)
	if err != nil {
		t.Fatalf("auto-detect should handle plain text, got error: %v", err)
	}
	if entry.Level != parser.LevelUnknown {
		t.Errorf("plain text level = %v, want UNKNOWN", entry.Level)
	}

	// Storage clear and reuse
	store := storage.New()
	store.Store(storage.Entry{Timestamp: time.Now(), Level: storage.LevelInfo, Message: "test"})
	store.Clear()
	if store.Count() != 0 {
		t.Fatalf("expected 0 after clear, got %d", store.Count())
	}

	// GetByID with invalid ID
	_, err = store.GetByID(0)
	if err == nil {
		t.Error("expected error for GetByID(0)")
	}
	_, err = store.GetByID(999)
	if err == nil {
		t.Error("expected error for GetByID(999)")
	}
}

// TestFormatOutput tests the query output formatting.
func TestFormatOutput(t *testing.T) {
	entries := []storage.Entry{
		{
			Timestamp: time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC),
			Level:     storage.LevelInfo,
			Message:   "test message",
			Source:    "app.log",
			LineNum:   1,
			Fields:    map[string]string{"user": "alice"},
		},
		{
			Timestamp: time.Date(2024, 1, 15, 10, 30, 1, 0, time.UTC),
			Level:     storage.LevelError,
			Message:   "error occurred",
			Source:    "error.log",
			LineNum:   5,
		},
	}

	// Test FormatEntries
	output := query.FormatEntries(entries)
	if output == "" {
		t.Fatal("FormatEntries returned empty string")
	}
	if output == "No entries found." {
		t.Fatal("FormatEntries returned 'No entries found.' for non-empty input")
	}
	if !strings.Contains(output, "test message") {
		t.Error("output should contain 'test message'")
	}
	if !strings.Contains(output, "error occurred") {
		t.Error("output should contain 'error occurred'")
	}

	// Test FormatEntries with empty input
	emptyOutput := query.FormatEntries(nil)
	if emptyOutput != "No entries found." {
		t.Errorf("FormatEntries(nil) = %q, want 'No entries found.'", emptyOutput)
	}

	// Test FormatStats
	stats := storage.Stats{
		TotalEntries: 100,
		LevelCounts:  map[string]int{"INFO": 60, "ERROR": 30, "WARN": 10},
		SourceCounts: map[string]int{"app.log": 70, "error.log": 30},
		OldestEntry:  time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		NewestEntry:  time.Date(2024, 1, 15, 23, 59, 59, 0, time.UTC),
	}
	statsOutput := query.FormatStats(stats)
	if statsOutput == "" {
		t.Fatal("FormatStats returned empty string")
	}
	if !strings.Contains(statsOutput, "100") {
		t.Error("stats output should contain total count '100'")
	}
}

// TestCollectorWithFiles tests collecting from actual file paths.
func TestCollectorWithFiles(t *testing.T) {
	// Test that Collector handles non-existent files gracefully
	rawCh := make(chan collector.RawLog, 100)
	sources := []collector.Source{
		{Name: "nonexistent", Path: "/tmp/nonexistent_file_for_test.log"},
	}
	c := collector.New(sources, rawCh)

	// Start should succeed (errors are logged, not returned)
	if err := c.Start(); err != nil {
		t.Fatalf("Start() should not error for missing file: %v", err)
	}

	// Wait for completion
	<-c.Done()

	// Channel should be empty (file doesn't exist)
	if len(rawCh) != 0 {
		t.Errorf("expected 0 logs from nonexistent file, got %d", len(rawCh))
	}
}

// TestConcurrentAccess tests that storage handles concurrent access safely.
func TestConcurrentAccess(t *testing.T) {
	store := storage.New()
	done := make(chan bool)

	// Concurrent writers
	for i := 0; i < 10; i++ {
		go func(n int) {
			for j := 0; j < 100; j++ {
				store.Store(storage.Entry{
					Timestamp: time.Now(),
					Level:     storage.LevelInfo,
					Message:   "concurrent write",
				})
			}
			done <- true
		}(i)
	}

	// Concurrent readers
	for i := 0; i < 5; i++ {
		go func() {
			for j := 0; j < 50; j++ {
				store.Count()
				store.Stats()
			}
			done <- true
		}()
	}

	// Wait for all goroutines
	for i := 0; i < 15; i++ {
		<-done
	}

	// Verify final count
	if store.Count() != 1000 {
		t.Fatalf("expected 1000 entries after concurrent writes, got %d", store.Count())
	}
}
