// Package multiline handles multi-line log entries such as stack traces
// and JSON blocks that span multiple lines.
//
// Multi-line log handling is essential because:
// 1. Stack traces in Java/Go/Python span many lines
// 2. JSON logs may be pretty-printed across multiple lines
// 3. Log lines can wrap in terminal output
//
// The core idea is to determine whether a new line is a continuation
// of the previous log entry or a new entry. This is done using:
// 1. Continuation patterns (regex that matches continuation lines)
// 2. Line content heuristics (does the line look like a new entry?)
// 3. JSON block detection (is this line part of a JSON object?)
package multiline

import (
	"regexp"
	"strings"
)

// Config holds the configuration for multi-line handling.
type Config struct {
	// ContinuationPatterns are regex patterns that match continuation lines.
	// If a line matches any of these patterns, it's treated as a continuation
	// of the previous log entry.
	ContinuationPatterns []string

	// StartPattern is a regex pattern that matches the start of a new log entry.
	// If a line does NOT match this pattern, it's treated as a continuation.
	StartPattern string

	// MaxContinuationLines is the maximum number of consecutive continuation
	// lines before the accumulated entry is flushed.
	MaxContinuationLines int

	// DetectJSONBlocks enables automatic JSON block detection.
	// When enabled, lines that are part of a JSON object (indented or
	// containing braces/brackets) are treated as continuations.
	DetectJSONBlocks bool
}

// DefaultConfig returns a Config with sensible defaults for most use cases.
func DefaultConfig() *Config {
	return &Config{
		// Stack traces typically start with "at " (Java/Go) or "github.com/" (Go)
		// or are indented whitespace followed by specific patterns
		ContinuationPatterns: []string{
			`^\s+at\s+`,           // Java/Go stack trace
			`^\s+---`,             // Go stack trace separator
			`^\s+goroutine\s+`,    // Go goroutine info
			`^\s+File\s+`,         // Python stack trace
			`^\s+Traceback\s+`,    // Python trace header (sometimes)
			`^\s*\)`,              // Closing parenthesis (JSON/object continuation)
			`^\s*[\]}]`,           // Closing bracket/brace
			`^\s*"[^"]*":\s*`,     // JSON key-value pair
		},
		// A new log entry typically starts with a timestamp
		StartPattern: `\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2}`,
		// Flush after 50 consecutive continuation lines to prevent unbounded memory
		MaxContinuationLines: 50,
		DetectJSONBlocks:     true,
	}
}

// Chunk represents a multi-line log entry that has been assembled.
type Chunk struct {
	// Lines contains all the lines in this chunk, in order.
	Lines []string
	// FirstLineNum is the line number of the first line.
	FirstLineNum int
	// LineCount is the total number of lines in this chunk.
	LineCount int
}

// String returns the chunk as a single string with newlines.
func (c *Chunk) String() string {
	return strings.Join(c.Lines, "\n")
}

// Assembler assembles raw lines into multi-line chunks.
type Assembler struct {
	cfg    *Config
	chunk  *Chunk
	done   chan Chunk
}

// NewAssembler creates a new Assembler with the given config.
func NewAssembler(cfg *Config) *Assembler {
	if cfg == nil {
		cfg = DefaultConfig()
	}
	return &Assembler{
		cfg:  cfg,
		done: make(chan Chunk, 100),
	}
}

// Feed sends a line to the assembler. It returns true if the line
// completes a chunk (and the chunk is available in the done channel).
func (a *Assembler) Feed(line string, lineNum int) bool {
	// If we have no chunk yet, start a new one
	if a.chunk == nil {
		a.chunk = &Chunk{
			Lines:        []string{line},
			FirstLineNum: lineNum,
			LineCount:    1,
		}
		return false
	}

	// Check if this line is a continuation of the current chunk
	if a.isContinuation(line) {
		a.chunk.Lines = append(a.chunk.Lines, line)
		a.chunk.LineCount++
		return false
	}

	// This line starts a new entry. Flush the current chunk.
	a.flush()

	// Start a new chunk with this line
	a.chunk = &Chunk{
		Lines:        []string{line},
		FirstLineNum: lineNum,
		LineCount:    1,
	}
	return false
}

// Flush sends the current chunk to the done channel and starts a new chunk.
func (a *Assembler) Flush() {
	if a.chunk != nil {
		a.flush()
	}
}

// flush sends the current chunk to the done channel.
func (a *Assembler) flush() {
	if a.chunk == nil {
		return
	}
	chunk := *a.chunk // Copy
	a.chunk = nil
	select {
	case a.done <- chunk:
	default:
		// Channel full, discard oldest
		select {
		case <-a.done:
			a.done <- chunk
		default:
			a.done <- chunk
		}
	}
}

// Done returns the channel where completed chunks are sent.
func (a *Assembler) Done() <-chan Chunk {
	return a.done
}

// isContinuation checks if a line is a continuation of a log entry.
func (a *Assembler) isContinuation(line string) bool {
	// Check continuation patterns first
	for _, pattern := range a.cfg.ContinuationPatterns {
		if re, err := regexp.Compile(pattern); err == nil {
			if re.MatchString(line) {
				return true
			}
		}
	}

	// Check if line matches the start pattern
	if a.cfg.StartPattern != "" {
		if re, err := regexp.Compile(a.cfg.StartPattern); err == nil {
			if re.MatchString(line) {
				return false // Line looks like a new entry
			}
		}
	}

	// JSON block detection
	if a.cfg.DetectJSONBlocks {
		if a.isJSONContinuation(line) {
			return true
		}
	}

	// If we have too many continuation lines, force flush
	if a.chunk != nil && a.chunk.LineCount >= a.cfg.MaxContinuationLines {
		return false
	}

	// Default: treat as continuation if no pattern matches
	// (heuristic: most log lines that don't match the start pattern are continuations)
	return len(strings.TrimSpace(line)) > 0
}

// isJSONContinuation checks if a line is likely part of a JSON block.
func (a *Assembler) isJSONContinuation(line string) bool {
	trimmed := strings.TrimSpace(line)

	// Count braces/brackets in the current chunk
	var openBraces, openBrackets int
	for _, ch := range a.chunk.Lines {
		for _, c := range ch {
			switch c {
			case '{':
				openBraces++
			case '}':
				openBraces--
			case '[':
				openBrackets++
			case ']':
				openBrackets--
			}
		}
	}

	// If we have unclosed braces/brackets, this line is likely a continuation
	if openBraces > 0 || openBrackets > 0 {
		return true
	}

	// If the line contains a colon (key-value) and is indented, likely JSON
	if strings.Contains(trimmed, ":") && strings.HasPrefix(line, " ") {
		return true
	}

	return false
}

// FlushableChunker is a wrapper that provides a simple Flush method
// and allows reading chunks from Done().
type FlushableChunker struct {
	*Assembler
}

// NewFlushableChunker creates a new FlushableChunker.
func NewFlushableChunker(cfg *Config) *FlushableChunker {
	return &FlushableChunker{Assembler: NewAssembler(cfg)}
}

// FlushAndReset flushes the current chunk and resets for a new one.
func (fc *FlushableChunker) FlushAndReset() {
	fc.Flush()
}
