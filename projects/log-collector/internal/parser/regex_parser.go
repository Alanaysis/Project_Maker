package parser

import (
	"fmt"
	"regexp"
	"time"
)

// RegexParser parses log lines using a user-defined regular expression.
// Named capture groups in the regex are mapped to Entry fields.
//
// Recognized named groups:
//   - time, ts, timestamp: parsed as timestamp
//   - level, severity, lvl: parsed as log level
//   - msg, message: used as the message
//   - Any other named group is stored in Fields
//
// Example pattern:
//
//	`^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<msg>.+)$`
type RegexParser struct {
	pattern     *regexp.Regexp
	groupNames  []string
	timeFormats []string
}

// NewRegexParser creates a new RegexParser with the given pattern.
// Returns an error if the pattern is not a valid regular expression.
func NewRegexParser(pattern string) (*RegexParser, error) {
	re, err := regexp.Compile(pattern)
	if err != nil {
		return nil, fmt.Errorf("invalid regex pattern: %w", err)
	}

	// Extract named groups
	groupNames := re.SubexpNames()

	return &RegexParser{
		pattern:    re,
		groupNames: groupNames,
		timeFormats: []string{
			time.RFC3339,
			time.RFC3339Nano,
			"2006-01-02T15:04:05",
			"2006-01-02 15:04:05",
			"2006-01-02 15:04:05.000",
			"02/Jan/2006:15:04:05 -0700",
			"Jan 02 15:04:05",
		},
	}, nil
}

// Parse parses a raw log line using the regex pattern.
func (rp *RegexParser) Parse(rawLine string, source string, lineNum int) (*Entry, error) {
	matches := rp.pattern.FindStringSubmatch(rawLine)
	if matches == nil {
		return nil, fmt.Errorf("line does not match regex pattern")
	}

	entry := &Entry{
		Level:   LevelUnknown,
		Fields:  make(map[string]string),
		Source:  source,
		LineNum: lineNum,
		Raw:     rawLine,
	}

	// Map named groups to entry fields
	for i, name := range rp.groupNames {
		if i == 0 || name == "" {
			continue // Skip unnamed group (index 0 is the full match)
		}

		value := matches[i]
		switch name {
		case "time", "ts", "timestamp":
			entry.Timestamp = rp.parseTime(value)
		case "level", "severity", "lvl":
			entry.Level = ParseLevel(value)
		case "msg", "message":
			entry.Message = value
		default:
			entry.Fields[name] = value
		}
	}

	if entry.Timestamp.IsZero() {
		entry.Timestamp = time.Now()
	}

	return entry, nil
}

// parseTime tries multiple time formats.
func (rp *RegexParser) parseTime(s string) time.Time {
	for _, format := range rp.timeFormats {
		if t, err := time.Parse(format, s); err == nil {
			return t
		}
	}
	return time.Time{}
}

// Pattern returns the compiled regex pattern.
func (rp *RegexParser) Pattern() *regexp.Regexp {
	return rp.pattern
}

// CommonPatterns provides ready-to-use regex patterns for common log formats.
var CommonPatterns = map[string]string{
	// Apache/Nginx Combined Log Format
	"apache": `^(?P<remote>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d+) (?P<size>\d+)`,
	// Syslog format
	"syslog": `^(?P<time>\w{3} \d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<app>\S+?)(\[(?P<pid>\d+)\])?: (?P<msg>.+)$`,
	// Generic timestamp + level + message
	"generic": `^(?P<time>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*)\s*[(\[]?(?P<level>DEBUG|INFO|WARN|ERROR|FATAL)[)\]]?\s*(?P<msg>.+)$`,
	// Access log with IP, timestamp, method, path, status
	"access": `^(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<time>[^\]]+)\] "(?P<method>\w+) (?P<path>[^"]+)" (?P<status>\d+)`,
}
