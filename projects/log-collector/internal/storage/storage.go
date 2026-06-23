// Package storage implements log storage and indexing.
//
// It provides an in-memory storage with indexing for fast querying
// by time range, level, and text search.
package storage

import (
	"fmt"
	"sort"
	"strings"
	"sync"
	"time"
)

// Level represents log severity levels (mirrors parser.Level).
type Level int

const (
	LevelDebug Level = iota
	LevelInfo
	LevelWarn
	LevelError
	LevelFatal
	LevelUnknown
)

// Entry represents a stored log entry.
type Entry struct {
	ID        int               // Unique ID
	Timestamp time.Time         // When the log was generated
	Level     Level             // Log severity level
	Message   string            // The log message
	Fields    map[string]string // Additional key-value fields
	Source    string            // Source identifier
	LineNum   int               // Original line number
	Raw       string            // Original raw line
}

// String returns the string representation of a log level.
func (l Level) String() string {
	switch l {
	case LevelDebug:
		return "DEBUG"
	case LevelInfo:
		return "INFO"
	case LevelWarn:
		return "WARN"
	case LevelError:
		return "ERROR"
	case LevelFatal:
		return "FATAL"
	default:
		return "UNKNOWN"
	}
}

// Query represents a log query with filters.
type Query struct {
	StartTime *time.Time        // Filter: start time (inclusive)
	EndTime   *time.Time        // Filter: end time (inclusive)
	Level     *Level            // Filter: exact level
	Levels    []Level           // Filter: multiple levels
	Source    string            // Filter: source contains
	Message   string            // Filter: message contains (case-insensitive)
	Fields    map[string]string // Filter: exact field matches
	Limit     int               // Max results to return (0 = no limit)
	Offset    int               // Skip first N results
	Reverse   bool              // Return results in reverse order (newest first)
}

// Stats contains storage statistics.
type Stats struct {
	TotalEntries int
	LevelCounts  map[string]int
	SourceCounts map[string]int
	OldestEntry  time.Time
	NewestEntry  time.Time
}

// Storage is an in-memory log storage with indexing.
type Storage struct {
	mu       sync.RWMutex
	entries  []Entry
	nextID   int
	timeIdx  []int // Index into entries, sorted by time
	levelIdx map[Level][]int
	srcIdx   map[string][]int
}

// New creates a new Storage.
func New() *Storage {
	return &Storage{
		entries:  make([]Entry, 0),
		levelIdx: make(map[Level][]int),
		srcIdx:   make(map[string][]int),
	}
}

// Store adds a log entry to the storage.
func (s *Storage) Store(entry Entry) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.nextID++
	entry.ID = s.nextID

	s.entries = append(s.entries, entry)

	// Update time index (entries are appended in order, so always sorted)
	s.timeIdx = append(s.timeIdx, entry.ID-1)

	// Update level index
	s.levelIdx[entry.Level] = append(s.levelIdx[entry.Level], entry.ID-1)

	// Update source index
	if entry.Source != "" {
		s.srcIdx[entry.Source] = append(s.srcIdx[entry.Source], entry.ID-1)
	}

	return entry.ID
}

// Query searches for log entries matching the given query.
func (s *Storage) Query(q Query) []Entry {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// Start with all entries or narrow by indexed fields
	var indices []int

	// Use the most selective index
	if q.Level != nil {
		indices = s.levelIdx[*q.Level]
	} else if len(q.Levels) > 0 {
		for _, lvl := range q.Levels {
			indices = append(indices, s.levelIdx[lvl]...)
		}
		sort.Ints(indices)
	} else if q.Source != "" {
		// Find sources containing the query
		for src, idxs := range s.srcIdx {
			if strings.Contains(src, q.Source) {
				indices = append(indices, idxs...)
			}
		}
		sort.Ints(indices)
	} else {
		// Use all entries
		indices = make([]int, len(s.entries))
		for i := range indices {
			indices[i] = i
		}
	}

	// Apply filters
	var results []Entry
	for _, idx := range indices {
		if idx >= len(s.entries) {
			continue
		}
		entry := s.entries[idx]

		// Time filter
		if q.StartTime != nil && entry.Timestamp.Before(*q.StartTime) {
			continue
		}
		if q.EndTime != nil && entry.Timestamp.After(*q.EndTime) {
			continue
		}

		// Level filter (when not used as primary index)
		if q.Level != nil && entry.Level != *q.Level {
			continue
		}

		// Source filter (when not used as primary index)
		if q.Source != "" && !strings.Contains(entry.Source, q.Source) {
			continue
		}

		// Message filter
		if q.Message != "" && !strings.Contains(
			strings.ToLower(entry.Message),
			strings.ToLower(q.Message),
		) {
			continue
		}

		// Fields filter
		if len(q.Fields) > 0 {
			match := true
			for k, v := range q.Fields {
				if entry.Fields[k] != v {
					match = false
					break
				}
			}
			if !match {
				continue
			}
		}

		results = append(results, entry)
	}

	// When Reverse is true, take from the end (most recent first)
	if q.Reverse {
		// Reverse the results first
		for i, j := 0, len(results)-1; i < j; i, j = i+1, j-1 {
			results[i], results[j] = results[j], results[i]
		}
	}

	// Apply offset
	if q.Offset > 0 && q.Offset < len(results) {
		results = results[q.Offset:]
	} else if q.Offset >= len(results) {
		return nil
	}

	// Apply limit
	if q.Limit > 0 && q.Limit < len(results) {
		results = results[:q.Limit]
	}

	return results
}

// Count returns the number of stored entries.
func (s *Storage) Count() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.entries)
}

// Stats returns storage statistics.
func (s *Storage) Stats() Stats {
	s.mu.RLock()
	defer s.mu.RUnlock()

	stats := Stats{
		TotalEntries: len(s.entries),
		LevelCounts:  make(map[string]int),
		SourceCounts: make(map[string]int),
	}

	for _, entry := range s.entries {
		stats.LevelCounts[entry.Level.String()]++
		if entry.Source != "" {
			stats.SourceCounts[entry.Source]++
		}

		if stats.OldestEntry.IsZero() || entry.Timestamp.Before(stats.OldestEntry) {
			stats.OldestEntry = entry.Timestamp
		}
		if entry.Timestamp.After(stats.NewestEntry) {
			stats.NewestEntry = entry.Timestamp
		}
	}

	return stats
}

// GetByID returns a single entry by its ID.
func (s *Storage) GetByID(id int) (Entry, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if id < 1 || id > len(s.entries) {
		return Entry{}, fmt.Errorf("entry %d not found", id)
	}

	return s.entries[id-1], nil
}

// Clear removes all entries from storage.
func (s *Storage) Clear() {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.entries = s.entries[:0]
	s.timeIdx = s.timeIdx[:0]
	s.levelIdx = make(map[Level][]int)
	s.srcIdx = make(map[string][]int)
	s.nextID = 0
}
