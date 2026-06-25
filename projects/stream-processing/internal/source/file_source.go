package source

import (
	"bufio"
	"fmt"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/learning/stream-processing/internal/core"
)

// FileSource reads lines from a file and emits them as events.
// Each line becomes an event with the line content as the value.
//
// Options:
//   - KeyFunc: extracts the key from a line (default: "file")
//   - ValueFunc: transforms the line into a value (default: raw string)
//   - TimestampFunc: extracts timestamp from a line (default: current time)
//   - Delimiter: field delimiter for structured files (default: ",")
type FileSource struct {
	path          string
	key           string
	delimiter     string
	keyFunc       func(line string, lineNum int) string
	valueFunc     func(line string) interface{}
	timestampFunc func(line string) time.Time
	stopped       bool
	mu            sync.Mutex
	stopCh        chan struct{}
}

// FileSourceOption configures a FileSource.
type FileSourceOption func(*FileSource)

// WithKeyFunc sets a custom key extraction function.
func WithKeyFunc(fn func(line string, lineNum int) string) FileSourceOption {
	return func(fs *FileSource) {
		fs.keyFunc = fn
	}
}

// WithValueFunc sets a custom value transformation function.
func WithValueFunc(fn func(line string) interface{}) FileSourceOption {
	return func(fs *FileSource) {
		fs.valueFunc = fn
	}
}

// WithTimestampFunc sets a custom timestamp extraction function.
func WithTimestampFunc(fn func(line string) time.Time) FileSourceOption {
	return func(fs *FileSource) {
		fs.timestampFunc = fn
	}
}

// WithDelimiter sets the field delimiter for CSV-like files.
func WithDelimiter(d string) FileSourceOption {
	return func(fs *FileSource) {
		fs.delimiter = d
	}
}

// NewFileSource creates a file source that reads from the given path.
func NewFileSource(path string, opts ...FileSourceOption) *FileSource {
	fs := &FileSource{
		path:      path,
		key:       "file",
		delimiter: ",",
		stopCh:    make(chan struct{}),
	}

	// Default functions
	fs.keyFunc = func(line string, lineNum int) string {
		return fs.key
	}
	fs.valueFunc = func(line string) interface{} {
		return line
	}
	fs.timestampFunc = func(line string) time.Time {
		return time.Now()
	}

	for _, opt := range opts {
		opt(fs)
	}

	return fs
}

func (fs *FileSource) Name() string {
	return fmt.Sprintf("file:%s", fs.path)
}

// Open reads the file and emits events into a stream.
func (fs *FileSource) Open() (*core.Stream, error) {
	file, err := os.Open(fs.path)
	if err != nil {
		return nil, fmt.Errorf("open file %s: %w", fs.path, err)
	}

	stream := core.NewStream(100)

	go func() {
		defer file.Close()
		defer stream.Close()

		scanner := bufio.NewScanner(file)
		lineNum := 0

		for scanner.Scan() {
			fs.mu.Lock()
			if fs.stopped {
				fs.mu.Unlock()
				return
			}
			fs.mu.Unlock()

			line := scanner.Text()
			lineNum++

			// Skip empty lines
			if strings.TrimSpace(line) == "" {
				continue
			}

			key := fs.keyFunc(line, lineNum)
			value := fs.valueFunc(line)
			ts := fs.timestampFunc(line)

			event := core.NewEventWithTime(key, value, ts)

			select {
			case <-fs.stopCh:
				return
			default:
				if !stream.Emit(event) {
					return
				}
			}
		}
	}()

	return stream, nil
}

// Stop signals the source to stop reading.
func (fs *FileSource) Stop() error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	if !fs.stopped {
		fs.stopped = true
		close(fs.stopCh)
	}
	return nil
}

// ParseCSVLine splits a CSV line into fields.
func ParseCSVLine(line, delimiter string) []string {
	return strings.Split(line, delimiter)
}

// ParseKeyValueLine parses "key:value" format.
func ParseKeyValueLine(line, delimiter string) (string, string) {
	parts := strings.SplitN(line, delimiter, 2)
	if len(parts) == 2 {
		return strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1])
	}
	return "default", strings.TrimSpace(line)
}
