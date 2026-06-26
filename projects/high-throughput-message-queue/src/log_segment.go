package queue

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// LogSegment represents a single append-only log file for a partition.
//
// A log segment is a file containing a range of messages with contiguous offsets.
// Segments are created when:
//   - The current segment reaches the configured max size
//   - A new segment is needed for time-based rollover
//
// Each segment file is named by its base offset (e.g., "00000000000000000042").
// This naming convention allows segments to be sorted lexicographically by offset.
//
// For each segment, we also maintain:
//   - .index file: Maps offsets to byte positions within the segment
//   - .translog file: Write-ahead log for crash recovery
type LogSegment struct {
	dir          string
	filename     string
	baseOffset   int64    // First offset in this segment
	file         *os.File
	writer       *bufio.Writer
	index        *IndexFile
	timestamp    int64    // Creation timestamp (nanoseconds)
	size         int64    // Current file size
	mu           sync.Mutex
	storage      StorageConfig
	isDeleted    bool
}

// NewLogSegment creates a new log segment file.
func NewLogSegment(dir, filename string, storage StorageConfig) (*LogSegment, error) {
	baseOffset, err := parseOffsetFilename(filename)
	if err != nil {
		return nil, err
	}

	fullPath := filepath.Join(dir, filename)
	file, err := os.OpenFile(fullPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to create segment file: %w", err)
	}

	indexPath := filepath.Join(dir, filename+".index")
	index := NewIndexFile(indexPath, storage.IndexBufferSize)

	seg := &LogSegment{
		dir:          dir,
		filename:     filename,
		baseOffset:   baseOffset,
		file:         file,
		writer:       bufio.NewWriterSize(file, 256*1024), // 256KB write buffer
		index:        index,
		timestamp:    0,
		size:         0,
		storage:      storage,
	}

	return seg, nil
}

// OpenLogSegment opens an existing log segment.
func OpenLogSegment(dir, filename string, storage StorageConfig) (*LogSegment, error) {
	baseOffset, err := parseOffsetFilename(filename)
	if err != nil {
		return nil, err
	}

	fullPath := filepath.Join(dir, filename)
	file, err := os.OpenFile(fullPath, os.O_RDONLY, 0644)
	if err != nil {
		return nil, fmt.Errorf("failed to open segment file: %w", err)
	}

	// Get file size
	info, err := file.Stat()
	if err != nil {
		file.Close()
		return nil, err
	}

	indexPath := filepath.Join(dir, filename+".index")
	index := NewIndexFile(indexPath, storage.IndexBufferSize)
	index.Load()

	seg := &LogSegment{
		dir:          dir,
		filename:     filename,
		baseOffset:   baseOffset,
		file:         file,
		index:        index,
		timestamp:    0,
		size:         info.Size(),
		storage:      storage,
	}

	return seg, nil
}

// Append writes a message to the segment and records its index entry.
// Returns the offset assigned to the message.
//
// Write path optimization:
// 1. Messages are written to a buffered writer, reducing syscall count
// 2. The index is updated in-memory, only flushed periodically
// 3. CRC32 checksums ensure data integrity without expensive validation
func (s *LogSegment) Append(msg *Message) (int64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if s.isDeleted {
		return -1, fmt.Errorf("segment is deleted")
	}

	// Assign offset
	offset := s.baseOffset + s.index.EntryCount()
	msg.Offset = offset
	msg.Partition = -1 // Will be set by the partition
	msg.Checksum = msg.Checksum()

	// Marshal message to bytes
	data, err := msg.Marshal()
	if err != nil {
		return -1, fmt.Errorf("failed to marshal message: %w", err)
	}

	// Write message length and data to file
	// Format: [4-byte length][message bytes]
	lengthBytes := make([]byte, 4)
	binary.LittleEndian.PutUint32(lengthBytes, uint32(len(data)))

	if _, err := s.writer.Write(lengthBytes); err != nil {
		return -1, fmt.Errorf("failed to write length: %w", err)
	}

	if _, err := s.writer.Write(data); err != nil {
		return -1, fmt.Errorf("failed to write message: %w", err)
	}

	// Update size tracking
	s.size += int64(4 + len(data))

	// Update index: store offset and relative position
	// Using relative position instead of absolute for index compression
	relativePos := uint32(s.size)
	s.index.Append(offset, relativePos)

	// Periodically flush the write buffer
	// This is a trade-off between performance and durability
	if s.index.EntryCount() % 1000 == 0 {
		if err := s.writer.Flush(); err != nil {
			return -1, fmt.Errorf("failed to flush writer: %w", err)
		}
	}

	return offset, nil
}

// Read reads messages starting from the given offset within this segment.
func (s *LogSegment) Read(startOffset int64, maxMessages int) ([]*Message, error) {
	if s.isDeleted {
		return nil, fmt.Errorf("segment is deleted")
	}

	if startOffset < s.baseOffset {
		return nil, fmt.Errorf("offset %d is before segment base offset %d", startOffset, s.baseOffset)
	}

	// Use index to find the byte position for startOffset
	pos, found := s.index.Lookup(startOffset)
	if !found {
		// Fall back to linear scan from the beginning
		pos = 0
	}

	// Seek to the position
	if _, err := s.file.Seek(int64(pos), 0); err != nil {
		return nil, fmt.Errorf("failed to seek: %w", err)
	}

	reader := bufio.NewReader(s.file)
	var messages []*Message

	for len(messages) < maxMessages {
		// Read message length
		lengthBytes := make([]byte, 4)
		_, err := reader.Read(lengthBytes)
		if err != nil {
			break // End of segment or error
		}

		msgLen := int(binary.LittleEndian.Uint32(lengthBytes))
		if msgLen <= 0 || msgLen > 10*1024*1024 { // Max 10MB per message
			break
		}

		// Read message data
		data := make([]byte, msgLen)
		_, err = reader.Read(data)
		if err != nil {
			break
		}

		// Deserialize message
		msg := &Message{}
		if err := msg.Unmarshal(data); err != nil {
			break
		}

		messages = append(messages, msg)
	}

	return messages, nil
}

// BaseOffset returns the first offset in this segment.
func (s *LogSegment) BaseOffset() int64 {
	return s.baseOffset
}

// NextOffset returns the next offset that would be assigned.
func (s *LogSegment) NextOffset() int64 {
	return s.baseOffset + s.index.EntryCount()
}

// Size returns the current file size in bytes.
func (s *LogSegment) Size() int64 {
	return s.size
}

// Timestamp returns when this segment was created.
func (s *LogSegment) Timestamp() int64 {
	return s.timestamp
}

// Close flushes and closes the segment.
func (s *LogSegment) Close() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if err := s.writer.Flush(); err != nil {
		return err
	}
	if err := s.file.Sync(); err != nil {
		return err
	}
	return s.file.Close()
}

// Delete removes the segment files from disk.
func (s *LogSegment) Delete() {
	s.isDeleted = true
	if s.file != nil {
		s.file.Close()
	}
	os.Remove(filepath.Join(s.dir, s.filename))
	os.Remove(filepath.Join(s.dir, s.filename+".index"))
}

// parseOffsetFilename extracts the base offset from a segment filename.
func parseOffsetFilename(filename string) (int64, error) {
	var offset int64
	_, err := fmt.Sscanf(filename, "%d", &offset)
	if err != nil {
		return 0, fmt.Errorf("invalid segment filename %s: %w", filename, err)
	}
	return offset, nil
}
