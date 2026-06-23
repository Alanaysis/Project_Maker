// Package query implements a query engine for log searching and filtering.
//
// It provides a higher-level interface over the storage layer, supporting
// query string parsing, output formatting, and aggregated queries.
package query

import (
	"fmt"
	"strings"
	"time"

	"github.com/project/log-collector/internal/storage"
)

// Engine provides query capabilities over stored logs.
type Engine struct {
	store *storage.Storage
}

// NewEngine creates a new query Engine.
func NewEngine(store *storage.Storage) *Engine {
	return &Engine{store: store}
}

// Search performs a text search across log messages.
func (e *Engine) Search(text string, limit int) []storage.Entry {
	q := storage.Query{
		Message: text,
		Limit:   limit,
		Reverse: true, // Newest first
	}
	return e.store.Query(q)
}

// ByLevel returns entries matching the given level.
func (e *Engine) ByLevel(level storage.Level, limit int) []storage.Entry {
	q := storage.Query{
		Level:   &level,
		Limit:   limit,
		Reverse: true,
	}
	return e.store.Query(q)
}

// ByTimeRange returns entries within the given time range.
func (e *Engine) ByTimeRange(start, end time.Time, limit int) []storage.Entry {
	q := storage.Query{
		StartTime: &start,
		EndTime:   &end,
		Limit:     limit,
		Reverse:   true,
	}
	return e.store.Query(q)
}

// Recent returns the N most recent entries.
func (e *Engine) Recent(n int) []storage.Entry {
	q := storage.Query{
		Limit:   n,
		Reverse: true,
	}
	return e.store.Query(q)
}

// Errors returns recent error and fatal level entries.
func (e *Engine) Errors(limit int) []storage.Entry {
	levels := []storage.Level{storage.LevelError, storage.LevelFatal}
	q := storage.Query{
		Levels:  levels,
		Limit:   limit,
		Reverse: true,
	}
	return e.store.Query(q)
}

// AdvancedQuery parses a query string and executes it.
//
// Query string format:
//
//	keyword:value [keyword:value ...]
//
// Supported keywords:
//   - level:DEBUG|INFO|WARN|ERROR|FATAL
//   - source:text
//   - message:text
//   - after:2024-01-01
//   - before:2024-12-31
//   - limit:N
//
// Anything without a keyword prefix is treated as a message search.
func (e *Engine) AdvancedQuery(queryStr string) ([]storage.Entry, error) {
	q := storage.Query{
		Reverse: true,
	}

	// Default limit
	q.Limit = 100

	parts := tokenize(queryStr)
	var freeText []string

	for _, part := range parts {
		colonIdx := strings.Index(part, ":")
		if colonIdx < 0 {
			freeText = append(freeText, part)
			continue
		}

		key := strings.ToLower(part[:colonIdx])
		val := part[colonIdx+1:]

		switch key {
		case "level":
			lvl := parseStorageLevel(val)
			q.Level = &lvl
		case "source":
			q.Source = val
		case "message", "msg":
			q.Message = val
		case "after":
			t, err := time.Parse("2006-01-02", val)
			if err != nil {
				return nil, fmt.Errorf("invalid date format for 'after': %s (use YYYY-MM-DD)", val)
			}
			q.StartTime = &t
		case "before":
			t, err := time.Parse("2006-01-02", val)
			if err != nil {
				return nil, fmt.Errorf("invalid date format for 'before': %s (use YYYY-MM-DD)", val)
			}
			q.EndTime = &t
		case "limit":
			n := 0
			fmt.Sscanf(val, "%d", &n)
			if n > 0 {
				q.Limit = n
			}
		default:
			// Unknown keyword, treat as free text
			freeText = append(freeText, part)
		}
	}

	// Combine free text as message search
	if len(freeText) > 0 && q.Message == "" {
		q.Message = strings.Join(freeText, " ")
	}

	return e.store.Query(q), nil
}

// FormatEntries formats entries as human-readable text.
func FormatEntries(entries []storage.Entry) string {
	if len(entries) == 0 {
		return "No entries found."
	}

	var sb strings.Builder
	for _, entry := range entries {
		ts := entry.Timestamp.Format("2006-01-02 15:04:05")
		if entry.Timestamp.IsZero() {
			ts = "----/--/-- --:--:--"
		}
		sb.WriteString(fmt.Sprintf("%s %-5s [%s:%d] %s",
			ts, entry.Level.String(), entry.Source, entry.LineNum, entry.Message))

		// Append fields
		if len(entry.Fields) > 0 {
			sb.WriteString(" |")
			for k, v := range entry.Fields {
				sb.WriteString(fmt.Sprintf(" %s=%s", k, v))
			}
		}
		sb.WriteString("\n")
	}

	return sb.String()
}

// FormatStats formats storage stats as human-readable text.
func FormatStats(stats storage.Stats) string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("Total entries: %d\n", stats.TotalEntries))
	sb.WriteString("Level distribution:\n")
	for lvl, count := range stats.LevelCounts {
		sb.WriteString(fmt.Sprintf("  %-7s: %d\n", lvl, count))
	}
	if len(stats.SourceCounts) > 0 {
		sb.WriteString("Source distribution:\n")
		for src, count := range stats.SourceCounts {
			sb.WriteString(fmt.Sprintf("  %-20s: %d\n", src, count))
		}
	}
	if !stats.OldestEntry.IsZero() {
		sb.WriteString(fmt.Sprintf("Time range: %s to %s\n",
			stats.OldestEntry.Format("2006-01-02 15:04:05"),
			stats.NewestEntry.Format("2006-01-02 15:04:05")))
	}
	return sb.String()
}

// tokenize splits a query string respecting quoted strings.
func tokenize(s string) []string {
	var tokens []string
	var current strings.Builder
	inQuote := false

	for _, ch := range s {
		switch {
		case ch == '"':
			inQuote = !inQuote
		case ch == ' ' && !inQuote:
			if current.Len() > 0 {
				tokens = append(tokens, current.String())
				current.Reset()
			}
		default:
			current.WriteRune(ch)
		}
	}

	if current.Len() > 0 {
		tokens = append(tokens, current.String())
	}

	return tokens
}

// parseStorageLevel parses a level string into storage.Level.
func parseStorageLevel(s string) storage.Level {
	switch strings.ToUpper(strings.TrimSpace(s)) {
	case "DEBUG", "DBG":
		return storage.LevelDebug
	case "INFO", "INF":
		return storage.LevelInfo
	case "WARN", "WARNING", "WRN":
		return storage.LevelWarn
	case "ERROR", "ERR":
		return storage.LevelError
	case "FATAL", "FTL", "PANIC":
		return storage.LevelFatal
	default:
		return storage.LevelUnknown
	}
}
