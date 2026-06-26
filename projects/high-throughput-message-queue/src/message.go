package queue

import (
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"time"
)

// Message represents a single message in the queue.
//
// Messages are the fundamental unit of data in a message queue. Each message
// consists of:
//   - Key: Optional partitioning key (messages with same key go to same partition)
//   - Value: The actual payload bytes
//   - Headers: Metadata for routing, filtering, etc.
//   - Timestamp: When the message was produced
//   - Offset: Assigned by the broker at write time
//   - Partition: The partition this message belongs to
//
// For high throughput, messages are batched together and written as a single
// I/O operation. This reduces the number of system calls and disk seeks.
type Message struct {
	Key       []byte      // Partitioning key (nil = use round-robin)
	Value     []byte      // Message payload
	Headers   map[string]string // Custom metadata
	Timestamp int64       // Unix nanosecond timestamp
	Offset    int64       // Assigned offset in partition
	Partition int         // Partition ID
	Checksum  uint32      // CRC32 checksum for integrity
}

// NewMessage creates a new message with the given key and value.
func NewMessage(key, value []byte) *Message {
	return &Message{
		Key:       key,
		Value:     value,
		Headers:   make(map[string]string),
		Timestamp: time.Now().UnixNano(),
		Offset:    -1,
		Partition: -1,
	}
}

// WithHeader adds a header to the message.
func (m *Message) WithHeader(key, value string) *Message {
	m.Headers[key] = value
	return m
}

// Checksum calculates CRC32 checksum over key and value.
func (m *Message) Checksum() uint32 {
	h := crc32.NewIEEE()
	if m.Key != nil {
		h.Write(m.Key)
	}
	h.Write(m.Value)
	return h.Sum32()
}

// SizeEstimate returns an approximate size of this message in bytes.
// Used for batching and segment size calculations.
func (m *Message) SizeEstimate() int {
	size := len(m.Value) + 8 // value length + value
	if m.Key != nil {
		size += len(m.Key) + 8 // key length + key
	}
	size += 8  // timestamp
	size += 8  // offset
	size += 4  // partition
	size += 4  // checksum
	size += 4  // headers count
	for k, v := range m.Headers {
		size += len(k) + len(v) + 8
	}
	return size
}

// Marshal serializes the message to bytes for storage.
//
// Wire format:
//
//	+--------+--------+--------+--------+--------+--------+--------+--------+
//	| KeyLen (4 bytes) | Key (variable) | ValueLen (4 bytes) | Value (variable) |
//	+--------+--------+--------+--------+--------+--------+--------+--------+
//	| Timestamp (8 bytes) | Offset (8 bytes) | Partition (4 bytes) | Checksum (4 bytes) |
//	+--------+--------+--------+--------+--------+--------+--------+--------+
//	| HeadersCount (4 bytes) | Header pairs (keyLen+key+valLen+val) |
//	+--------+--------+--------+--------+--------+--------+--------+--------+
//
// For zero-copy optimization, we avoid unnecessary allocations by:
// 1. Pre-allocating buffer sizes when possible
// 2. Using binary.Write for primitive types
// 3. Minimizing intermediate allocations
func (m *Message) Marshal() ([]byte, error) {
	// Calculate total size first
	keyLen := len(m.Key)
	valueLen := len(m.Value)
	headersSize := 4 // headers count
	for k, v := range m.Headers {
		headersSize += 4 + len(k) + 4 + len(v)
	}

	totalSize := 4 + keyLen + 4 + valueLen + 8 + 8 + 4 + 4 + headersSize
	buf := make([]byte, totalSize)

	// Write key length and key
	binary.LittleEndian.PutUint32(buf[0:4], uint32(keyLen))
	if keyLen > 0 {
		copy(buf[4:4+keyLen], m.Key)
	}

	// Write value length and value
	offset := 4 + keyLen
	binary.LittleEndian.PutUint32(buf[offset:offset+4], uint32(valueLen))
	offset += 4
	copy(buf[offset:offset+valueLen], m.Value)
	offset += valueLen

	// Write timestamp
	binary.LittleEndian.PutUint64(buf[offset:offset+8], uint64(m.Timestamp))
	offset += 8

	// Write offset
	binary.LittleEndian.PutUint64(buf[offset:offset+8], uint64(m.Offset))
	offset += 8

	// Write partition
	binary.LittleEndian.PutUint32(buf[offset:offset+4], uint32(m.Partition))
	offset += 4

	// Write checksum
	binary.LittleEndian.PutUint32(buf[offset:offset+4], m.Checksum)
	offset += 4

	// Write headers
	binary.LittleEndian.PutUint32(buf[offset:offset+4], uint32(len(m.Headers)))
	offset += 4
	for k, v := range m.Headers {
		binary.LittleEndian.PutUint32(buf[offset:offset+4], uint32(len(k)))
		offset += 4
		copy(buf[offset:offset+len(k)], k)
		offset += len(k)
		binary.LittleEndian.PutUint32(buf[offset:offset+4], uint32(len(v)))
		offset += 4
		copy(buf[offset:offset+len(v)], v)
		offset += len(v)
	}

	return buf, nil
}

// Unmarshal deserializes a message from bytes.
func (m *Message) Unmarshal(data []byte) error {
	if len(data) < 4 {
		return fmt.Errorf("data too short")
	}

	offset := 0

	// Read key length
	keyLen := int(binary.LittleEndian.Uint32(data[offset : offset+4]))
	offset += 4

	// Read key
	if keyLen > 0 {
		if len(data) < offset+keyLen {
			return fmt.Errorf("insufficient data for key")
		}
		m.Key = make([]byte, keyLen)
		copy(m.Key, data[offset:offset+keyLen])
		offset += keyLen
	}

	// Read value length
	if len(data) < offset+4 {
		return fmt.Errorf("insufficient data for value length")
	}
	valueLen := int(binary.LittleEndian.Uint32(data[offset : offset+4]))
	offset += 4

	// Read value
	if len(data) < offset+valueLen {
		return fmt.Errorf("insufficient data for value")
	}
	m.Value = make([]byte, valueLen)
	copy(m.Value, data[offset:offset+valueLen])
	offset += valueLen

	// Read timestamp
	if len(data) < offset+8 {
		return fmt.Errorf("insufficient data for timestamp")
	}
	m.Timestamp = int64(binary.LittleEndian.Uint64(data[offset : offset+8]))
	offset += 8

	// Read offset
	if len(data) < offset+8 {
		return fmt.Errorf("insufficient data for offset")
	}
	m.Offset = int64(binary.LittleEndian.Uint64(data[offset : offset+8]))
	offset += 8

	// Read partition
	if len(data) < offset+4 {
		return fmt.Errorf("insufficient data for partition")
	}
	m.Partition = int(binary.LittleEndian.Uint32(data[offset : offset+4]))
	offset += 4

	// Read checksum
	if len(data) < offset+4 {
		return fmt.Errorf("insufficient data for checksum")
	}
	m.Checksum = binary.LittleEndian.Uint32(data[offset : offset+4])
	offset += 4

	// Read headers
	if len(data) < offset+4 {
		return fmt.Errorf("insufficient data for headers count")
	}
	headersCount := int(binary.LittleEndian.Uint32(data[offset : offset+4]))
	offset += 4

	m.Headers = make(map[string]string, headersCount)
	for i := 0; i < headersCount; i++ {
		if len(data) < offset+4 {
			return fmt.Errorf("insufficient data for header key length")
		}
		keyLen := int(binary.LittleEndian.Uint32(data[offset : offset+4]))
		offset += 4

		if len(data) < offset+keyLen {
			return fmt.Errorf("insufficient data for header key")
		}
		key := string(data[offset : offset+keyLen])
		offset += keyLen

		if len(data) < offset+4 {
			return fmt.Errorf("insufficient data for header value length")
		}
		valLen := int(binary.LittleEndian.Uint32(data[offset : offset+4]))
		offset += 4

		if len(data) < offset+valLen {
			return fmt.Errorf("insufficient data for header value")
		}
		value := string(data[offset : offset+valLen])
		offset += valLen

		m.Headers[key] = value
	}

	return nil
}
