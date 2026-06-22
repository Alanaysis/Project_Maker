package wal

import (
	"encoding/binary"
	"errors"
	"fmt"
	"io"
	"os"
	"sync"
)

// Magic number for WAL file identification
const WALMagicNumber uint32 = 0x57414C00

// WALVersion is the current version of the WAL format
const WALVersion uint32 = 1

// SyncMode defines when to sync the WAL to disk.
type SyncMode int

const (
	// SyncImmediate syncs after every write.
	SyncImmediate SyncMode = iota
	// SyncBatch syncs periodically or when buffer is full.
	SyncBatch
	// SyncNone never syncs (for testing only).
	SyncNone
)

// Error definitions
var (
	ErrWALNotInitialized = errors.New("WAL not initialized")
	ErrTransactionNotFound = errors.New("transaction not found")
	ErrChecksumMismatch    = errors.New("checksum mismatch")
	ErrCorruptedLog        = errors.New("corrupted log entry")
	ErrDiskFull            = errors.New("disk full")
	ErrIOError             = errors.New("I/O error")
	ErrInvalidMagicNumber  = errors.New("invalid WAL magic number")
	ErrInvalidVersion      = errors.New("invalid WAL version")
)

// WALHeader represents the header of a WAL file.
type WALHeader struct {
	MagicNumber uint32
	Version     uint32
	CreatedAt   int64
}

// WALWriter writes log entries to a WAL file.
type WALWriter struct {
	mu         sync.Mutex
	file       *os.File
	path       string
	currentLSN uint64
	syncMode   SyncMode
}

// NewWALWriter creates a new WAL writer for the given file path.
func NewWALWriter(path string, syncMode SyncMode) (*WALWriter, error) {
	file, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open WAL file: %w", err)
	}

	writer := &WALWriter{
		file:     file,
		path:     path,
		syncMode: syncMode,
	}

	// Check if file is empty and write header if needed
	stat, err := file.Stat()
	if err != nil {
		file.Close()
		return nil, fmt.Errorf("failed to stat WAL file: %w", err)
	}

	if stat.Size() == 0 {
		if err := writer.writeHeader(); err != nil {
			file.Close()
			return nil, fmt.Errorf("failed to write WAL header: %w", err)
		}
	} else {
		// Read existing entries to determine current LSN
		if err := writer.initializeLSN(); err != nil {
			file.Close()
			return nil, fmt.Errorf("failed to initialize LSN: %w", err)
		}
	}

	return writer, nil
}

// writeHeader writes the WAL file header.
func (w *WALWriter) writeHeader() error {
	header := WALHeader{
		MagicNumber: WALMagicNumber,
		Version:     WALVersion,
		CreatedAt:   0, // Will be set by caller
	}

	if err := binary.Write(w.file, binary.LittleEndian, header.MagicNumber); err != nil {
		return err
	}
	if err := binary.Write(w.file, binary.LittleEndian, header.Version); err != nil {
		return err
	}
	if err := binary.Write(w.file, binary.LittleEndian, header.CreatedAt); err != nil {
		return err
	}

	return nil
}

// initializeLSN reads the existing WAL file to determine the current LSN.
func (w *WALWriter) initializeLSN() error {
	reader, err := NewWALReader(w.path)
	if err != nil {
		return err
	}
	defer reader.Close()

	maxLSN := uint64(0)
	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			// Skip corrupted entries
			continue
		}
		if entry.LSN > maxLSN {
			maxLSN = entry.LSN
		}
	}

	w.currentLSN = maxLSN
	return nil
}

// Write writes a single log entry to the WAL.
func (w *WALWriter) Write(entry *LogEntry) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file == nil {
		return ErrWALNotInitialized
	}

	// Assign LSN
	w.currentLSN++
	entry.LSN = w.currentLSN

	// Serialize entry
	data, err := entry.Serialize()
	if err != nil {
		return fmt.Errorf("failed to serialize entry: %w", err)
	}

	// Write length prefix
	lengthBytes := make([]byte, 4)
	binary.LittleEndian.PutUint32(lengthBytes, uint32(len(data)))

	if _, err := w.file.Write(lengthBytes); err != nil {
		return fmt.Errorf("failed to write length: %w", err)
	}

	// Write data
	if _, err := w.file.Write(data); err != nil {
		return fmt.Errorf("failed to write entry: %w", err)
	}

	// Sync if needed
	if w.syncMode == SyncImmediate {
		if err := w.file.Sync(); err != nil {
			return fmt.Errorf("failed to sync: %w", err)
		}
	}

	return nil
}

// WriteBatch writes multiple log entries to the WAL.
func (w *WALWriter) WriteBatch(entries []*LogEntry) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file == nil {
		return ErrWALNotInitialized
	}

	// Batch serialize
	var batch []byte
	for _, entry := range entries {
		w.currentLSN++
		entry.LSN = w.currentLSN

		data, err := entry.Serialize()
		if err != nil {
			return fmt.Errorf("failed to serialize entry: %w", err)
		}

		lengthBytes := make([]byte, 4)
		binary.LittleEndian.PutUint32(lengthBytes, uint32(len(data)))

		batch = append(batch, lengthBytes...)
		batch = append(batch, data...)
	}

	// Write batch
	if _, err := w.file.Write(batch); err != nil {
		return fmt.Errorf("failed to write batch: %w", err)
	}

	// Sync if needed
	if w.syncMode == SyncImmediate {
		if err := w.file.Sync(); err != nil {
			return fmt.Errorf("failed to sync: %w", err)
		}
	}

	return nil
}

// CurrentLSN returns the current LSN.
func (w *WALWriter) CurrentLSN() uint64 {
	w.mu.Lock()
	defer w.mu.Unlock()
	return w.currentLSN
}

// Sync forces a sync of the WAL to disk.
func (w *WALWriter) Sync() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file == nil {
		return ErrWALNotInitialized
	}

	return w.file.Sync()
}

// Close closes the WAL writer.
func (w *WALWriter) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file == nil {
		return nil
	}

	// Sync before closing
	if err := w.file.Sync(); err != nil {
		return fmt.Errorf("failed to sync before close: %w", err)
	}

	if err := w.file.Close(); err != nil {
		return fmt.Errorf("failed to close file: %w", err)
	}

	w.file = nil
	return nil
}

// WALReader reads log entries from a WAL file.
type WALReader struct {
	file   *os.File
	path   string
	offset int64
}

// NewWALReader creates a new WAL reader for the given file path.
func NewWALReader(path string) (*WALReader, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open WAL file: %w", err)
	}

	reader := &WALReader{
		file: file,
		path: path,
	}

	// Skip header
	reader.offset = 16 // 4 + 4 + 8 bytes

	return reader, nil
}

// ReadNext reads the next log entry from the WAL.
func (r *WALReader) ReadNext() (*LogEntry, error) {
	// Read length
	lengthBytes := make([]byte, 4)
	if _, err := r.file.ReadAt(lengthBytes, r.offset); err != nil {
		if err == io.EOF {
			return nil, io.EOF
		}
		return nil, fmt.Errorf("failed to read length: %w", err)
	}

	length := binary.LittleEndian.Uint32(lengthBytes)
	r.offset += 4

	// Read data
	data := make([]byte, length)
	if _, err := r.file.ReadAt(data, r.offset); err != nil {
		if err == io.EOF {
			return nil, io.EOF
		}
		return nil, fmt.Errorf("failed to read data: %w", err)
	}
	r.offset += int64(length)

	// Deserialize
	entry, err := DeserializeLogEntry(data)
	if err != nil {
		return nil, fmt.Errorf("failed to deserialize entry: %w", err)
	}

	return entry, nil
}

// ReadAll reads all log entries from the WAL.
func (r *WALReader) ReadAll() ([]*LogEntry, error) {
	var entries []*LogEntry

	for {
		entry, err := r.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			return entries, err
		}
		entries = append(entries, entry)
	}

	return entries, nil
}

// ReadByLSN reads a specific log entry by its LSN.
func (r *WALReader) ReadByLSN(targetLSN uint64) (*LogEntry, error) {
	// Reset to beginning
	r.offset = 16

	for {
		entry, err := r.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // Skip corrupted entries
		}
		if entry.LSN == targetLSN {
			return entry, nil
		}
	}

	return nil, fmt.Errorf("entry with LSN %d not found", targetLSN)
}

// SeekToLSN positions the reader at the entry with the given LSN.
func (r *WALReader) SeekToLSN(targetLSN uint64) error {
	// Reset to beginning
	r.offset = 16

	for {
		entryStartOffset := r.offset
		entry, err := r.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // Skip corrupted entries
		}
		if entry.LSN >= targetLSN {
			r.offset = entryStartOffset
			return nil
		}
	}

	return fmt.Errorf("LSN %d not found", targetLSN)
}

// Close closes the WAL reader.
func (r *WALReader) Close() error {
	if r.file == nil {
		return nil
	}
	return r.file.Close()
}
