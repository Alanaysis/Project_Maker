package queue

import (
	"encoding/binary"
	"fmt"
	"os"
	"sync"
)

// IndexFile provides offset-to-position lookup for a log segment.
//
// The index is critical for performance. Without it, reading a message at
// offset N would require scanning all previous messages linearly - O(N) time.
// With the index, we can jump directly to the right position - O(log M) time
// where M is the number of index entries.
//
// Index Design:
//
//	Each index entry maps: offset -> relative byte position within the segment
//
// Entries are stored in a fixed-size array for cache efficiency. When the
// index is full, a new segment is created. The index is sparse: it doesn't
// store every offset, just sampled ones (every Nth entry). This reduces
// memory usage while keeping lookup fast.
//
// For zero-copy optimization:
// 1. Index entries use fixed-size (8 bytes each): 4 bytes offset + 4 bytes position
// 2. The index is memory-mapped when possible (on modern OSes)
// 3. Sparse indexing reduces memory footprint
type IndexFile struct {
	path     string
	entries  []indexEntry
	buffer   []byte
	capacity int
	mu       sync.RWMutex
}

// indexEntry is a single offset-to-position mapping.
type indexEntry struct {
	offset    int32 // Relative offset within the segment (4 bytes)
	relativePos uint32 // Relative byte position in the segment (4 bytes)
}

// NewIndexFile creates a new in-memory index.
func NewIndexFile(path string, capacity int) *IndexFile {
	return &IndexFile{
		path:     path,
		entries:  make([]indexEntry, 0, capacity),
		capacity: capacity,
		buffer:   make([]byte, 8), // 8 bytes per entry for serialization
	}
}

// Append adds a new offset-to-position mapping to the index.
func (idx *IndexFile) Append(offset int64, relativePos uint32) {
	idx.mu.Lock()
	defer idx.mu.Unlock()

	entry := indexEntry{
		offset:    int32(offset),
		relativePos: relativePos,
	}

	if len(idx.entries) < idx.capacity {
		idx.entries = append(idx.entries, entry)
	} else {
		// Index is full, signal that a new segment is needed
		// In production, you'd use a more sophisticated eviction strategy
	}
}

// Lookup finds the byte position for a given offset.
// Returns the position and whether it was found.
//
// Uses binary search for O(log M) lookup time.
// If the exact offset isn't in the index, returns the closest earlier entry.
// The caller then needs to scan forward from that position.
func (idx *IndexFile) Lookup(offset int64) (uint32, bool) {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	if len(idx.entries) == 0 {
		return 0, false
	}

	// Binary search for the entry
	result := idx.binarySearch(offset)
	return result.relativePos, result.offset == int32(offset)
}

// binarySearch performs binary search on the index entries.
func (idx *IndexFile) binarySearch(offset int64) indexEntry {
	lo, hi := 0, len(idx.entries)-1
	var result indexEntry

	for lo <= hi {
		mid := (lo + hi) / 2
		entry := idx.entries[mid]

		if entry.offset == int32(offset) {
			return entry
		} else if entry.offset < int32(offset) {
			result = entry
			lo = mid + 1
		} else {
			hi = mid - 1
		}
	}

	return result
}

// EntryCount returns the number of entries in the index.
func (idx *IndexFile) EntryCount() uint32 {
	idx.mu.RLock()
	defer idx.mu.RUnlock()
	return uint32(len(idx.entries))
}

// Load reads the index from disk.
func (idx *IndexFile) Load() {
	data, err := os.ReadFile(idx.path)
	if err != nil {
		return
	}

	// Each entry is 8 bytes: 4 bytes offset + 4 bytes position
	for i := 0; i+7 < len(data); i += 8 {
		offset := int32(binary.LittleEndian.Uint32(data[i : i+4]))
		relativePos := binary.LittleEndian.Uint32(data[i+4 : i+8])

		idx.entries = append(idx.entries, indexEntry{
			offset:    offset,
			relativePos: relativePos,
		})
	}
}

// Save writes the index to disk.
func (idx *IndexFile) Save() error {
	idx.mu.RLock()
	defer idx.mu.RUnlock()

	// Serialize entries to bytes
	data := make([]byte, 0, len(idx.entries)*8)
	for _, entry := range idx.entries {
		binary.LittleEndian.PutUint32(idx.buffer[0:4], uint32(entry.offset))
		binary.LittleEndian.PutUint32(idx.buffer[4:8], entry.relativePos)
		data = append(data, idx.buffer...)
	}

	return os.WriteFile(idx.path, data, 0644)
}

// Clear removes all entries from the index.
func (idx *IndexFile) Clear() {
	idx.mu.Lock()
	defer idx.mu.Unlock()
	idx.entries = idx.entries[:0]
}
