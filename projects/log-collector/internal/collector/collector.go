// Package collector implements log collection from various sources.
//
// The collector is responsible for reading raw log lines from sources
// (files, stdin) and feeding them into the processing pipeline.
package collector

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"sync"
)

// RawLog represents a raw log line with its source metadata.
type RawLog struct {
	Line      string // The raw log line
	Source    string // Source identifier (filename, "stdin", etc.)
	LineNum   int    // Line number in the source
	Timestamp int64  // Collection timestamp (Unix nano)
}

// Source represents a log source to collect from.
type Source struct {
	Name string // Human-readable name
	Path string // File path (empty for stdin)
}

// Collector collects log lines from configured sources.
type Collector struct {
	sources  []Source
	output   chan RawLog
	done     chan struct{}
	wg       sync.WaitGroup
	stopOnce sync.Once
}

// New creates a new Collector with the given sources.
// The output channel is where collected raw logs will be sent.
func New(sources []Source, output chan RawLog) *Collector {
	return &Collector{
		sources: sources,
		output:  output,
		done:    make(chan struct{}),
	}
}

// Start begins collecting logs from all configured sources.
// Each source is read in its own goroutine.
func (c *Collector) Start() error {
	if len(c.sources) == 0 {
		return fmt.Errorf("no sources configured")
	}

	for _, src := range c.sources {
		c.wg.Add(1)
		go c.collectSource(src)
	}

	// Wait for all sources to finish in background
	go func() {
		c.wg.Wait()
		c.stopOnce.Do(func() {
			close(c.done)
		})
	}()

	return nil
}

// Stop signals the collector to stop and waits for completion.
func (c *Collector) Stop() {
	c.stopOnce.Do(func() {
		close(c.done)
	})
	c.wg.Wait()
}

// Done returns a channel that is closed when all collection is complete.
func (c *Collector) Done() <-chan struct{} {
	return c.done
}

// collectSource reads lines from a single source.
func (c *Collector) collectSource(src Source) {
	defer c.wg.Done()

	var reader io.Reader

	if src.Path == "" || src.Path == "-" {
		reader = os.Stdin
	} else {
		file, err := os.Open(src.Path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "collector: failed to open %s: %v\n", src.Path, err)
			return
		}
		defer file.Close()
		reader = file
	}

	c.readLines(reader, src.Name)
}

// readLines reads lines from a reader and sends them to the output channel.
func (c *Collector) readLines(reader io.Reader, source string) {
	scanner := bufio.NewScanner(reader)
	// Increase buffer size for long log lines (max 1MB)
	scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := scanner.Text()
		if line == "" {
			continue // Skip empty lines
		}

		rawLog := RawLog{
			Line:    line,
			Source:  source,
			LineNum: lineNum,
		}

		select {
		case c.output <- rawLog:
		case <-c.done:
			return
		}
	}

	if err := scanner.Err(); err != nil {
		fmt.Fprintf(os.Stderr, "collector: error reading %s: %v\n", source, err)
	}
}

// CollectFromReader collects log lines from an io.Reader (useful for testing).
func CollectFromReader(reader io.Reader, source string) []RawLog {
	var logs []RawLog
	scanner := bufio.NewScanner(reader)
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := scanner.Text()
		if line == "" {
			continue
		}
		logs = append(logs, RawLog{
			Line:    line,
			Source:  source,
			LineNum: lineNum,
		})
	}

	return logs
}
