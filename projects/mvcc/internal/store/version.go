package store

import (
	"fmt"
	"sync"
)

// VersionStatus represents the lifecycle status of a version
type VersionStatus int

const (
	VersionActive    VersionStatus = iota // Version is active and visible
	VersionDeleted                        // Version has been logically deleted (tombstone)
	VersionGarbage                        // Version is marked for garbage collection
)

func (s VersionStatus) String() string {
	switch s {
	case VersionActive:
		return "Active"
	case VersionDeleted:
		return "Deleted"
	case VersionGarbage:
		return "Garbage"
	default:
		return "Unknown"
	}
}

// Version represents a single version of a key-value pair
type Version struct {
	Key       string
	Value     []byte
	CreatedBy uint64 // Transaction ID that created this version
	CreatedAt uint64 // Timestamp when this version was created
	DeletedBy uint64 // Transaction ID that deleted this version (0 if not deleted)
	DeletedAt uint64 // Timestamp when this version was deleted (0 if not deleted)
	Status    VersionStatus
}

// IsVisible checks if this version is visible at the given timestamp
// A version is visible if:
// 1. It is not in Garbage status
// 2. It was created at or before the read timestamp
// 3. It was not deleted before or at the read timestamp
func (v *Version) IsVisible(readTimestamp uint64) bool {
	if v.Status == VersionGarbage {
		return false
	}
	// Version must be created at or before the read timestamp
	if v.CreatedAt > readTimestamp {
		return false
	}
	// If deleted, the deletion must be after the read timestamp
	if v.DeletedAt > 0 && v.DeletedAt <= readTimestamp {
		return false
	}
	return true
}

// Store is the core key-value store that manages multiple versions of each key
type Store struct {
	mu       sync.RWMutex
	versions map[string][]*Version // key -> sorted versions (by CreatedAt)
}

// NewStore creates a new versioned key-value store
func NewStore() *Store {
	return &Store{
		versions: make(map[string][]*Version),
	}
}

// Put adds a new version for the given key
func (s *Store) Put(key string, value []byte, txnID uint64, timestamp uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()

	version := &Version{
		Key:       key,
		Value:     value,
		CreatedBy: txnID,
		CreatedAt: timestamp,
		Status:    VersionActive,
	}

	s.versions[key] = append(s.versions[key], version)
}

// Delete marks a key as deleted at the given timestamp (creates a tombstone)
func (s *Store) Delete(key string, txnID uint64, timestamp uint64) bool {
	s.mu.Lock()
	defer s.mu.Unlock()

	versions := s.versions[key]
	// Find the latest visible version
	for i := len(versions) - 1; i >= 0; i-- {
		v := versions[i]
		if v.Status == VersionActive && v.CreatedAt <= timestamp {
			v.DeletedBy = txnID
			v.DeletedAt = timestamp
			v.Status = VersionDeleted
			return true
		}
	}
	return false
}

// Get retrieves the value for a key at the given read timestamp
func (s *Store) Get(key string, readTimestamp uint64) ([]byte, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions := s.versions[key]
	// Search from newest to oldest
	for i := len(versions) - 1; i >= 0; i-- {
		v := versions[i]
		if v.IsVisible(readTimestamp) {
			return v.Value, true
		}
	}
	return nil, false
}

// GetVersion retrieves the version object for a key at the given read timestamp
func (s *Store) GetVersion(key string, readTimestamp uint64) (*Version, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions := s.versions[key]
	for i := len(versions) - 1; i >= 0; i-- {
		v := versions[i]
		if v.IsVisible(readTimestamp) {
			return v, true
		}
	}
	return nil, false
}

// HasConflict checks if a write to the given key would conflict
// A conflict exists if another transaction has written to the key after our read timestamp
func (s *Store) HasConflict(key string, readTimestamp uint64, txnID uint64) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions := s.versions[key]
	for _, v := range versions {
		if v.CreatedBy != txnID && v.CreatedAt > readTimestamp && v.Status == VersionActive {
			return true
		}
	}
	return false
}

// RemoveVersions removes all versions of a key that are no longer visible
// to any active transaction with the given minimum read timestamp.
//
// A version can be removed when:
// 1. It was created before minActiveTimestamp, AND
// 2. It is not visible at minActiveTimestamp (deleted before it), OR
// 3. It is superseded by a newer version that is also before minActiveTimestamp
//
// We keep the latest version before minActiveTimestamp if it is still
// visible at that point (for any active transaction to read).
func (s *Store) RemoveVersions(minActiveTimestamp uint64) int {
	s.mu.Lock()
	defer s.mu.Unlock()

	removed := 0
	for key, versions := range s.versions {
		var remaining []*Version

		// Track the latest old version (before minActiveTimestamp)
		var latestOldIdx int = -1
		var latestOldTS uint64 = 0

		// First pass: find the latest version before minActiveTimestamp
		for i, v := range versions {
			if v.CreatedAt < minActiveTimestamp && v.CreatedAt > latestOldTS {
				latestOldTS = v.CreatedAt
				latestOldIdx = i
			}
		}

		// Second pass: decide which versions to keep
		for i, v := range versions {
			if v.CreatedAt >= minActiveTimestamp {
				// New versions (after safe point) are always kept
				remaining = append(remaining, v)
			} else if i == latestOldIdx {
				// This is the latest old version
				// Keep it only if it's still visible at minActiveTimestamp
				if v.IsVisible(minActiveTimestamp) {
					remaining = append(remaining, v)
				} else {
					removed++
				}
			} else {
				// Older versions are superseded and can be removed
				removed++
			}
		}

		if len(remaining) == 0 {
			delete(s.versions, key)
		} else {
			s.versions[key] = remaining
		}
	}
	return removed
}

// AllVersions returns all versions for a key (for debugging/testing)
func (s *Store) AllVersions(key string) []*Version {
	s.mu.RLock()
	defer s.mu.RUnlock()

	versions := s.versions[key]
	result := make([]*Version, len(versions))
	copy(result, versions)
	return result
}

// Keys returns all keys in the store
func (s *Store) Keys() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	keys := make([]string, 0, len(s.versions))
	for k := range s.versions {
		keys = append(keys, k)
	}
	return keys
}

// VersionCount returns the total number of versions across all keys
func (s *Store) VersionCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()

	count := 0
	for _, versions := range s.versions {
		count += len(versions)
	}
	return count
}

// String returns a string representation of the store for debugging
func (s *Store) String() string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := "Store {\n"
	for key, versions := range s.versions {
		result += fmt.Sprintf("  %s: [\n", key)
		for _, v := range versions {
			result += fmt.Sprintf("    {Value: %s, CreatedBy: %d, CreatedAt: %d, DeletedBy: %d, DeletedAt: %d, Status: %s}\n",
				string(v.Value), v.CreatedBy, v.CreatedAt, v.DeletedBy, v.DeletedAt, v.Status)
		}
		result += "  ]\n"
	}
	result += "}"
	return result
}
