// Package filter implements log entry filtering with multiple strategies.
//
// It supports filtering by log level, keyword matching, and regex patterns.
// Filters can be composed to create complex filtering pipelines.
package filter

import (
	"regexp"
	"strings"
)

// Level represents a log severity level for filtering.
type Level int

const (
	LevelDebug Level = iota
	LevelInfo
	LevelWarn
	LevelError
	LevelFatal
	LevelUnknown
)

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

// Entry represents a minimal log entry for filtering purposes.
// This is decoupled from storage/parser Entry to keep the filter package independent.
type Entry struct {
	Level   Level
	Message string
	Source  string
	Fields  map[string]string
}

// Filter defines the interface for log filtering.
type Filter interface {
	// Match returns true if the entry passes the filter.
	Match(entry Entry) bool
}

// LevelFilter filters entries by minimum log level.
// Only entries with level >= MinLevel are allowed through.
type LevelFilter struct {
	MinLevel Level
}

// Match returns true if the entry's level is >= the minimum level.
func (f *LevelFilter) Match(entry Entry) bool {
	return entry.Level >= f.MinLevel
}

// KeywordFilter filters entries by keyword presence in the message.
// When CaseSensitive is false (default), matching is case-insensitive.
type KeywordFilter struct {
	Keyword      string
	CaseSensitive bool
	Exclude       bool // If true, entries containing the keyword are excluded
}

// Match returns true if the entry passes the keyword filter.
func (f *KeywordFilter) Match(entry Entry) bool {
	msg := entry.Message
	keyword := f.Keyword

	if !f.CaseSensitive {
		msg = strings.ToLower(msg)
		keyword = strings.ToLower(keyword)
	}

	found := strings.Contains(msg, keyword)
	if f.Exclude {
		return !found
	}
	return found
}

// RegexFilter filters entries by a regular expression pattern applied to the message.
type RegexFilter struct {
	Pattern *regexp.Regexp
	Exclude bool // If true, entries matching the pattern are excluded
}

// NewRegexFilter creates a new RegexFilter from a pattern string.
// Returns an error if the pattern is not a valid regular expression.
func NewRegexFilter(pattern string, exclude bool) (*RegexFilter, error) {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return nil, err
	}
	return &RegexFilter{Pattern: re, Exclude: exclude}, nil
}

// Match returns true if the entry passes the regex filter.
func (f *RegexFilter) Match(entry Entry) bool {
	found := f.Pattern.MatchString(entry.Message)
	if f.Exclude {
		return !found
	}
	return found
}

// SourceFilter filters entries by source name.
type SourceFilter struct {
	Source  string
	Exclude bool // If true, entries from this source are excluded
}

// Match returns true if the entry passes the source filter.
func (f *SourceFilter) Match(entry Entry) bool {
	found := strings.Contains(entry.Source, f.Source)
	if f.Exclude {
		return !found
	}
	return found
}

// Chain combines multiple filters with AND logic.
// All filters must match for an entry to pass.
type Chain struct {
	Filters []Filter
}

// NewChain creates a new filter chain.
func NewChain(filters ...Filter) *Chain {
	return &Chain{Filters: filters}
}

// Match returns true only if ALL filters in the chain match.
func (c *Chain) Match(entry Entry) bool {
	for _, f := range c.Filters {
		if !f.Match(entry) {
			return false
		}
	}
	return true
}

// MatchAny combines multiple filters with OR logic.
// At least one filter must match for an entry to pass.
type MatchAny struct {
	Filters []Filter
}

// Match returns true if ANY filter in the set matches.
func (m *MatchAny) Match(entry Entry) bool {
	for _, f := range m.Filters {
		if f.Match(entry) {
			return true
		}
	}
	return false
}

// Apply applies a filter to a slice of entries and returns matching entries.
func Apply(entries []Entry, f Filter) []Entry {
	var result []Entry
	for _, entry := range entries {
		if f.Match(entry) {
			result = append(result, entry)
		}
	}
	return result
}
