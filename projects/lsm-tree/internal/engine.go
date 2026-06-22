package internal

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"sync"
)

// LSMEngine is the main storage engine implementing the LSM Tree architecture.
//
// Write Path:
//   Write -> WAL -> MemTable -> (when full) Flush to SSTable
//
// Read Path:
//   Read -> MemTable -> SSTables (newest to oldest) -> return result
//
// Compaction:
//   Periodically merges SSTables to remove tombstones and obsolete versions.
type LSMEngine struct {
	mu       sync.RWMutex
	memTable *MemTable
	wal      *WAL
	sstables [][]*SSTable // sstables[level] = list of tables at that level
	dataDir  string
	nextID   int
}

// NewLSMEngine creates a new LSM Tree engine.
func NewLSMEngine(dataDir string, memTableSize int) (*LSMEngine, error) {
	// Create data directory if it doesn't exist
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		return nil, fmt.Errorf("engine: failed to create data dir: %w", err)
	}

	// Create WAL
	walPath := filepath.Join(dataDir, "wal.log")
	wal, err := NewWAL(walPath)
	if err != nil {
		return nil, fmt.Errorf("engine: failed to create WAL: %w", err)
	}

	// Create MemTable
	memTable := NewMemTable(memTableSize)

	// Replay WAL to recover MemTable
	if err := WALReplay(walPath, memTable); err != nil {
		return nil, fmt.Errorf("engine: WAL replay failed: %w", err)
	}

	// Load existing SSTables
	sstables := make([][]*SSTable, maxLevelCount)
	nextID := 0

	entries, err := os.ReadDir(dataDir)
	if err != nil {
		return nil, fmt.Errorf("engine: failed to read data dir: %w", err)
	}

	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".sst" {
			continue
		}
		path := filepath.Join(dataDir, entry.Name())
		table, err := OpenSSTable(path)
		if err != nil {
			continue // skip corrupted files
		}
		level := table.Level()
		if level < 0 || level >= maxLevelCount {
			level = 0
		}
		sstables[level] = append(sstables[level], table)

		// Parse ID from filename
		var id int
		if _, err := fmt.Sscanf(entry.Name(), "sstable_L%d_%d.sst", &level, &id); err == nil {
			if id >= nextID {
				nextID = id + 1
			}
		}
	}

	return &LSMEngine{
		memTable: memTable,
		wal:      wal,
		sstables: sstables,
		dataDir:  dataDir,
		nextID:   nextID,
	}, nil
}

// Put inserts or updates a key-value pair.
func (e *LSMEngine) Put(key, value []byte) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Write to WAL first for durability
	if err := e.wal.WritePut(key, value); err != nil {
		return fmt.Errorf("engine: WAL write failed: %w", err)
	}

	// Write to MemTable
	e.memTable.Put(key, value)

	// Check if MemTable needs flushing
	if e.memTable.ShouldFlush() {
		if err := e.flushMemTable(); err != nil {
			return fmt.Errorf("engine: flush failed: %w", err)
		}
	}

	return nil
}

// Get retrieves the value for a given key.
func (e *LSMEngine) Get(key []byte) ([]byte, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()

	// Search MemTable first (newest data)
	if val, found := e.memTable.Get(key); found {
		return val, nil
	}

	// Search SSTables from newest to oldest, level by level
	for level := 0; level < maxLevelCount; level++ {
		// Search from newest to oldest within each level
		for i := len(e.sstables[level]) - 1; i >= 0; i-- {
			table := e.sstables[level][i]
			val, found, err := table.Get(key)
			if err != nil {
				return nil, fmt.Errorf("engine: SSTable read error: %w", err)
			}
			if found {
				// Check if it's a tombstone
				if val == nil {
					return nil, nil // key was deleted
				}
				return val, nil
			}
		}
	}

	return nil, nil // key not found
}

// Delete marks a key as deleted.
func (e *LSMEngine) Delete(key []byte) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Write tombstone to WAL
	if err := e.wal.WriteDelete(key); err != nil {
		return fmt.Errorf("engine: WAL write failed: %w", err)
	}

	// Mark as deleted in MemTable
	e.memTable.Delete(key)

	// Check if MemTable needs flushing
	if e.memTable.ShouldFlush() {
		if err := e.flushMemTable(); err != nil {
			return fmt.Errorf("engine: flush failed: %w", err)
		}
	}

	return nil
}

// flushMemTable writes the current MemTable to an SSTable and creates a new MemTable.
func (e *LSMEngine) flushMemTable() error {
	entries := e.memTable.Entries()
	if len(entries) == 0 {
		return nil
	}

	// Build SSTable
	fileName := fmt.Sprintf("sstable_L0_%d.sst", e.nextID)
	filePath := filepath.Join(e.dataDir, fileName)
	e.nextID++

	builder := NewSSTableBuilder()
	for _, entry := range entries {
		builder.Add(entry.Key, entry.Value, entry.Deleted)
	}

	table, err := builder.Build(filePath, 0)
	if err != nil {
		return fmt.Errorf("engine: failed to build SSTable: %w", err)
	}

	e.sstables[0] = append(e.sstables[0], table)

	// Reset MemTable
	e.memTable = NewMemTable(e.memTable.sizeLimit)

	// Reset WAL
	e.wal.Close()
	walPath := filepath.Join(e.dataDir, "wal.log")
	RemoveWAL(walPath)
	wal, err := NewWAL(walPath)
	if err != nil {
		return fmt.Errorf("engine: failed to create new WAL: %w", err)
	}
	e.wal = wal

	// Trigger compaction if level 0 has too many tables
	if len(e.sstables[0]) >= level0MaxTables {
		if err := e.compactLevel(0); err != nil {
			return fmt.Errorf("engine: compaction failed: %w", err)
		}
	}

	return nil
}

// compactLevel performs compaction at the given level.
func (e *LSMEngine) compactLevel(level int) error {
	if level >= maxLevelCount-1 {
		return nil
	}

	tablesToCompact := e.sstables[level]
	if len(tablesToCompact) == 0 {
		return nil
	}

	// Also include any overlapping tables from the next level
	nextLevel := level + 1
	var overlappingNextLevel []*SSTable
	remaining := make([]*SSTable, 0, len(e.sstables[nextLevel]))

	if len(tablesToCompact) > 0 {
		// Find the key range of tables being compacted
		minKey, maxKey := e.getKeyRange(tablesToCompact)

		for _, table := range e.sstables[nextLevel] {
			if e.tableOverlaps(table, minKey, maxKey) {
				overlappingNextLevel = append(overlappingNextLevel, table)
			} else {
				remaining = append(remaining, table)
			}
		}
	}

	// Merge all tables
	allTables := append(tablesToCompact, overlappingNextLevel...)

	// Collect all entries
	merged := make(map[string]*Entry)
	for _, table := range allTables {
		iter, err := table.NewIterator()
		if err != nil {
			return err
		}
		for iter.Valid() {
			key := string(iter.Key())
			merged[key] = &Entry{
				Key:     iter.Key(),
				Value:   iter.Value(),
				Deleted: iter.IsDeleted(),
			}
			iter.Next()
		}
	}

	// Sort entries
	entries := make([]*Entry, 0, len(merged))
	for _, entry := range merged {
		if entry.Deleted && nextLevel >= maxLevelCount-1 {
			continue // remove tombstones at max level
		}
		entries = append(entries, entry)
	}
	sort.Slice(entries, func(i, j int) bool {
		return bytes.Compare(entries[i].Key, entries[j].Key) < 0
	})

	// Close and remove old tables
	for _, table := range allTables {
		table.Close()
		os.Remove(table.FilePath())
	}

	// Write merged entries to new SSTable(s)
	if len(entries) > 0 {
		fileName := fmt.Sprintf("sstable_L%d_%d.sst", nextLevel, e.nextID)
		filePath := filepath.Join(e.dataDir, fileName)
		e.nextID++

		builder := NewSSTableBuilder()
		for _, entry := range entries {
			builder.Add(entry.Key, entry.Value, entry.Deleted)
		}

		newTable, err := builder.Build(filePath, nextLevel)
		if err != nil {
			return err
		}
		remaining = append(remaining, newTable)
	}

	e.sstables[level] = nil
	e.sstables[nextLevel] = remaining

	return nil
}

// getKeyRange returns the min and max keys across all given tables.
func (e *LSMEngine) getKeyRange(tables []*SSTable) (minKey, maxKey []byte) {
	for _, table := range tables {
		iter, err := table.NewIterator()
		if err != nil {
			continue
		}
		if iter.Valid() {
			k := iter.Key()
			if minKey == nil || bytes.Compare(k, minKey) < 0 {
				minKey = make([]byte, len(k))
				copy(minKey, k)
			}
			// Find max key by iterating to the end
			lastKey := k
			for iter.Valid() {
				lastKey = iter.Key()
				iter.Next()
			}
			if maxKey == nil || bytes.Compare(lastKey, maxKey) > 0 {
				maxKey = make([]byte, len(lastKey))
				copy(maxKey, lastKey)
			}
		}
	}
	return
}

// tableOverlaps checks if a table's key range overlaps with [minKey, maxKey].
func (e *LSMEngine) tableOverlaps(table *SSTable, minKey, maxKey []byte) bool {
	iter, err := table.NewIterator()
	if err != nil {
		return false
	}
	if !iter.Valid() {
		return false
	}

	// Check if table's range overlaps with [minKey, maxKey]
	tableFirst := iter.Key()
	if bytes.Compare(tableFirst, maxKey) > 0 {
		return false
	}

	// Find table's last key
	lastKey := tableFirst
	for iter.Valid() {
		lastKey = iter.Key()
		iter.Next()
	}

	return bytes.Compare(lastKey, minKey) >= 0
}

// Close gracefully shuts down the engine.
func (e *LSMEngine) Close() error {
	e.mu.Lock()
	defer e.mu.Unlock()

	// Flush remaining MemTable
	if e.memTable.Size() > 0 {
		if err := e.flushMemTable(); err != nil {
			return fmt.Errorf("engine: final flush failed: %w", err)
		}
	}

	// Close WAL
	if err := e.wal.Close(); err != nil {
		return fmt.Errorf("engine: WAL close failed: %w", err)
	}

	// Close all SSTables
	for level := range e.sstables {
		for _, table := range e.sstables[level] {
			table.Close()
		}
	}

	return nil
}

// Stats returns statistics about the engine.
type EngineStats struct {
	MemTableSize int
	MemTableBytes int
	SSTableCount []int
}

// Stats returns current engine statistics.
func (e *LSMEngine) Stats() EngineStats {
	e.mu.RLock()
	defer e.mu.RUnlock()

	counts := make([]int, maxLevelCount)
	for level := range e.sstables {
		counts[level] = len(e.sstables[level])
	}

	return EngineStats{
		MemTableSize:  e.memTable.Size(),
		MemTableBytes: e.memTable.Bytes(),
		SSTableCount:  counts,
	}
}

// DataDir returns the data directory path.
func (e *LSMEngine) DataDir() string {
	return e.dataDir
}
