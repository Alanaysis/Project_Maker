// Log parsing and filtering example.
//
// This example demonstrates:
// 1. Parsing multiple log formats (JSON, logfmt, common, regex)
// 2. Filtering by level, keyword, and regex
// 3. Combining filters
// 4. Handling multi-line logs (stack traces, JSON blocks)
//
// Run: go run examples/parsing_filtering.go

package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/project/log-collector/internal/filter"
	"github.com/project/log-collector/internal/multiline"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/storage"
)

func main() {
	fmt.Println("=== Log Collector - Parsing & Filtering Example ===")
	fmt.Println()

	// Step 1: Parse JSON logs
	fmt.Println("Step 1: JSON Log Parsing")
	parseJSONExample()
	fmt.Println()

	// Step 2: Parse logfmt logs
	fmt.Println("Step 2: Logfmt Log Parsing")
	parseLogfmtExample()
	fmt.Println()

	// Step 3: Parse common format logs
	fmt.Println("Step 3: Common Format Log Parsing")
	parseCommonExample()
	fmt.Println()

	// Step 4: Parse with custom regex
	fmt.Println("Step 4: Custom Regex Parsing")
	parseRegexExample()
	fmt.Println()

	// Step 5: Auto-detection
	fmt.Println("Step 5: Auto-Detection")
	autoDetectExample()
	fmt.Println()

	// Step 6: Filtering by level
	fmt.Println("Step 6: Level Filtering")
	levelFilterExample()
	fmt.Println()

	// Step 7: Filtering by keyword
	fmt.Println("Step 7: Keyword Filtering")
	keywordFilterExample()
	fmt.Println()

	// Step 8: Filtering by regex
	fmt.Println("Step 8: Regex Filtering")
	regexFilterExample()
	fmt.Println()

	// Step 9: Combined filtering
	fmt.Println("Step 9: Combined Filtering")
	combinedFilterExample()
	fmt.Println()

	// Step 10: Multi-line handling
	fmt.Println("Step 10: Multi-line Handling")
	multilineExample()
	fmt.Println()

	// Step 11: Storage and query
	fmt.Println("Step 11: Storage and Query")
	storageExample()
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}

// parseJSONExample demonstrates JSON log parsing.
func parseJSONExample() {
	jsonLines := []string{
		`{"level":"info","msg":"server started","port":8080,"ts":"2024-01-15T10:00:00Z"}`,
		`{"level":"error","msg":"connection timeout","host":"db.example.com","timeout_ms":30000}`,
		`{"level":"warn","msg":"slow query","table":"users","duration_ms":500}`,
		`{"level":"debug","msg":"cache hit","key":"user:123"}`,
		`{"level":"fatal","msg":"disk full","component":"storage"}`,
	}

	p := parser.New(parser.FormatJSON)
	fmt.Println("  Input (JSON) -> Parsed Entry:")
	for i, line := range jsonLines {
		entry, err := p.Parse(line, "app.log", i+1)
		if err != nil {
			fmt.Printf("    [%d] ERROR: %v\n", i+1, err)
			continue
		}
		fmt.Printf("    [%d] Level: %-5s | Message: %s\n", i+1, entry.Level.String(), entry.Message)
		fmt.Printf("         Fields: %v\n", entry.Fields)
	}
}

// parseLogfmtExample demonstrates logfmt parsing.
func parseLogfmtExample() {
	logfmtLines := []string{
		`level=info msg="server started" port=8080 ts=2024-01-15T10:00:00Z`,
		`level=error msg="connection timeout" host=db.example.com timeout_ms=30000`,
		`level=warn msg="slow query" table=users duration_ms=500`,
		`level=debug msg="cache hit" key="user:123"`,
	}

	p := parser.New(parser.FormatLogfmt)
	fmt.Println("  Input (logfmt) -> Parsed Entry:")
	for i, line := range logfmtLines {
		entry, err := p.Parse(line, "app.log", i+1)
		if err != nil {
			fmt.Printf("    [%d] ERROR: %v\n", i+1, err)
			continue
		}
		fmt.Printf("    [%d] Level: %-5s | Message: %s\n", i+1, entry.Level.String(), entry.Message)
		fmt.Printf("         Fields: %v\n", entry.Fields)
	}
}

// parseCommonExample demonstrates common format parsing.
func parseCommonExample() {
	commonLines := []string{
		`2024-01-15 10:00:00 [INFO] Application started successfully`,
		`2024-01-15 10:00:01 [ERROR] Failed to connect to database`,
		`2024-01-15 10:00:02 [WARN] Memory usage high: 85%`,
		`2024-01-15 10:00:03 [DEBUG] Processing request #12345`,
		`2024-01-15 10:00:04 [FATAL] Unrecoverable error in worker`,
	}

	p := parser.New(parser.FormatCommon)
	fmt.Println("  Input (common) -> Parsed Entry:")
	for i, line := range commonLines {
		entry, err := p.Parse(line, "error.log", i+1)
		if err != nil {
			fmt.Printf("    [%d] ERROR: %v\n", i+1, err)
			continue
		}
		fmt.Printf("    [%d] Level: %-5s | Message: %s\n", i+1, entry.Level.String(), entry.Message)
	}
}

// parseRegexExample demonstrates custom regex parsing.
func parseRegexExample() {
	// Create a regex parser for Apache-style logs
	p, err := parser.NewWithRegex(`^(?P<remote>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\d+)`)
	if err != nil {
		fmt.Printf("  Failed to create regex parser: %v\n", err)
		return
	}

	apacheLines := []string{
		`192.168.1.100 - - [15/Jan/2024:10:00:00 +0000] "GET /api/users HTTP/1.1" 200 1234`,
		`10.0.0.50 - - [15/Jan/2024:10:00:01 +0000] "POST /api/login HTTP/1.1" 401 567`,
		`172.16.0.1 - - [15/Jan/2024:10:00:02 +0000] "GET /static/style.css HTTP/1.1" 304 0`,
	}

	fmt.Println("  Input (Apache) -> Parsed Entry:")
	for i, line := range apacheLines {
		entry, err := p.Parse(line, "access.log", i+1)
		if err != nil {
			fmt.Printf("    [%d] ERROR: %v\n", i+1, err)
			continue
		}
		fmt.Printf("    [%d] Level: %-5s | Message: %s\n", i+1, entry.Level.String(), entry.Message)
		fmt.Printf("         Fields: %v\n", entry.Fields)
	}

	// Show common patterns
	fmt.Println("\n  Built-in common patterns:")
	for name, pattern := range parser.CommonPatterns {
		fmt.Printf("    %-10s: %s\n", name, pattern[:60]+"...")
	}
}

// autoDetectExample demonstrates auto-detection of log formats.
func autoDetectExample() {
	mixedLines := []string{
		`{"level":"info","msg":"JSON format","ts":"2024-01-15T10:00:00Z"}`,
		`level=warn msg="logfmt format" duration_ms=500`,
		`2024-01-15 10:00:02 [ERROR] Common format message`,
		`This is an unrecognized format line`,
	}

	p := parser.New(parser.FormatAuto)
	fmt.Println("  Auto-detection results:")
	for i, line := range mixedLines {
		entry, err := p.Parse(line, "mixed.log", i+1)
		if err != nil {
			fmt.Printf("    [%d] ERROR: %v\n", i+1, err)
			continue
		}
		fmt.Printf("    [%d] Level: %-5s | Message: %s\n", i+1, entry.Level.String(), entry.Message)
		if len(entry.Fields) > 0 {
			fmt.Printf("         Fields: %v\n", entry.Fields)
		}
	}
}

// levelFilterExample demonstrates level-based filtering.
func levelFilterExample() {
	sampleEntries := createSampleFilterEntries()

	fmt.Println("  Original entries:")
	for i, e := range sampleEntries {
		fmt.Printf("    [%d] %-5s: %s\n", i+1, e.Level.String(), e.Message)
	}

	// Filter by minimum level
	filters := []struct {
		name   string
		filter filter.Filter
	}{
		{"level >= DEBUG", &filter.LevelFilter{MinLevel: filter.LevelDebug}},
		{"level >= INFO", &filter.LevelFilter{MinLevel: filter.LevelInfo}},
		{"level >= WARN", &filter.LevelFilter{MinLevel: filter.LevelWarn}},
		{"level >= ERROR", &filter.LevelFilter{MinLevel: filter.LevelError}},
		{"level >= FATAL", &filter.LevelFilter{MinLevel: filter.LevelFatal}},
	}

	for _, f := range filters {
		matched := filter.Apply(sampleEntries, f.filter)
		fmt.Printf("\n  Filter: %s -> %d matched\n", f.name, len(matched))
		for _, e := range matched {
			fmt.Printf("    %s: %s\n", e.Level.String(), e.Message)
		}
	}
}

// keywordFilterExample demonstrates keyword-based filtering.
func keywordFilterExample() {
	sampleEntries := createSampleFilterEntries()

	fmt.Println("  Original entries:")
	for i, e := range sampleEntries {
		fmt.Printf("    [%d] %-5s: %s\n", i+1, e.Level.String(), e.Message)
	}

	// Keyword filters
	filters := []struct {
		name   string
		filter filter.Filter
	}{
		{"contains 'timeout'", &filter.KeywordFilter{Keyword: "timeout", CaseSensitive: false}},
		{"contains 'timeout' (case-sensitive)", &filter.KeywordFilter{Keyword: "timeout", CaseSensitive: true}},
		{"excludes 'cache'", &filter.KeywordFilter{Keyword: "cache", CaseSensitive: false, Exclude: true}},
	}

	for _, f := range filters {
		matched := filter.Apply(sampleEntries, f.filter)
		fmt.Printf("\n  Filter: %s -> %d matched\n", f.name, len(matched))
		for _, e := range matched {
			fmt.Printf("    %s: %s\n", e.Level.String(), e.Message)
		}
	}
}

// regexFilterExample demonstrates regex-based filtering.
func regexFilterExample() {
	sampleEntries := createSampleFilterEntries()

	fmt.Println("  Original entries:")
	for i, e := range sampleEntries {
		fmt.Printf("    [%d] %-5s: %s\n", i+1, e.Level.String(), e.Message)
	}

	// Regex filters
	filters := []struct {
		name   string
		filter filter.Filter
	}{
		{"matches '\\d{3}'", &filter.RegexFilter{Pattern: mustCompile(`\d{3}`)}},
		{"excludes '\\d{3}'", &filter.RegexFilter{Pattern: mustCompile(`\d{3}`), Exclude: true}},
		{"matches 'error|timeout|fail'", &filter.RegexFilter{Pattern: mustCompile(`(?i)error|timeout|fail`)}},
	}

	for _, f := range filters {
		matched := filter.Apply(sampleEntries, f.filter)
		fmt.Printf("\n  Filter: %s -> %d matched\n", f.name, len(matched))
		for _, e := range matched {
			fmt.Printf("    %s: %s\n", e.Level.String(), e.Message)
		}
	}
}

// combinedFilterExample demonstrates combining multiple filters.
func combinedFilterExample() {
	sampleEntries := createSampleFilterEntries()

	fmt.Println("  Original entries:")
	for i, e := range sampleEntries {
		fmt.Printf("    [%d] %-5s: %s\n", i+1, e.Level.String(), e.Message)
	}

	// Chain filter (AND logic)
	chain := filter.NewChain(
		&filter.LevelFilter{MinLevel: filter.LevelWarn},
		&filter.KeywordFilter{Keyword: "timeout", CaseSensitive: false},
	)
	matched := filter.Apply(sampleEntries, chain)
	fmt.Printf("\n  Chain (level >= WARN AND contains 'timeout'): %d matched\n", len(matched))
	for _, e := range matched {
		fmt.Printf("    %s: %s\n", e.Level.String(), e.Message)
	}

	// MatchAny filter (OR logic)
	matchAny := &filter.MatchAny{
		Filters: []filter.Filter{
			&filter.KeywordFilter{Keyword: "timeout", CaseSensitive: false},
			&filter.KeywordFilter{Keyword: "disk", CaseSensitive: false},
		},
	}
	matchedAny := filter.Apply(sampleEntries, matchAny)
	fmt.Printf("\n  MatchAny (contains 'timeout' OR contains 'disk'): %d matched\n", len(matchedAny))
	for _, e := range matchedAny {
		fmt.Printf("    %s: %s\n", e.Level.String(), e.Message)
	}
}

// multilineExample demonstrates multi-line log handling.
func multilineExample() {
	fmt.Println("  Stack trace assembly:")

	cfg := multiline.DefaultConfig()
	assembler := multiline.NewAssembler(cfg)

	// Simulate a Go stack trace
	lines := []string{
		`2024-01-15 10:00:00 [ERROR] panic: runtime error`,
		`goroutine 1 [running]:`,
		`main.main()`,
		`  at /app/main.go:42`,
		`  goroutine 2 [IO wait]:`,
		`  net.(*netFD).Read()`,
		`    at /usr/local/go/src/net/fd_posix.go:55`,
		`  goroutine 3 [sleep]:`,
		`  time.Sleep()`,
		`    at /usr/local/go/src/time/sleep.go:180`,
		`2024-01-15 10:00:01 [INFO] recovery completed`,
	}

	chunkCount := 0
	for i, line := range lines {
		assembler.Feed(line, i+1)
	}
	assembler.Flush()

	// Read chunks from the done channel
	for chunk := range assembler.Done():
		chunkCount++
		fmt.Printf("  Chunk %d (%d lines):\n", chunkCount, chunk.LineCount)
		for j, l := range chunk.Lines {
			fmt.Printf("    Line %d: %s\n", j+1, l)
		}
	}

	fmt.Printf("\n  Total chunks assembled: %d\n", chunkCount)
}

// storageExample demonstrates storage and querying.
func storageExample() {
	store := storage.New()
	p := parser.New(parser.FormatAuto)

	// Parse and store sample entries
	rawLines := []string{
		`{"level":"info","msg":"server started","port":8080}`,
		`{"level":"error","msg":"connection timeout","host":"db.example.com"}`,
		`{"level":"warn","msg":"slow query","table":"users","duration_ms":500}`,
		`{"level":"info","msg":"request handled","method":"GET","path":"/api/users"}`,
		`{"level":"error","msg":"disk full","component":"storage"}`,
		`2024-01-15 10:00:05 [INFO] Application started successfully`,
		`2024-01-15 10:00:06 [ERROR] Failed to connect to cache`,
	}

	for i, line := range rawLines {
		entry, err := p.Parse(line, "test.log", i+1)
		if err != nil {
			continue
		}
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
		store.Store(storage.Entry{
			Timestamp: entry.Timestamp,
			Level:     lvl,
			Message:   entry.Message,
			Fields:    entry.Fields,
			Source:    entry.Source,
			LineNum:   entry.LineNum,
			Raw:       entry.Raw,
		})
	}

	fmt.Printf("  Stored %d entries\n", store.Count())

	// Query examples
	fmt.Println("\n  Query results:")

	// All entries
	all := store.Query(storage.Query{Limit: 0})
	fmt.Printf("  All entries: %d\n", len(all))

	// By level
	errors := store.Query(storage.Query{Level: storage.PtrLevel(storage.LevelError), Limit: 0})
	fmt.Printf("  Errors: %d\n", len(errors))
	for _, e := range errors {
		fmt.Printf("    - %s\n", e.Message)
	}

	// By source
	testLogs := store.Query(storage.Query{Source: "test.log", Limit: 0})
	fmt.Printf("  From test.log: %d\n", len(testLogs))

	// By message
	timeoutLogs := store.Query(storage.Query{Message: "timeout", Limit: 0})
	fmt.Printf("  Contains 'timeout': %d\n", len(timeoutLogs))
	for _, e := range timeoutLogs {
		fmt.Printf("    - %s\n", e.Message)
	}

	// Recent entries
	recent := store.Query(storage.Query{Limit: 3, Reverse: true})
	fmt.Printf("  Recent 3: %d\n", len(recent))
	for _, e := range recent {
		fmt.Printf("    - %s: %s\n", e.Level.String(), e.Message)
	}

	// Stats
	stats := store.Stats()
	fmt.Printf("\n  Storage stats:\n")
	fmt.Printf("    Total: %d\n", stats.TotalEntries)
	fmt.Printf("    Levels: %v\n", stats.LevelCounts)
	fmt.Printf("    Sources: %v\n", stats.SourceCounts)
}

// createSampleFilterEntries creates sample entries for filtering demos.
func createSampleFilterEntries() []filter.Entry {
	return []filter.Entry{
		{Level: filter.LevelInfo, Message: "Server started on port 8080", Fields: map[string]string{"port": "8080"}},
		{Level: filter.LevelInfo, Message: "Cache initialized successfully", Fields: map[string]string{"size": "1024"}},
		{Level: filter.LevelWarn, Message: "Slow query detected: 500ms", Fields: map[string]string{"table": "users"}},
		{Level: filter.LevelError, Message: "Connection timeout to db.example.com", Fields: map[string]string{"host": "db.example.com"}},
		{Level: filter.LevelError, Message: "Disk space critical: 95% used", Fields: map[string]string{"disk": "/var/log"}},
		{Level: filter.LevelFatal, Message: "Out of memory: cannot allocate 1GB", Fields: map[string]string{"heap": "4294967296"}},
		{Level: filter.LevelDebug, Message: "Cache hit for key: user:123", Fields: map[string]string{"key": "user:123"}},
		{Level: filter.LevelWarn, Message: "Memory usage high: 85% of heap", Fields: map[string]string{"pct": "85"}},
	}
}

// mustCompile compiles a regex or panics.
func mustCompile(s string) *filter.RegexFilter {
	f, err := filter.NewRegexFilter(s, false)
	if err != nil {
		panic(err)
	}
	return f
}

// Ensure strings import is used
var _ = strings.Contains

func init() {
	// Ensure os import is used
	_ = os.Stdout
}
