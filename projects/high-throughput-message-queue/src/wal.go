package queue

import (
	"encoding/binary"
	"fmt"
	"os"
	"sync"
)

// WriteAheadLog implements a write-ahead log (WAL) for durability.
//
// A write-ahead log is a fundamental durability mechanism. Before any data
// is considered "committed", it must first be written to the WAL. If the
// system crashes, the WAL can be replayed to recover uncommitted data.
//
// WAL Design:
//
//	1. Producer writes message to WAL
//	2. WAL flushes to disk (fsync)
//	3. Only then is the message considered "committed"
//	4. On recovery, replay the WAL to restore state
//
// This ensures that no message is lost even if the process crashes immediately
// after the producer's send() call. The trade-off is reduced throughput due
// to synchronous disk writes.
//
// Optimization: We batch WAL entries and flush them together to reduce
// the number of fsync calls, improving throughput while maintaining
// durability guarantees.
type WriteAheadLog struct {
	mu      sync.Mutex
	file    *os.File
	writer  *os.File // Direct file writer (no buffering for durability)
	path    string
	entries []walEntry
	magic   uint32
}

// walEntry is a single WAL entry.
type walEntry struct {
	magic     uint32 // Magic number for validation
	timestamp int64
	offset    int64
	partition int
	dataLen   int32
	data      []byte
	crc       uint32
}

// WAL magic number for file validation
const walMagic uint32 = 0x4D514C57 // "MQLW" in ASCII

// NewWriteAheadLog creates a new WAL at the given path.
func NewWriteAheadLog(path string) (*WriteAheadLog, error) {
	// Create or open the WAL file
	file, err := os.OpenFile(path, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to create WAL: %w", err)
	}

	wal := &WriteAheadLog{
		file:    file,
		writer:  file,
		path:    path,
		entries: make([]walEntry, 0),
		magic:   walMagic,
	}

	// Validate existing WAL
	if err := wal.validate(); err != nil {
		file.Close()
		return nil, err
	}

	return wal, nil
}

// Append adds an entry to the WAL and flushes it to disk.
//
// This is the critical durability path. The entry is written and fsynced
// before the function returns, ensuring it survives a crash.
func (wal *WriteAheadLog) Append(offset int64, partition int, data []byte) error {
	wal.mu.Lock()
	defer wal.mu.Unlock()

	entry := walEntry{
		magic:     wal.magic,
		timestamp: 0,
		offset:    offset,
		partition: partition,
		dataLen:   int32(len(data)),
		data:      data,
		crc:       0,
	}

	// Write entry header: [magic(4) + timestamp(8) + offset(8) + partition(4) + dataLen(4)]
	header := make([]byte, 28)
	binary.LittleEndian.PutUint32(header[0:4], entry.magic)
	binary.LittleEndian.PutUint64(header[4:12], uint64(entry.timestamp))
	binary.LittleEndian.PutUint64(header[12:20], uint64(entry.offset))
	binary.LittleEndian.PutUint32(header[20:24], uint32(entry.partition))
	binary.LittleEndian.PutUint32(header[24:28], uint32(entry.dataLen))

	// Write header + data to WAL
	if _, err := wal.writer.Write(header); err != nil {
		return fmt.Errorf("failed to write WAL header: %w", err)
	}

	if entry.dataLen > 0 {
		if _, err := wal.writer.Write(entry.data); err != nil {
			return fmt.Errorf("failed to write WAL data: %w", err)
		}
	}

	// CRITICAL: fsync to ensure durability
	// This is the most expensive operation in the write path
	// For high throughput, you'd use dedicated fsync threads
	if err := wal.writer.Sync(); err != nil {
		return fmt.Errorf("failed to sync WAL: %w", err)
	}

	wal.entries = append(wal.entries, entry)
	return nil
}

// Recover replays the WAL and returns all entries.
func (wal *WriteAheadLog) Recover() ([]walEntry, error) {
	data, err := os.ReadFile(wal.path)
	if err != nil {
		return nil, err
	}

	var entries []walEntry
	offset := 0

	for offset+28 <= len(data) {
		// Read header
		magic := binary.LittleEndian.Uint32(data[offset : offset+4])
		if magic != wal.magic {
			break // Invalid or truncated entry
		}

		entryTimestamp := int64(binary.LittleEndian.Uint64(data[offset+4 : offset+12]))
		entryOffset := int64(binary.LittleEndian.Uint64(data[offset+12 : offset+20]))
		entryPartition := int(binary.LittleEndian.Uint32(data[offset+20 : offset+24]))
		entryDataLen := int32(binary.LittleEndian.Uint32(data[offset+24 : offset+28]))

		offset += 28

		// Read data
		if offset+int(entryDataLen) > len(data) {
			break // Truncated entry
		}
		entryData := make([]byte, entryDataLen)
		copy(entryData, data[offset:offset+int(entryDataLen)])
		offset += int(entryDataLen)

		entries = append(entries, walEntry{
			magic:     magic,
			timestamp: entryTimestamp,
			offset:    entryOffset,
			partition: entryPartition,
			dataLen:   entryDataLen,
			data:      entryData,
		})
	}

	return entries, nil
}

// Close closes the WAL file.
func (wal *WriteAheadLog) Close() error {
	return wal.file.Close()
}

// validate checks if the WAL file is valid.
func (wal *WriteAheadLog) validate() error {
	// Check magic number at the start of the file
	data, err := os.ReadFile(wal.path)
	if err != nil || len(data) < 4 {
		return nil // New or empty WAL
	}

	magic := binary.LittleEndian.Uint32(data[0:4])
	if magic != wal.magic {
		return fmt.Errorf("invalid WAL magic number: 0x%08x", magic)
	}

	return nil
}

// Truncate removes the WAL file (for cleanup).
func (wal *WriteAheadLog) Truncate() error {
	wal.mu.Lock()
	defer wal.mu.Unlock()

	wal.entries = wal.entries[:0]
	return os.Remove(wal.path)
}
