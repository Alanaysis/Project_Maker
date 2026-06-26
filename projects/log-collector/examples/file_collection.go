// File log collection example.
//
// This example demonstrates collecting logs from files using the collector package.
// It shows:
// 1. Reading logs from multiple files
// 2. Auto-detecting log formats (JSON, logfmt, common)
// 3. Parsing and structuring log entries
// 4. Multi-line handling for stack traces
//
// Run: go run examples/file_collection.go

package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/project/log-collector/internal/collector"
	"github.com/project/log-collector/internal/filter"
	"github.com/project/log-collector/internal/forwarder"
	"github.com/project/log-collector/internal/multiline"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/storage"
	"github.com/project/log-collector/internal/transport"
)

func main() {
	fmt.Println("=== Log Collector - File Collection Example ===")
	fmt.Println()

	// Step 1: Create sample log files
	fmt.Println("Step 1: Creating sample log files...")
	createSampleLogs()
	fmt.Println()

	// Step 2: Collect logs from files
	fmt.Println("Step 2: Collecting logs from files...")
	logs := collectFromFiles([]string{"app.log", "error.log"})
	fmt.Printf("Collected %d raw log lines\n", len(logs))
	fmt.Println()

	// Step 3: Parse logs with auto-detection
	fmt.Println("Step 3: Parsing logs (auto-detect format)...")
	parseAndDisplay(logs, parser.FormatAuto)
	fmt.Println()

	// Step 4: Parse logs with JSON format
	fmt.Println("Step 4: Parsing logs (JSON format)...")
	logs2 := collectFromFiles([]string{"app.log"})
	parseAndDisplayFormat(logs2, parser.FormatJSON)
	fmt.Println()

	// Step 5: Parse logs with common format
	fmt.Println("Step 5: Parsing logs (common format)...")
	logs3 := collectFromFiles([]string{"error.log"})
	parseAndDisplayFormat(logs3, parser.FormatCommon)
	fmt.Println()

	// Step 6: Store parsed entries
	fmt.Println("Step 6: Storing parsed entries with indexing...")
	store, stats := storeEntries(logs)
	fmt.Printf("Stored %d entries\n", store.Count())
	fmt.Printf("Stats:\n%s", storage.FormatStats(stats))
	fmt.Println()

	// Step 7: Query stored entries
	fmt.Println("Step 7: Querying stored entries...")
	queryExamples(store)
	fmt.Println()

	// Step 8: Demonstrate filtering
	fmt.Println("Step 8: Demonstrating filtering...")
	filterExamples(logs)
	fmt.Println()

	// Step 9: Demonstrate multi-line handling
	fmt.Println("Step 9: Demonstrating multi-line handling...")
	multilineExample()
	fmt.Println()

	// Step 10: Demonstrate forwarder
	fmt.Println("Step 10: Demonstrating forwarder concepts...")
	forwarderExample()
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}

// createSampleLogs creates sample log files for demonstration.
func createSampleLogs() {
	// Create app.log with JSON format
	appLog := `{
"level":"info","msg":"server started","port":8080,"ts":"2024-01-15T10:00:00Z"}
{"level":"info","msg":"listening on :8080","ts":"2024-01-15T10:00:01Z"}
{"level":"info","msg":"request handled","method":"GET","path":"/api/users","status":200,"duration_ms":15,"ts":"2024-01-15T10:00:02Z"}
{"level":"warn","msg":"slow query detected","table":"users","duration_ms":500,"ts":"2024-01-15T10:00:03Z"}
{"level":"error","msg":"connection timeout","host":"db.example.com","timeout_ms":30000,"ts":"2024-01-15T10:00:04Z"}
{"level":"info","msg":"request handled","method":"POST","path":"/api/users","status":201,"duration_ms":45,"ts":"2024-01-15T10:00:05Z"}
{"level":"debug","msg":"cache hit","key":"user:123","ttl_s":300,"ts":"2024-01-15T10:00:06Z"}
{"level":"error","msg":"failed to send notification","service":"email","error":"connection refused","ts":"2024-01-15T10:00:07Z"}
{"level":"fatal","msg":"unrecoverable error","component":"database","error":"disk full","ts":"2024-01-15T10:00:08Z"}
`
	os.WriteFile("app.log", []byte(appLog), 0644)

	// Create error.log with common format
	errorLog := `2024-01-15 10:00:00 [INFO] Application starting up
2024-01-15 10:00:01 [INFO] Loading configuration from /etc/app/config.yml
2024-01-15 10:00:02 [WARN] Configuration file not found, using defaults
2024-01-15 10:00:03 [INFO] Database connection established
2024-01-15 10:00:04 [ERROR] Failed to connect to cache server: connection refused
2024-01-15 10:00:05 [INFO] Running in degraded mode (no cache)
2024-01-15 10:00:06 [ERROR] Request timeout for /api/reports: 30s exceeded
2024-01-15 10:00:07 [WARN] Memory usage high: 85% of heap
2024-01-15 10:00:08 [INFO] Garbage collection completed: freed 512MB
2024-01-15 10:00:09 [ERROR] Disk space critical: /var/log at 95% capacity
2024-01-15 10:00:10 [FATAL] Out of memory: cannot allocate 1GB
`
	os.WriteFile("error.log", []byte(errorLog), 0644)

	fmt.Println("  Created app.log (JSON format)")
	fmt.Println("  Created error.log (common format)")
}

// collectFromFiles reads logs from the given files.
func collectFromFiles(paths []string) []collector.RawLog {
	var allLogs []collector.RawLog
	for _, path := range paths {
		file, err := os.Open(path)
		if err != nil {
			log.Printf("Warning: could not open %s: %v", path, err)
			continue
		}
		logs := collector.CollectFromReader(file, filepath.Base(path))
		allLogs = append(allLogs, logs...)
		file.Close()
	}
	return allLogs
}

// parseAndDisplay parses logs with the given format and displays them.
func parseAndDisplay(logs []collector.RawLog, format parser.Format) {
	p := parser.New(format)
	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			fmt.Printf("  [PARSE ERROR] %s: %v\n", raw.Source, err)
			continue
		}
		displayEntry(entry)
	}
}

// parseAndDisplayFormat parses logs with a specific format.
func parseAndDisplayFormat(logs []collector.RawLog, format parser.Format) {
	p := parser.New(format)
	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			fmt.Printf("  [PARSE ERROR] %s: %v\n", raw.Source, err)
			continue
		}
		displayEntry(entry)
	}
}

// displayEntry prints a parsed log entry.
func displayEntry(entry *parser.Entry) {
	ts := entry.Timestamp.Format("2006-01-02 15:04:05")
	if entry.Timestamp.IsZero() {
		ts = "----/--/-- --:--:--"
	}
	fmt.Printf("  [%s] %-5s [%s:%d] %s", ts, entry.Level.String(), entry.Source, entry.LineNum, entry.Message)
	if len(entry.Fields) > 0 {
		fmt.Print(" |")
		for k, v := range entry.Fields {
			fmt.Printf(" %s=%s", k, v)
		}
	}
	fmt.Println()
}

// storeEntries parses logs, stores them, and returns stats.
func storeEntries(logs []collector.RawLog) (*storage.Storage, storage.Stats) {
	store := storage.New()
	p := parser.New(parser.FormatAuto)

	for _, raw := range logs {
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err != nil {
			continue
		}
		// Convert parser.Level to storage.Level
		var lvl storage.Level
		switch entry.Level {
		case parser.LevelDebug:
			lvl = storage.LevelDebug
		case parser.LevelInfo:
			lvl = storage.LevelInfo
		case parser.LevelWarn:
			lvl = storage.LevelWarn
		case parser.LevelError:
			lvl = storage.LevelError
		case parser.LevelFatal:
			lvl = storage.LevelFatal
		default:
			lvl = storage.LevelUnknown
		}

		storageEntry := storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     lvl,
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		}
		store.Store(storageEntry)
	}

	return store, store.Stats()
}

// queryExamples demonstrates various query operations.
func queryExamples(store *storage.Storage) {
	// Query all entries
	all := store.Query(storage.Query{Limit: 0})
	fmt.Printf("  Total entries: %d\n", len(all))

	// Query by level
	errors := store.Query(storage.Query{Level: storage.PtrLevel(storage.LevelError), Limit: 0})
	fmt.Printf("  Error entries: %d\n", len(errors))

	// Query by source
	appLogs := store.Query(storage.Query{Source: "app.log", Limit: 0})
	fmt.Printf("  App log entries: %d\n", len(appLogs))

	// Query by message search
	timeoutLogs := store.Query(storage.Query{Message: "timeout", Limit: 0})
	fmt.Printf("  Entries with 'timeout': %d\n", len(timeoutLogs))

	// Query recent entries
	recent := store.Query(storage.Query{Limit: 3, Reverse: true})
	fmt.Printf("  Most recent %d entries:\n", len(recent))
	for _, e := range recent {
		fmt.Printf("    - %s: %s\n", e.Level.String(), e.Message)
	}

	// Query with time range
	start := time.Date(2024, 1, 15, 10, 0, 3, 0, time.UTC)
	end := time.Date(2024, 1, 15, 10, 0, 6, 0, time.UTC)
	timeRange := store.Query(storage.Query{StartTime: &start, EndTime: &end, Limit: 0})
	fmt.Printf("  Entries in time range [%s, %s]: %d\n",
		start.Format("15:04:05"), end.Format("15:04:05"), len(timeRange))
}

// filterExamples demonstrates various filtering operations.
func filterExamples(logs []collector.RawLog) {
	// Create filter chain: ERROR level + contains "timeout"
	chain := filter.NewChain(
		&filter.LevelFilter{MinLevel: filter.LevelError},
		&filter.KeywordFilter{Keyword: "timeout", CaseSensitive: false},
	)

	// Convert to filter entries
	var filterEntries []filter.Entry
	for _, raw := range logs {
		fe := filter.Entry{
			Level:   filter.LevelError,
			Message: raw.Line,
			Source:  raw.Source,
			Fields:  make(map[string]string),
		}
		// Try to parse level from the line
		p := parser.New(parser.FormatAuto)
		entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
		if err == nil {
			switch entry.Level {
			case parser.LevelDebug:
				fe.Level = filter.LevelDebug
			case parser.LevelInfo:
				fe.Level = filter.LevelInfo
			case parser.LevelWarn:
				fe.Level = filter.LevelWarn
			case parser.LevelError:
				fe.Level = filter.LevelError
			case parser.LevelFatal:
				fe.Level = filter.LevelFatal
			}
			fe.Fields = entry.Fields
		}
		filterEntries = append(filterEntries, fe)
	}

	// Apply filter
	matched := filter.Apply(filterEntries, chain)
	fmt.Printf("  Filter: level >= ERROR AND contains 'timeout'\n")
	fmt.Printf("  Matched %d entries\n", len(matched))
	for _, e := range matched {
		fmt.Printf("    - %s\n", e.Message)
	}

	// Level-only filter
	levelFilter := &filter.LevelFilter{MinLevel: filter.LevelWarn}
	warnAndAbove := filter.Apply(filterEntries, levelFilter)
	fmt.Printf("\n  Filter: level >= WARN\n")
	fmt.Printf("  Matched %d entries\n", len(warnAndAbove))
}

// multilineExample demonstrates multi-line log handling.
func multilineExample() {
	fmt.Println("  Multi-line log handling (stack traces):")

	cfg := multiline.DefaultConfig()
	assembler := multiline.NewAssembler(cfg)

	// Simulate a Go stack trace
	stackTrace := []string{
		"2024-01-15 10:00:00 [ERROR] panic: runtime error",
		"goroutine 1 [running]:",
		"main.main()",
		"  at /app/main.go:42",
		"  goroutine 2 [IO wait]:",
		"  net.(*netFD).Read()",
		"    at /usr/local/go/src/net/fd_posix.go:55",
		"  --- end goroutine 2",
		"2024-01-15 10:00:01 [INFO] recovery completed",
	}

	for i, line := range stackTrace {
		isChunk := assembler.Feed(line, i+1)
		if isChunk {
			fmt.Printf("    [CHUNK] %s\n", assembler.Done())
		}
	}
	assembler.Flush()

	// Simulate JSON block
	fmt.Println("\n  JSON block handling:")
	jsonLines := []string{
		`2024-01-15 10:00:00 [INFO] request received`,
		`  {`,
		`    "method": "POST",`,
		`    "path": "/api/users",`,
		`    "body": {"name": "John", "email": "john@example.com"}`,
		`  }`,
		`2024-01-15 10:00:01 [INFO] response sent`,
	}

	jsonAssembler := multiline.NewFlushableChunker(multiline.DefaultConfig())
	for i, line := range jsonLines {
		jsonAssembler.Feed(line, i+1)
	}
	jsonAssembler.FlushAndReset()

	fmt.Println("  (Chunks sent to Done() channel for processing)")
}

// forwarderExample demonstrates forwarder concepts.
func forwarderExample() {
	fmt.Println("  Forwarder concepts:")
	fmt.Println("  - Batching: Collect entries into batches for efficiency")
	fmt.Println("  - Retry: Exponential backoff for failed sends")
	fmt.Println("  - Backpressure: Slow down when buffer is near capacity")

	// Demonstrate batch size calculation
	entries := []forwarder.Entry{
		{Raw: "test log line 1", Message: "test message 1", Source: "app"},
		{Raw: "test log line 2", Message: "test message 2", Source: "app", Fields: map[string]string{"key": "value"}},
		{Raw: "test log line 3", Message: "test message 3", Source: "worker"},
	}
	size := forwarder.CalculateBatchSize(entries)
	fmt.Printf("  Batch size for %d entries: %d bytes\n", len(entries), size)

	// Demonstrate backpressure monitoring
	bm := forwarder.NewBackpressureMonitor(1000)
	fmt.Println("  Backpressure monitoring:")
	fmt.Printf("    At 500/1000: ratio=%.2f, backpressured=%v\n",
		bm.GetBackpressureRatio(), bm.Check(500))
	fmt.Printf("    At 850/1000: ratio=%.2f, backpressured=%v\n",
		bm.GetBackpressureRatio(), bm.Check(850))
	fmt.Printf("    At 950/1000: ratio=%.2f, backpressured=%v\n",
		bm.GetBackpressureRatio(), bm.Check(950))

	// Demonstrate exponential backoff
	eb := forwarder.NewExponentialBackoff(100*time.Millisecond, 10*time.Second, 2.0)
	fmt.Println("  Exponential backoff:")
	for i := 0; i < 5; i++ {
		fmt.Printf("    Retry %d: %v\n", i, eb.NextInterval(i))
	}

	// Demo file writer
	fmt.Println("\n  FileWriter demo:")
	fw, err := transport.NewFileWriter(transport.FileWriterConfig{
		Path:    "demo_output.log",
		MaxSize: 1024 * 10, // 10KB for demo
	})
	if err != nil {
		log.Printf("  Warning: could not create file writer: %v", err)
		return
	}
	fw.WriteEntry(time.Now(), "INFO", "demo", "This is a demo log entry")
	fw.WriteEntry(time.Now(), "WARN", "demo", "This is a demo warning")
	fw.WriteEntry(time.Now(), "ERROR", "demo", "This is a demo error")
	fw.Close()
	fmt.Println("  Wrote 3 entries to demo_output.log")
}
