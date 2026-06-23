// Package parser implements log line parsing into structured entries.
//
// It supports multiple log formats:
//   - JSON: {"level":"info","msg":"hello","ts":"2024-01-01T00:00:00Z"}
//   - Logfmt: level=info msg=hello ts=2024-01-01T00:00:00Z
//   - Common: 2024-01-01 12:00:00 [INFO] server: message
//   - Auto-detect: tries each format in order
package parser

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// Level represents log severity levels.
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

// ParseLevel parses a string into a Level.
func ParseLevel(s string) Level {
	switch strings.ToUpper(strings.TrimSpace(s)) {
	case "DEBUG", "DBG":
		return LevelDebug
	case "INFO", "INF":
		return LevelInfo
	case "WARN", "WARNING", "WRN":
		return LevelWarn
	case "ERROR", "ERR":
		return LevelError
	case "FATAL", "FTL", "PANIC":
		return LevelFatal
	default:
		return LevelUnknown
	}
}

// Entry represents a parsed log entry.
type Entry struct {
	Timestamp time.Time         // When the log was generated
	Level     Level             // Log severity level
	Message   string            // The log message
	Fields    map[string]string // Additional key-value fields
	Source    string            // Source identifier
	LineNum   int               // Original line number
	Raw       string            // Original raw line
}

// Format represents a log format type.
type Format int

const (
	FormatAuto   Format = iota // Auto-detect format
	FormatJSON                 // JSON format
	FormatLogfmt               // Logfmt (key=value) format
	FormatCommon               // Common log format: "2024-01-01 12:00:00 [INFO] message"
)

// Parser parses raw log lines into structured entries.
type Parser struct {
	format      Format
	timeFormats []string
}

// New creates a new Parser with the given format.
func New(format Format) *Parser {
	return &Parser{
		format: format,
		timeFormats: []string{
			time.RFC3339,
			time.RFC3339Nano,
			"2006-01-02T15:04:05",
			"2006-01-02 15:04:05",
			"2006-01-02 15:04:05.000",
			"02/Jan/2006:15:04:05 -0700",
			"Jan 02 15:04:05",
		},
	}
}

// Parse parses a raw log line into an Entry.
func (p *Parser) Parse(rawLine string, source string, lineNum int) (*Entry, error) {
	rawLine = strings.TrimSpace(rawLine)
	if rawLine == "" {
		return nil, fmt.Errorf("empty log line")
	}

	var entry *Entry
	var err error

	switch p.format {
	case FormatJSON:
		entry, err = p.parseJSON(rawLine)
	case FormatLogfmt:
		entry, err = p.parseLogfmt(rawLine)
	case FormatCommon:
		entry, err = p.parseCommon(rawLine)
	case FormatAuto:
		entry, err = p.parseAuto(rawLine)
	default:
		return nil, fmt.Errorf("unsupported format: %d", p.format)
	}

	if err != nil {
		return nil, err
	}

	entry.Source = source
	entry.LineNum = lineNum
	entry.Raw = rawLine
	return entry, nil
}

// parseAuto tries each format in order.
func (p *Parser) parseAuto(line string) (*Entry, error) {
	// Try JSON first
	if entry, err := p.parseJSON(line); err == nil {
		return entry, nil
	}

	// Try logfmt
	if entry, err := p.parseLogfmt(line); err == nil {
		return entry, nil
	}

	// Try common format
	if entry, err := p.parseCommon(line); err == nil {
		return entry, nil
	}

	// Fallback: treat entire line as message
	return &Entry{
		Timestamp: time.Now(),
		Level:     LevelUnknown,
		Message:   line,
		Fields:    make(map[string]string),
	}, nil
}

// parseJSON parses a JSON log line.
func (p *Parser) parseJSON(line string) (*Entry, error) {
	var raw map[string]interface{}
	if err := json.Unmarshal([]byte(line), &raw); err != nil {
		return nil, fmt.Errorf("not valid JSON: %w", err)
	}

	entry := &Entry{
		Level:  LevelUnknown,
		Fields: make(map[string]string),
	}

	// Extract known fields
	for key, val := range raw {
		valStr := fmt.Sprintf("%v", val)
		switch strings.ToLower(key) {
		case "msg", "message":
			entry.Message = valStr
		case "level", "severity", "lvl":
			entry.Level = ParseLevel(valStr)
		case "time", "ts", "timestamp", "@timestamp":
			entry.Timestamp = p.parseTime(valStr)
		default:
			entry.Fields[key] = valStr
		}
	}

	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now()
	}

	return entry, nil
}

// parseLogfmt parses a logfmt line (key=value pairs).
func (p *Parser) parseLogfmt(line string) (*Entry, error) {
	if !strings.Contains(line, "=") {
		return nil, fmt.Errorf("not logfmt format")
	}

	entry := &Entry{
		Level:  LevelUnknown,
		Fields: make(map[string]string),
	}

	pairs := tokenizeLogfmt(line)
	if len(pairs) == 0 {
		return nil, fmt.Errorf("no key=value pairs found")
	}

	for key, val := range pairs {
		switch strings.ToLower(key) {
		case "msg", "message":
			entry.Message = val
		case "level", "severity", "lvl":
			entry.Level = ParseLevel(val)
		case "time", "ts", "timestamp":
			entry.Timestamp = p.parseTime(val)
		default:
			entry.Fields[key] = val
		}
	}

	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now()
	}

	return entry, nil
}

// tokenizeLogfmt splits a logfmt line into key=value pairs, handling quoted values.
func tokenizeLogfmt(line string) map[string]string {
	pairs := make(map[string]string)

	for len(line) > 0 {
		// Skip leading whitespace
		line = strings.TrimLeft(line, " \t")
		if len(line) == 0 {
			break
		}

		// Find the key
		eqIdx := strings.Index(line, "=")
		if eqIdx < 0 {
			break
		}
		key := line[:eqIdx]
		line = line[eqIdx+1:]

		// Extract the value (may be quoted)
		var val string
		if len(line) > 0 && line[0] == '"' {
			// Quoted value: find closing quote
			endQuote := strings.Index(line[1:], "\"")
			if endQuote >= 0 {
				val = line[1 : endQuote+1]
				line = line[endQuote+2:]
			} else {
				// No closing quote, take rest of line
				val = line[1:]
				line = ""
			}
		} else {
			// Unquoted value: read until next space
			spaceIdx := strings.IndexAny(line, " \t")
			if spaceIdx < 0 {
				val = line
				line = ""
			} else {
				val = line[:spaceIdx]
				line = line[spaceIdx:]
			}
		}

		if key != "" {
			pairs[key] = val
		}
	}

	return pairs
}

// parseCommon parses common log format: "2024-01-01 12:00:00 [INFO] message"
func (p *Parser) parseCommon(line string) (*Entry, error) {
	entry := &Entry{
		Fields: make(map[string]string),
	}

	// Try to match: "YYYY-MM-DD HH:MM:SS [LEVEL] message"
	// Find the level bracket
	levelStart := strings.Index(line, "[")
	levelEnd := strings.Index(line, "]")

	if levelStart < 0 || levelEnd < 0 || levelEnd <= levelStart {
		return nil, fmt.Errorf("no level bracket found")
	}

	// Parse level
	levelStr := line[levelStart+1 : levelEnd]
	entry.Level = ParseLevel(levelStr)

	// Parse timestamp (everything before the level bracket)
	timeStr := strings.TrimSpace(line[:levelStart])
	entry.Timestamp = p.parseTime(timeStr)

	// Parse message (everything after the level bracket)
	entry.Message = strings.TrimSpace(line[levelEnd+1:])

	return entry, nil
}

// parseTime tries multiple time formats.
func (p *Parser) parseTime(s string) time.Time {
	for _, fmt := range p.timeFormats {
		if t, err := time.Parse(fmt, s); err == nil {
			return t
		}
	}
	return time.Time{}
}
