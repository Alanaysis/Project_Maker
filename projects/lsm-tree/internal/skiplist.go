package internal

import (
	"bytes"
	"math/rand"
)

const (
	maxLevel = 16
	p        = 0.5
)

// SkipListNode represents a node in the skip list.
type SkipListNode struct {
	key     []byte
	value   []byte
	deleted bool
	next    []*SkipListNode
}

// SkipList is a probabilistic data structure used as the in-memory component (MemTable) of an LSM Tree.
// It provides O(log N) search, insert, and delete operations.
type SkipList struct {
	head  *SkipListNode
	level int
	size  int
	bytes int
}

// NewSkipList creates a new empty skip list.
func NewSkipList() *SkipList {
	head := &SkipListNode{
		next: make([]*SkipListNode, maxLevel),
	}
	return &SkipList{
		head:  head,
		level: 0,
		size:  0,
		bytes: 0,
	}
}

// randomLevel generates a random level for a new node.
func randomLevel() int {
	lvl := 0
	for rand.Float64() < p && lvl < maxLevel-1 {
		lvl++
	}
	return lvl
}

// Insert adds a key-value pair to the skip list.
// If the key already exists, its value is updated.
func (s *SkipList) Insert(key, value []byte) {
	// update[i] holds the node at level i whose next pointer needs updating
	update := make([]*SkipListNode, maxLevel)
	current := s.head

	// Traverse from the highest level down to find insertion position
	for i := s.level; i >= 0; i-- {
		for current.next[i] != nil && bytes.Compare(current.next[i].key, key) < 0 {
			current = current.next[i]
		}
		update[i] = current
	}

	// Move to the lowest level
	current = current.next[0]

	// If key exists, update value
	if current != nil && bytes.Equal(current.key, key) {
		oldSize := len(current.value)
		current.value = value
		current.deleted = false
		s.bytes += len(value) - oldSize
		return
	}

	// Generate random level for new node
	newLevel := randomLevel()
	if newLevel > s.level {
		for i := s.level + 1; i <= newLevel; i++ {
			update[i] = s.head
		}
		s.level = newLevel
	}

	// Create new node
	newNode := &SkipListNode{
		key:   key,
		value: value,
		next:  make([]*SkipListNode, newLevel+1),
	}

	// Update pointers at each level
	for i := 0; i <= newLevel; i++ {
		newNode.next[i] = update[i].next[i]
		update[i].next[i] = newNode
	}

	s.size++
	s.bytes += len(key) + len(value)
}

// Get retrieves the value for a given key.
// Returns the value and true if found, nil and false otherwise.
func (s *SkipList) Get(key []byte) ([]byte, bool) {
	current := s.head

	for i := s.level; i >= 0; i-- {
		for current.next[i] != nil && bytes.Compare(current.next[i].key, key) < 0 {
			current = current.next[i]
		}
	}

	current = current.next[0]
	if current != nil && bytes.Equal(current.key, key) && !current.deleted {
		return current.value, true
	}
	return nil, false
}

// Delete marks a key as deleted (tombstone).
func (s *SkipList) Delete(key []byte) bool {
	current := s.head

	for i := s.level; i >= 0; i-- {
		for current.next[i] != nil && bytes.Compare(current.next[i].key, key) < 0 {
			current = current.next[i]
		}
	}

	current = current.next[0]
	if current != nil && bytes.Equal(current.key, key) {
		current.deleted = true
		return true
	}
	return false
}

// Entries returns all entries in sorted order.
func (s *SkipList) Entries() []*Entry {
	entries := make([]*Entry, 0, s.size)
	current := s.head.next[0]
	for current != nil {
		entries = append(entries, &Entry{
			Key:     current.key,
			Value:   current.value,
			Deleted: current.deleted,
		})
		current = current.next[0]
	}
	return entries
}

// Size returns the number of entries in the skip list.
func (s *SkipList) Size() int {
	return s.size
}

// Bytes returns the approximate memory usage in bytes.
func (s *SkipList) Bytes() int {
	return s.bytes
}

// Iterator provides ordered iteration over skip list entries.
type SkipListIterator struct {
	current *SkipListNode
}

// NewIterator creates a new iterator starting from the first entry.
func (s *SkipList) NewIterator() *SkipListIterator {
	return &SkipListIterator{
		current: s.head.next[0],
	}
}

// Valid returns true if the iterator is at a valid position.
func (it *SkipListIterator) Valid() bool {
	return it.current != nil
}

// Next advances the iterator to the next entry.
func (it *SkipListIterator) Next() {
	if it.current != nil {
		it.current = it.current.next[0]
	}
}

// Key returns the key at the current position.
func (it *SkipListIterator) Key() []byte {
	if it.current != nil {
		return it.current.key
	}
	return nil
}

// Value returns the value at the current position.
func (it *SkipListIterator) Value() []byte {
	if it.current != nil {
		return it.current.value
	}
	return nil
}

// IsDeleted returns true if the current entry is a tombstone.
func (it *SkipListIterator) IsDeleted() bool {
	return it.current != nil && it.current.deleted
}
