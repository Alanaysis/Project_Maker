package transport

import (
	"fmt"
	"os"
	"sync"
	"time"
)

// FileWriter writes log entries to a file with optional rotation.
type FileWriter struct {
	path     string
	file     *os.File
	mu       sync.Mutex
	maxSize  int64 // Maximum file size in bytes before rotation (0 = no limit)
	maxAge   time.Duration // Maximum age before rotation (0 = no limit)
	curSize  int64
	stopOnce sync.Once
	done     chan struct{}
}

// FileWriterConfig configures a FileWriter.
type FileWriterConfig struct {
	Path    string        // File path to write to
	MaxSize int64         // Maximum file size in bytes before rotation (0 = no limit)
	MaxAge  time.Duration // Maximum age before rotation (0 = no limit)
}

// NewFileWriter creates a new FileWriter with the given configuration.
func NewFileWriter(cfg FileWriterConfig) (*FileWriter, error) {
	file, err := os.OpenFile(cfg.Path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return nil, fmt.Errorf("file writer: failed to open %s: %w", cfg.Path, err)
	}

	// Get current size
	info, err := file.Stat()
	if err != nil {
		file.Close()
		return nil, fmt.Errorf("file writer: failed to stat %s: %w", cfg.Path, err)
	}

	return &FileWriter{
		path:    cfg.Path,
		file:    file,
		maxSize: cfg.MaxSize,
		maxAge:  cfg.MaxAge,
		curSize: info.Size(),
		done:    make(chan struct{}),
	}, nil
}

// Write writes a log line to the file.
func (w *FileWriter) Write(line string) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Check if rotation is needed
	if w.needsRotation() {
		if err := w.rotate(); err != nil {
			return fmt.Errorf("file writer: rotation failed: %w", err)
		}
	}

	n, err := fmt.Fprintln(w.file, line)
	if err != nil {
		return fmt.Errorf("file writer: write failed: %w", err)
	}

	w.curSize += int64(n)
	return nil
}

// WriteEntry writes a formatted log entry to the file.
func (w *FileWriter) WriteEntry(timestamp time.Time, level, source, message string) error {
	line := fmt.Sprintf("%s %-5s [%s] %s",
		timestamp.Format("2006-01-02 15:04:05"),
		level,
		source,
		message,
	)
	return w.Write(line)
}

// needsRotation checks if the file needs to be rotated.
func (w *FileWriter) needsRotation() bool {
	if w.maxSize > 0 && w.curSize >= w.maxSize {
		return true
	}
	return false
}

// rotate rotates the current log file.
func (w *FileWriter) rotate() error {
	// Close current file
	if err := w.file.Close(); err != nil {
		return err
	}

	// Rename current file with timestamp
	rotatedName := fmt.Sprintf("%s.%s", w.path, time.Now().Format("20060102-150405"))
	if err := os.Rename(w.path, rotatedName); err != nil {
		return err
	}

	// Open new file
	file, err := os.OpenFile(w.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}

	w.file = file
	w.curSize = 0
	return nil
}

// Close closes the file writer.
func (w *FileWriter) Close() error {
	w.stopOnce.Do(func() {
		close(w.done)
	})
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.file != nil {
		return w.file.Close()
	}
	return nil
}

// Done returns a channel that is closed when the writer is closed.
func (w *FileWriter) Done() <-chan struct{} {
	return w.done
}
