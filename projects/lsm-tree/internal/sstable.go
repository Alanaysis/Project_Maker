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

// SSTable (Sorted String Table) is the on-disk storage format for an LSM Tree.
//
// File format:
//   [data blocks]   - sorted key-value pairs
//   [index block]   - sparse index: every Nth key with its offset
//   [bloom filter]  - Bloom filter for fast negative lookups
//   [footer]        - metadata (see below)
//
// Each data entry: [key_len:4][key][val_len:4][value][deleted:1][crc32:4]
// Each index entry: [key_len:4][key][offset:8]
// Footer (40 bytes): [indexBlockOffset:8][bloomOffset:8][bloomLen:8][entryCount:8][indexCount:4][level:4]

const (
	indexInterval = 16 // every 16th key is indexed
)

// SSTable represents a sorted string table stored on disk.
type SSTable struct {
	filePath   string
	file       *os.File
	index      []*indexEntry
	bloom      *BloomFilter
	entryCount uint64
	level      int
	dataSize   uint64 // byte offset where data section ends (= index block starts)
}

// indexEntry maps a key to its byte offset in the data section.
type indexEntry struct {
	key    []byte
	offset uint64
}

// SSTableBuilder is used to construct an SSTable from sorted entries.
type SSTableBuilder struct {
	entries []*Entry
}

// NewSSTableBuilder creates a new builder.
func NewSSTableBuilder() *SSTableBuilder {
	return &SSTableBuilder{
		entries: make([]*Entry, 0),
	}
}

// Add appends an entry to the builder.
func (b *SSTableBuilder) Add(key, value []byte, deleted bool) {
	b.entries = append(b.entries, &Entry{
		Key:     key,
		Value:   value,
		Deleted: deleted,
	})
}

// Build writes the entries to an SSTable file.
func (b *SSTableBuilder) Build(filePath string, level int) (*SSTable, error) {
	// Sort entries by key
	sort.Slice(b.entries, func(i, j int) bool {
		return bytes.Compare(b.entries[i].Key, b.entries[j].Key) < 0
	})

	f, err := os.Create(filePath)
	if err != nil {
		return nil, fmt.Errorf("sstable: failed to create file: %w", err)
	}
	writer := bufio.NewWriter(f)

	var dataOffset uint64
	var indexEntries []*indexEntry

	// Build Bloom filter for non-deleted entries
	bloom := OptimalBloomFilter(uint64(len(b.entries)), 0.01)

	// Write data entries
	for i, entry := range b.entries {
		// Write key
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(entry.Key))); err != nil {
			f.Close()
			return nil, err
		}
		if _, err := writer.Write(entry.Key); err != nil {
			f.Close()
			return nil, err
		}

		// Write value
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(entry.Value))); err != nil {
			f.Close()
			return nil, err
		}
		if _, err := writer.Write(entry.Value); err != nil {
			f.Close()
			return nil, err
		}

		// Write deleted flag
		deletedByte := byte(0)
		if entry.Deleted {
			deletedByte = 1
		}
		if err := writer.WriteByte(deletedByte); err != nil {
			f.Close()
			return nil, err
		}

		// Calculate and write CRC32
		data := make([]byte, 0, len(entry.Key)+len(entry.Value)+1)
		data = append(data, entry.Key...)
		data = append(data, entry.Value...)
		data = append(data, deletedByte)
		checksum := crc32.ChecksumIEEE(data)
		if err := binary.Write(writer, binary.LittleEndian, checksum); err != nil {
			f.Close()
			return nil, err
		}

		// Add to Bloom filter (only non-deleted keys for efficiency)
		if !entry.Deleted {
			bloom.Add(entry.Key)
		}

		// Build sparse index: every indexInterval-th key
		if i%indexInterval == 0 {
			indexEntries = append(indexEntries, &indexEntry{
				key:    entry.Key,
				offset: dataOffset,
			})
		}

		// Calculate data offset: key_len(4) + key + val_len(4) + value + deleted(1) + crc(4)
		dataOffset += 4 + uint64(len(entry.Key)) + 4 + uint64(len(entry.Value)) + 1 + 4
	}

	// Record the start of the index block
	indexBlockOffset := dataOffset

	// Write index entries
	for _, ie := range indexEntries {
		if err := binary.Write(writer, binary.LittleEndian, uint32(len(ie.key))); err != nil {
			f.Close()
			return nil, err
		}
		if _, err := writer.Write(ie.key); err != nil {
			f.Close()
			return nil, err
		}
		if err := binary.Write(writer, binary.LittleEndian, ie.offset); err != nil {
			f.Close()
			return nil, err
		}
	}

	// Serialize and write Bloom filter
	bloomData := bloom.MarshalBinary()
	bloomOffset := indexBlockOffset + uint64(len(indexEntries))*(4+8) // approximate
	// Actually, we need the exact position after index block
	bloomOffset = dataOffset
	for _, ie := range indexEntries {
		bloomOffset += 4 + uint64(len(ie.key)) + 8
	}
	bloomLen := uint64(len(bloomData))

	if _, err := writer.Write(bloomData); err != nil {
		f.Close()
		return nil, err
	}

	// Write footer (40 bytes):
	// [indexBlockOffset:8][bloomOffset:8][bloomLen:8][entryCount:8][indexCount:4][level:4]
	if err := binary.Write(writer, binary.LittleEndian, indexBlockOffset); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Write(writer, binary.LittleEndian, bloomOffset); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Write(writer, binary.LittleEndian, bloomLen); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint64(len(b.entries))); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint32(len(indexEntries))); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Write(writer, binary.LittleEndian, uint32(level)); err != nil {
		f.Close()
		return nil, err
	}

	if err := writer.Flush(); err != nil {
		f.Close()
		return nil, err
	}
	if err := f.Sync(); err != nil {
		f.Close()
		return nil, err
	}
	f.Close()

	return OpenSSTable(filePath)
}

// OpenSSTable opens an existing SSTable file and reads its index and Bloom filter.
func OpenSSTable(filePath string) (*SSTable, error) {
	f, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("sstable: failed to open file: %w", err)
	}

	// Read footer (last 40 bytes):
	// [indexBlockOffset:8][bloomOffset:8][bloomLen:8][entryCount:8][indexCount:4][level:4]
	fileInfo, err := f.Stat()
	if err != nil {
		f.Close()
		return nil, err
	}
	fileSize := fileInfo.Size()
	if fileSize < 40 {
		f.Close()
		return nil, fmt.Errorf("sstable: file too small")
	}

	footerOffset := fileSize - 40
	if _, err := f.Seek(footerOffset, io.SeekStart); err != nil {
		f.Close()
		return nil, err
	}

	var indexBlockOffset uint64
	var bloomOffset uint64
	var bloomLen uint64
	var entryCount uint64
	var indexCount uint32
	var level uint32

	if err := binary.Read(f, binary.LittleEndian, &indexBlockOffset); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Read(f, binary.LittleEndian, &bloomOffset); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Read(f, binary.LittleEndian, &bloomLen); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Read(f, binary.LittleEndian, &entryCount); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Read(f, binary.LittleEndian, &indexCount); err != nil {
		f.Close()
		return nil, err
	}
	if err := binary.Read(f, binary.LittleEndian, &level); err != nil {
		f.Close()
		return nil, err
	}

	// Read index entries
	if _, err := f.Seek(int64(indexBlockOffset), io.SeekStart); err != nil {
		f.Close()
		return nil, err
	}

	reader := bufio.NewReader(f)
	index := make([]*indexEntry, 0, indexCount)
	for i := uint32(0); i < indexCount; i++ {
		var keyLen uint32
		if err := binary.Read(reader, binary.LittleEndian, &keyLen); err != nil {
			f.Close()
			return nil, err
		}
		key := make([]byte, keyLen)
		if _, err := io.ReadFull(reader, key); err != nil {
			f.Close()
			return nil, err
		}
		var offset uint64
		if err := binary.Read(reader, binary.LittleEndian, &offset); err != nil {
			f.Close()
			return nil, err
		}
		index = append(index, &indexEntry{key: key, offset: offset})
	}

	// Read Bloom filter
	var bloom *BloomFilter
	if bloomLen > 0 {
		if _, err := f.Seek(int64(bloomOffset), io.SeekStart); err != nil {
			f.Close()
			return nil, err
		}
		bloomData := make([]byte, bloomLen)
		if _, err := io.ReadFull(f, bloomData); err != nil {
			f.Close()
			return nil, err
		}
		bloom = UnmarshalBloomFilter(bloomData)
	}

	return &SSTable{
		filePath:   filePath,
		file:       f,
		index:      index,
		bloom:      bloom,
		entryCount: entryCount,
		level:      int(level),
		dataSize:   indexBlockOffset,
	}, nil
}

// Get searches for a key in the SSTable using the Bloom filter and sparse index.
// First checks the Bloom filter to quickly reject keys that are definitely not present.
func (s *SSTable) Get(key []byte) ([]byte, bool, error) {
	// Use Bloom filter for fast negative lookup
	if s.bloom != nil && !s.bloom.Contains(key) {
		return nil, false, nil // definitely not in this SSTable
	}

	// Find the rightmost index entry whose key <= target key
	startOffset := uint64(0)
	for i := len(s.index) - 1; i >= 0; i-- {
		if bytes.Compare(s.index[i].key, key) <= 0 {
			startOffset = s.index[i].offset
			break
		}
	}

	// Use a SectionReader limited to the data section to prevent reading past it
	sectionReader := io.NewSectionReader(s.file, int64(startOffset), int64(s.dataSize-startOffset))
	reader := bufio.NewReader(sectionReader)

	for {
		rec, err := readSSTableEntry(reader)
		if err != nil {
			if err == io.EOF || err == io.ErrUnexpectedEOF {
				break
			}
			return nil, false, err
		}

		cmp := bytes.Compare(rec.Key, key)
		if cmp == 0 {
			return rec.Value, !rec.Deleted, nil
		}
		if cmp > 0 {
			break
		}
	}

	return nil, false, nil
}

// Close closes the SSTable file.
func (s *SSTable) Close() error {
	return s.file.Close()
}

// FilePath returns the path of the SSTable file.
func (s *SSTable) FilePath() string {
	return s.filePath
}

// EntryCount returns the number of entries in the SSTable.
func (s *SSTable) EntryCount() uint64 {
	return s.entryCount
}

// Level returns the compaction level of this SSTable.
func (s *SSTable) Level() int {
	return s.level
}

// BloomFilter returns the Bloom filter of this SSTable, or nil if not present.
func (s *SSTable) BloomFilter() *BloomFilter {
	return s.bloom
}

// readSSTableEntry reads a single data entry from the SSTable.
func readSSTableEntry(reader *bufio.Reader) (*Entry, error) {
	// Read key
	var keyLen uint32
	if err := binary.Read(reader, binary.LittleEndian, &keyLen); err != nil {
		return nil, err
	}
	key := make([]byte, keyLen)
	if _, err := io.ReadFull(reader, key); err != nil {
		return nil, err
	}

	// Read value
	var valLen uint32
	if err := binary.Read(reader, binary.LittleEndian, &valLen); err != nil {
		return nil, err
	}
	value := make([]byte, valLen)
	if _, err := io.ReadFull(reader, value); err != nil {
		return nil, err
	}

	// Read deleted flag
	deletedByte, err := reader.ReadByte()
	if err != nil {
		return nil, err
	}
	deleted := deletedByte == 1

	// Read and verify CRC32
	var storedCRC uint32
	if err := binary.Read(reader, binary.LittleEndian, &storedCRC); err != nil {
		return nil, err
	}
	data := make([]byte, 0, len(key)+len(value)+1)
	data = append(data, key...)
	data = append(data, value...)
	data = append(data, deletedByte)
	if crc32.ChecksumIEEE(data) != storedCRC {
		return nil, fmt.Errorf("sstable: CRC mismatch for key %s", key)
	}

	return &Entry{
		Key:     key,
		Value:   value,
		Deleted: deleted,
	}, nil
}

// SSTableIterator iterates over all entries in an SSTable in sorted order.
type SSTableIterator struct {
	reader  *bufio.Reader
	current *Entry
	err     error
}

// NewIterator creates a new iterator over the SSTable entries.
func (s *SSTable) NewIterator() (*SSTableIterator, error) {
	// Use a SectionReader limited to the data section
	sectionReader := io.NewSectionReader(s.file, 0, int64(s.dataSize))
	reader := bufio.NewReader(sectionReader)

	// Read first entry
	entry, err := readSSTableEntry(reader)
	if err != nil {
		if err == io.EOF || err == io.ErrUnexpectedEOF {
			return &SSTableIterator{reader: reader, current: nil}, nil
		}
		return nil, err
	}

	return &SSTableIterator{
		reader:  reader,
		current: entry,
	}, nil
}

// Valid returns true if the iterator is at a valid position.
func (it *SSTableIterator) Valid() bool {
	return it.current != nil
}

// Next advances the iterator.
func (it *SSTableIterator) Next() {
	entry, err := readSSTableEntry(it.reader)
	if err != nil {
		it.current = nil
		if err != io.EOF && err != io.ErrUnexpectedEOF {
			it.err = err
		}
		return
	}
	it.current = entry
}

// Key returns the current key.
func (it *SSTableIterator) Key() []byte {
	if it.current != nil {
		return it.current.Key
	}
	return nil
}

// Value returns the current value.
func (it *SSTableIterator) Value() []byte {
	if it.current != nil {
		return it.current.Value
	}
	return nil
}

// IsDeleted returns true if the current entry is a tombstone.
func (it *SSTableIterator) IsDeleted() bool {
	return it.current != nil && it.current.Deleted
}

// Error returns any error encountered during iteration.
func (it *SSTableIterator) Error() error {
	return it.err
}
