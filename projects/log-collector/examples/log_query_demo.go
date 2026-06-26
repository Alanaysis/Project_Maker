// Log query demo example.
//
// This example demonstrates the query engine capabilities:
// 1. Basic queries (search, by level, by time range)
// 2. Advanced queries (combined filters)
// 3. Storage statistics
// 4. Output formatting
//
// Run: go run examples/log_query_demo.go

package main

import (
	"fmt"
	"strings"
	"time"

	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/storage"
	"github.com/project/log-collector/internal/query"
)

func main() {
	fmt.Println("=== Log Collector - Query Demo ===")
	fmt.Println()

	// Create storage and populate with sample data
	store, entries := createSampleData()

	fmt.Printf("Created storage with %d entries\n", store.Count())
	fmt.Println()

	// Demo 1: Basic queries
	fmt.Println("=== Demo 1: Basic Queries ===")
	demoBasicQueries(store)
	fmt.Println()

	// Demo 2: Advanced queries
	fmt.Println("=== Demo 2: Advanced Queries ===")
	demoAdvancedQueries(store)
	fmt.Println()

	// Demo 3: Query engine
	fmt.Println("=== Demo 3: Query Engine ===")
	demoQueryEngine(store)
	fmt.Println()

	// Demo 4: Storage statistics
	fmt.Println("=== Demo 4: Storage Statistics ===")
	demoStats(store)
	fmt.Println()

	// Demo 5: Output formatting
	fmt.Println("=== Demo 5: Output Formatting ===")
	demoFormatting(store)
	fmt.Println()

	fmt.Println("=== Demo Complete ===")
}

// createSampleData populates storage with realistic log data.
func createSampleData() (*storage.Storage, []storage.Entry) {
	store := storage.New()
	var stored []storage.Entry

	now := time.Date(2024, 1, 15, 10, 0, 0, 0, time.UTC)
	samples := []struct {
		level   storage.Level
		message string
		fields  map[string]string
		source  string
	}{
		{storage.LevelInfo, "Application starting up", map[string]string{"version": "1.2.3"}, "app"},
		{storage.LevelInfo, "Loading configuration", map[string]string{"path": "/etc/app/config.yml"}, "app"},
		{storage.LevelWarn, "Configuration file not found, using defaults", nil, "app"},
		{storage.LevelInfo, "Database connection established", map[string]string{"host": "db.example.com", "port": "5432"}, "app"},
		{storage.LevelInfo, "Cache initialized", map[string]string{"size": "1024", "ttl": "300"}, "app"},
		{storage.LevelInfo, "Server listening on :8080", map[string]string{"port": "8080", "proto": "http"}, "app"},
		{storage.LevelDebug, "Processing request #1001", map[string]string{"method": "GET", "path": "/api/users"}, "app"},
		{storage.LevelInfo, "Request handled", map[string]string{"method": "GET", "path": "/api/users", "status": "200", "duration_ms": "15"}, "app"},
		{storage.LevelDebug, "Cache hit", map[string]string{"key": "user:123", "ttl_s": "300"}, "cache"},
		{storage.LevelInfo, "Request handled", map[string]string{"method": "POST", "path": "/api/users", "status": "201", "duration_ms": "45"}, "app"},
		{storage.LevelWarn, "Slow query detected", map[string]string{"table": "users", "duration_ms": "500"}, "db"},
		{storage.LevelInfo, "Request handled", map[string]string{"method": "GET", "path": "/api/health", "status": "200", "duration_ms": "2"}, "app"},
		{storage.LevelError, "Connection timeout", map[string]string{"host": "redis.example.com", "timeout_ms": "30000"}, "cache"},
		{storage.LevelWarn, "Memory usage high", map[string]string{"pct": "85", "heap_bytes": "1073741824"}, "app"},
		{storage.LevelInfo, "Garbage collection completed", map[string]string{"freed_mb": "512", "duration_ms": "150"}, "app"},
		{storage.LevelError, "Failed to send notification", map[string]string{"service": "email", "error": "connection refused"}, "notification"},
		{storage.LevelInfo, "Request handled", map[string]string{"method": "GET", "path": "/api/reports", "status": "200", "duration_ms": "250"}, "app"},
		{storage.LevelWarn, "Disk space critical", map[string]string{"disk": "/var/log", "pct": "95"}, "system"},
		{storage.LevelError, "Request timeout", map[string]string{"path": "/api/reports", "timeout_ms": "30000"}, "app"},
		{storage.LevelFatal, "Out of memory", map[string]string{"heap_bytes": "4294967296", "limit": "4294967296"}, "app"},
	}

	for i, s := range samples {
		entry := storage.Entry{
			Timestamp: now.Add(time.Duration(i) * time.Minute),
			Level:     s.level,
			Message:   s.message,
			Fields:    s.fields,
			Source:    s.source,
			LineNum:   i + 1,
			Raw:       fmt.Sprintf("%s %s", s.level.String(), s.message),
		}
		store.Store(entry)
		stored = append(stored, entry)
	}

	return store, stored
}

// demoBasicQueries demonstrates basic query operations.
func demoBasicQueries(store *storage.Storage) {
	// All entries
	all := store.Query(storage.Query{Limit: 0})
	fmt.Printf("1. All entries: %d\n", len(all))

	// Recent entries
	recent := store.Query(storage.Query{Limit: 5, Reverse: true})
	fmt.Printf("\n2. Recent 5 entries:\n")
	for _, e := range recent {
		ts := e.Timestamp.Format("15:04:05")
		fmt.Printf("   %s %-5s [%s] %s\n", ts, e.Level.String(), e.Source, e.Message)
	}

	// By level
	errors := store.Query(storage.Query{Level: storage.PtrLevel(storage.LevelError), Limit: 0})
	fmt.Printf("\n3. Error entries (%d):\n", len(errors))
	for _, e := range errors {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// By message
	timeout := store.Query(storage.Query{Message: "timeout", Limit: 0})
	fmt.Printf("\n4. Entries containing 'timeout' (%d):\n", len(timeout))
	for _, e := range timeout {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// Time range
	start := time.Date(2024, 1, 15, 10, 5, 0, 0, time.UTC)
	end := time.Date(2024, 1, 15, 10, 15, 0, 0, time.UTC)
	timeRange := store.Query(storage.Query{StartTime: &start, EndTime: &end, Limit: 0})
	fmt.Printf("\n5. Entries in time range [%s, %s] (%d):\n",
		start.Format("15:04:05"), end.Format("15:04:05"), len(timeRange))
	for _, e := range timeRange {
		fmt.Printf("   %s [%s] %s\n", e.Timestamp.Format("15:04:05"), e.Source, e.Message)
	}

	// By source
	appEntries := store.Query(storage.Query{Source: "app", Limit: 0})
	fmt.Printf("\n6. Entries from 'app' source (%d):\n", len(appEntries))
	for _, e := range appEntries {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}
}

// demoAdvancedQueries demonstrates advanced query operations.
func demoAdvancedQueries(store *storage.Storage) {
	// Multiple levels
	levels := []storage.Level{storage.LevelError, storage.LevelFatal}
	queries := storage.Query{Levels: levels, Limit: 0}
	critical := store.Query(queries)
	fmt.Printf("1. Critical entries (ERROR+FATAL) (%d):\n", len(critical))
	for _, e := range critical {
		fmt.Printf("   [%s] %s\n", e.Level.String(), e.Message)
	}

	// With message filter
	warnMsg := store.Query(storage.Query{
		Message: "slow",
		Limit:   0,
	})
	fmt.Printf("\n2. Entries containing 'slow' (%d):\n", len(warnMsg))
	for _, e := range warnMsg {
		fmt.Printf("   [%s] %s\n", e.Level.String(), e.Message)
	}

	// With offset
	paginated := store.Query(storage.Query{
		Limit:  3,
		Offset: 3,
		Reverse: true,
	})
	fmt.Printf("\n3. Paginated results (skip 3, limit 3):\n")
	for _, e := range paginated {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// Reverse order
	reversed := store.Query(storage.Query{
		Limit:   5,
		Reverse: true,
	})
	fmt.Printf("\n4. Recent 5 (reverse order):\n")
	for _, e := range reversed {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// By field
	cacheEntries := store.Query(storage.Query{
		Fields: map[string]string{"key": "user:123"},
		Limit:  0,
	})
	fmt.Printf("\n5. Entries with field key=user:123 (%d):\n", len(cacheEntries))
	for _, e := range cacheEntries {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}
}

// demoQueryEngine demonstrates the query engine.
func demoQueryEngine(store *storage.Storage) {
	engine := query.NewEngine(store)

	// Search
	fmt.Println("1. Search 'timeout':")
	results := engine.Search("timeout", 10)
	for _, e := range results {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// By level
	fmt.Println("\n2. By level (ERROR):")
	results = engine.ByLevel(storage.LevelError, 10)
	for _, e := range results {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// Recent
	fmt.Println("\n3. Recent 3:")
	results = engine.Recent(3)
	for _, e := range results {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// Errors
	fmt.Println("\n4. Recent errors:")
	results = engine.Errors(5)
	for _, e := range results {
		fmt.Printf("   [%s] %s\n", e.Source, e.Message)
	}

	// Advanced query
	fmt.Println("\n5. Advanced query 'level:WARN message:slow':")
	advancedResults, err := engine.AdvancedQuery("level:WARN message:slow")
	if err != nil {
		fmt.Printf("   Error: %v\n", err)
	} else {
		for _, e := range advancedResults {
			fmt.Printf("   [%s] %s\n", e.Source, e.Message)
		}
	}

	// Time range query
	fmt.Println("\n6. Time range query 'after:2024-01-15 before:2024-01-16':")
	advancedResults, err = engine.AdvancedQuery("after:2024-01-15 before:2024-01-16 limit:5")
	if err != nil {
		fmt.Printf("   Error: %v\n", err)
	} else {
		for _, e := range advancedResults {
			fmt.Printf("   [%s] %s\n", e.Source, e.Message)
		}
	}
}

// demoStats demonstrates storage statistics.
func demoStats(store *storage.Storage) {
	stats := store.Stats()
	fmt.Printf("Total entries: %d\n", stats.TotalEntries)
	fmt.Printf("\nLevel distribution:\n")
	for lvl, count := range stats.LevelCounts {
		fmt.Printf("  %-7s: %d\n", lvl, count)
	}
	fmt.Printf("\nSource distribution:\n")
	for src, count := range stats.SourceCounts {
		fmt.Printf("  %-10s: %d\n", src, count)
	}
	if !stats.OldestEntry.IsZero() {
		fmt.Printf("\nTime range: %s to %s\n",
			stats.OldestEntry.Format("2006-01-02 15:04:05"),
			stats.NewestEntry.Format("2006-01-02 15:04:05"))
	}
}

// demoFormatting demonstrates output formatting.
func demoFormatting(store *storage.Storage) {
	// Get entries
	entries := store.Query(storage.Query{Limit: 5, Reverse: true})

	// Format using query engine
	formatted := query.FormatEntries(entries)
	fmt.Println("Formatted output:")
	fmt.Print(formatted)

	// Stats formatting
	stats := store.Stats()
	statsFormatted := query.FormatStats(stats)
	fmt.Println("Stats formatted:")
	fmt.Print(statsFormatted)
}

// Ensure strings import is used
var _ = strings.Contains
