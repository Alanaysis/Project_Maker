package internal

// Entry represents a key-value pair with metadata.
type Entry struct {
	Key     []byte
	Value   []byte
	Deleted bool
}

// MemTable is an in-memory write buffer backed by a skip list.
// When it reaches a size threshold, it is flushed to an SSTable on disk.
type MemTable struct {
	skiplist  *SkipList
	sizeLimit int
}

// NewMemTable creates a new MemTable with the given size limit in bytes.
func NewMemTable(sizeLimit int) *MemTable {
	return &MemTable{
		skiplist:  NewSkipList(),
		sizeLimit: sizeLimit,
	}
}

// Put inserts or updates a key-value pair.
func (m *MemTable) Put(key, value []byte) {
	m.skiplist.Insert(key, value)
}

// Get retrieves the value for a given key.
func (m *MemTable) Get(key []byte) ([]byte, bool) {
	return m.skiplist.Get(key)
}

// Delete marks a key as deleted by inserting a tombstone.
func (m *MemTable) Delete(key []byte) bool {
	return m.skiplist.Delete(key)
}

// Entries returns all entries in sorted order.
func (m *MemTable) Entries() []*Entry {
	return m.skiplist.Entries()
}

// Size returns the number of entries.
func (m *MemTable) Size() int {
	return m.skiplist.Size()
}

// Bytes returns the approximate memory usage.
func (m *MemTable) Bytes() int {
	return m.skiplist.Bytes()
}

// ShouldFlush returns true if the MemTable has reached its size limit.
func (m *MemTable) ShouldFlush() bool {
	return m.Bytes() >= m.sizeLimit
}

// NewIterator creates a new iterator over the MemTable entries.
func (m *MemTable) NewIterator() *SkipListIterator {
	return m.skiplist.NewIterator()
}
