package internal

import (
	"bufio"
	"bytes"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"io"
	"os"
	"sort"
)

// Compaction merges multiple SSTables into fewer, larger SSTables.
// This process removes tombstones and obsolete versions of keys,
// reclaiming disk space and improving read performance.
//
// Leveled Compaction Strategy:
//   - Level 0: SSTables flushed from MemTable (may have overlapping key ranges)
//   - Level 1+: Non-overlapping SSTables sorted by key range
//   - When a level is full, its SSTables are merged into the next level

const (
	maxLevelCount    = 7
	level0MaxTables  = 4
	levelSizeMultiple = 10
)

// Compactor handles the compaction process.
type Compactor struct {
	dataDir string
}

// NewCompactor creates a new compactor for the given data directory.
func NewCompactor(dataDir string) *Compactor {
	return &Compactor{dataDir: dataDir}
}

// CompactLevel performs compaction on SSTables at the given level.
// It selects overlapping SSTables from the current level and merges them
// with overlapping SSTables from the next level.
func (c *Compactor) CompactLevel(tables []*SSTable, level int) ([]*SSTable, error) {
	if len(tables) == 0 {
		return tables, nil
	}

	// Collect all entries from the tables being compacted
	merged := make(map[string]*Entry)
	for _, table := range tables {
		iter, err := table.NewIterator()
		if err != nil {
			return nil, fmt.Errorf("compaction: failed to create iterator: %w", err)
		}
		for iter.Valid() {
			key := string(iter.Key())
			// Last writer wins (tables are ordered newest to oldest)
			if _, exists := merged[key]; !exists {
				merged[key] = &Entry{
					Key:     iter.Key(),
					Value:   iter.Value(),
					Deleted: iter.IsDeleted(),
				}
			}
			iter.Next()
		}
		if err := iter.Error(); err != nil {
			return nil, fmt.Errorf("compaction: iteration error: %w", err)
		}
	}

	// Filter out tombstones at the highest level (no older versions exist)
	filtered := make([]*Entry, 0, len(merged))
	for _, entry := range merged {
		if entry.Deleted && level >= maxLevelCount-1 {
			continue // discard tombstone at max level
		}
		filtered = append(filtered, entry)
	}

	// Sort entries by key
	sort.Slice(filtered, func(i, j int) bool {
		return bytes.Compare(filtered[i].Key, filtered[j].Key) < 0
	})

	// Write merged entries to a new SSTable
	if len(filtered) == 0 {
		return nil, nil
	}

	outputPath := fmt.Sprintf("%s/sstable_L%d_0.sst", c.dataDir, level+1)
	builder := NewSSTableBuilder()
	for _, entry := range filtered {
		builder.Add(entry.Key, entry.Value, entry.Deleted)
	}

	newTable, err := builder.Build(outputPath, level+1)
	if err != nil {
		return nil, fmt.Errorf("compaction: failed to build merged table: %w", err)
	}

	// Close and remove old tables
	for _, table := range tables {
		table.Close()
		os.Remove(table.FilePath())
	}

	return []*SSTable{newTable}, nil
}

// Compact performs a simple compaction: merge all given tables into one.
func Compact(tables []*SSTable, outputPath string, level int) (*SSTable, error) {
	// Merge all entries
	merged := make(map[string]*Entry)

	for _, table := range tables {
		iter, err := table.NewIterator()
		if err != nil {
			return nil, fmt.Errorf("compaction: failed to create iterator: %w", err)
		}
		for iter.Valid() {
			key := string(iter.Key())
			// Last writer wins
			merged[key] = &Entry{
				Key:     iter.Key(),
				Value:   iter.Value(),
				Deleted: iter.IsDeleted(),
			}
			iter.Next()
		}
		if err := iter.Error(); err != nil {
			return nil, fmt.Errorf("compaction: iteration error: %w", err)
		}
	}

	// Sort and build
	entries := make([]*Entry, 0, len(merged))
	for _, entry := range merged {
		// Remove tombstones at max level
		if entry.Deleted && level >= maxLevelCount-1 {
			continue
		}
		entries = append(entries, entry)
	}

	sort.Slice(entries, func(i, j int) bool {
		return bytes.Compare(entries[i].Key, entries[j].Key) < 0
	})

	if len(entries) == 0 {
		return nil, nil
	}

	builder := NewSSTableBuilder()
	for _, entry := range entries {
		builder.Add(entry.Key, entry.Value, entry.Deleted)
	}

	return builder.Build(outputPath, level)
}

// MergeIterator merges multiple sorted iterators into a single sorted stream.
type MergeIterator struct {
	iters   []SSTIterator
	entries []*Entry
	current *Entry
}

// SSTIterator is a common interface for SSTable and SkipList iterators.
type SSTIterator interface {
	Valid() bool
	Next()
	Key() []byte
	Value() []byte
	IsDeleted() bool
}

// NewMergeIterator creates a merge iterator from multiple SSTIterators.
func NewMergeIterator(iters []SSTIterator) *MergeIterator {
	mi := &MergeIterator{
		iters:   iters,
		entries: make([]*Entry, len(iters)),
	}
	// Initialize: read first entry from each iterator
	for i, iter := range iters {
		if iter.Valid() {
			mi.entries[i] = &Entry{
				Key:     iter.Key(),
				Value:   iter.Value(),
				Deleted: iter.IsDeleted(),
			}
		}
	}
	return mi
}

// Valid returns true if the merge iterator has more entries.
func (mi *MergeIterator) Valid() bool {
	for _, entry := range mi.entries {
		if entry != nil {
			return true
		}
	}
	return false
}

// Next advances the merge iterator and returns the next entry in sorted order.
// For duplicate keys, the entry from the earliest (highest priority) iterator wins.
func (mi *MergeIterator) Next() *Entry {
	var minKey []byte
	minIdx := -1

	// Find the smallest key across all iterators
	for i, entry := range mi.entries {
		if entry == nil {
			continue
		}
		if minIdx == -1 || bytes.Compare(entry.Key, minKey) < 0 {
			minKey = entry.Key
			minIdx = i
		}
	}

	if minIdx == -1 {
		mi.current = nil
		return nil
	}

	result := mi.entries[minIdx]

	// Advance the iterator that provided this entry
	mi.iters[minIdx].Next()
	if mi.iters[minIdx].Valid() {
		mi.entries[minIdx] = &Entry{
			Key:     mi.iters[minIdx].Key(),
			Value:   mi.iters[minIdx].Value(),
			Deleted: mi.iters[minIdx].IsDeleted(),
		}
	} else {
		mi.entries[minIdx] = nil
	}

	// Skip duplicate keys from other iterators (they lose)
	for i, entry := range mi.entries {
		if entry == nil || i == minIdx {
			continue
		}
		if bytes.Equal(entry.Key, result.Key) {
			// Discard this entry (lower priority)
			mi.iters[i].Next()
			if mi.iters[i].Valid() {
				mi.entries[i] = &Entry{
					Key:     mi.iters[i].Key(),
					Value:   mi.iters[i].Value(),
					Deleted: mi.iters[i].IsDeleted(),
				}
			} else {
				mi.entries[i] = nil
			}
		}
	}

	mi.current = result
	return result
}

// readSSTableEntries reads all entries from an SSTable file (utility function).
func readSSTableEntries(filePath string) ([]*Entry, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	// Read footer to get data section size
	fileInfo, err := f.Stat()
	if err != nil {
		return nil, err
	}
	fileSize := fileInfo.Size()
	if fileSize < 32 {
		return nil, nil
	}
	if _, err := f.Seek(fileSize-32, io.SeekStart); err != nil {
		return nil, err
	}
	var indexBlockOffset uint64
	if err := binary.Read(f, binary.LittleEndian, &indexBlockOffset); err != nil {
		return nil, err
	}

	// Read entries using SectionReader limited to data section
	f.Seek(0, io.SeekStart)
	sectionReader := io.NewSectionReader(f, 0, int64(indexBlockOffset))
	reader := bufio.NewReader(sectionReader)

	var entries []*Entry
	for {
		rec, err := readSSTableEntry(reader)
		if err != nil {
			if err == io.EOF || err == io.ErrUnexpectedEOF {
				break
			}
			return nil, err
		}
		entries = append(entries, rec)
	}
	return entries, nil
}

// writeSSTableEntries writes sorted entries to an SSTable file (utility function).
func writeSSTableEntries(filePath string, entries []*Entry, level int) error {
	f, err := os.Create(filePath)
	if err != nil {
		return err
	}
	writer := bufio.NewWriter(f)

	var dataOffset uint64
	var indexEntries []*indexEntry

	for i, entry := range entries {
		// Write key
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(entry.Key))); err != nil {
			f.Close()
			return err
		}
		if _, err := writer.Write(entry.Key); err != nil {
			f.Close()
			return err
		}

		// Write value
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(entry.Value))); err != nil {
			f.Close()
			return err
		}
		if _, err := writer.Write(entry.Value); err != nil {
			f.Close()
			return err
		}

		// Write deleted flag
		deletedByte := byte(0)
		if entry.Deleted {
			deletedByte = 1
		}
		if err := writer.WriteByte(deletedByte); err != nil {
			f.Close()
			return err
		}

		// CRC
		data := make([]byte, 0, len(entry.Key)+len(entry.Value)+1)
		data = append(data, entry.Key...)
		data = append(data, entry.Value...)
		data = append(data, deletedByte)
		checksum := crc32.ChecksumIEEE(data)
		if err := binary.Write(writer, binary.LittleEndian, checksum); err != nil {
			f.Close()
			return err
		}

		if i%indexInterval == 0 {
			indexEntries = append(indexEntries, &indexEntry{
				key:    entry.Key,
				offset: dataOffset,
			})
		}
		dataOffset += 4 + uint64(len(entry.Key)) + 4 + uint64(len(entry.Value)) + 1 + 4
	}

	// Index block offset
	indexBlockOffset := dataOffset
	for _, ie := range indexEntries {
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(ie.key))); err != nil {
			f.Close()
			return err
		}
		if _, err := writer.Write(ie.key); err != nil {
			f.Close()
			return err
		}
		if err := binary.Write(writer, binary.LittleEndian, ie.offset); err != nil {
			f.Close()
			return err
		}
	}

	// Footer
	if err := binary.Write(writer, binary.LittleEndian, indexBlockOffset); err != nil {
		f.Close()
		return err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint64(len(entries))); err != nil {
		f.Close()
		return err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint64(len(indexEntries))); err != nil {
		f.Close()
		return err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint64(level)); err != nil {
		f.Close()
		return err
	}

	if err := writer.Flush(); err != nil {
		f.Close()
		return err
	}
	if err := f.Sync(); err != nil {
		f.Close()
		return err
	}
	return f.Close()
}
