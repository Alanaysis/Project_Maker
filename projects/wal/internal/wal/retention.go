package wal

import (
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

// RetentionPolicy defines how WAL logs should be retained and cleaned up.
type RetentionPolicy struct {
	// MaxSize is the maximum total size of WAL files in bytes (0 = unlimited).
	MaxSize int64
	// MaxAge is the maximum age of WAL files before cleanup (0 = unlimited).
	MaxAge time.Duration
	// MaxFiles is the maximum number of WAL files to keep (0 = unlimited).
	MaxFiles int
	// MinFiles is the minimum number of WAL files to keep regardless of other policies.
	MinFiles int
}

// DefaultRetentionPolicy returns a sensible default retention policy.
func DefaultRetentionPolicy() *RetentionPolicy {
	return &RetentionPolicy{
		MaxSize:  1024 * 1024 * 1024, // 1 GB
		MaxAge:   7 * 24 * time.Hour, // 7 days
		MaxFiles: 10,
		MinFiles: 2,
	}
}

// LogCleaner manages WAL log cleanup based on retention policies.
type LogCleaner struct {
	mu       sync.Mutex
	walDir   string
	policy   *RetentionPolicy
	stopCh   chan struct{}
	interval time.Duration
}

// NewLogCleaner creates a new log cleaner.
func NewLogCleaner(walDir string, policy *RetentionPolicy, interval time.Duration) *LogCleaner {
	if policy == nil {
		policy = DefaultRetentionPolicy()
	}

	return &LogCleaner{
		walDir:   walDir,
		policy:   policy,
		stopCh:   make(chan struct{}),
		interval: interval,
	}
}

// Start begins periodic log cleanup.
func (lc *LogCleaner) Start() {
	go lc.cleanupLoop()
}

// cleanupLoop runs the cleanup at regular intervals.
func (lc *LogCleaner) cleanupLoop() {
	ticker := time.NewTicker(lc.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := lc.Cleanup(); err != nil {
				log.Printf("Log cleanup failed: %v", err)
			}
		case <-lc.stopCh:
			return
		}
	}
}

// Stop stops the periodic cleanup.
func (lc *LogCleaner) Stop() {
	close(lc.stopCh)
}

// Cleanup performs log cleanup based on the retention policy.
func (lc *LogCleaner) Cleanup() error {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	files, err := lc.getWALFiles()
	if err != nil {
		return fmt.Errorf("failed to list WAL files: %w", err)
	}

	if len(files) == 0 {
		return nil
	}

	// Sort by modification time (oldest first)
	sort.Slice(files, func(i, j int) bool {
		return files[i].ModTime.Before(files[j].ModTime)
	})

	var toDelete []walFileInfo

	// Apply age-based cleanup
	if lc.policy.MaxAge > 0 {
		cutoff := time.Now().Add(-lc.policy.MaxAge)
		for _, f := range files {
			if f.ModTime.Before(cutoff) {
				toDelete = append(toDelete, f)
			}
		}
	}

	// Apply count-based cleanup
	if lc.policy.MaxFiles > 0 && len(files) > lc.policy.MaxFiles {
		excess := len(files) - lc.policy.MaxFiles
		for i := 0; i < excess; i++ {
			// Only add if not already marked for deletion
			if !lc.containsFile(toDelete, files[i].Path) {
				toDelete = append(toDelete, files[i])
			}
		}
	}

	// Apply size-based cleanup
	if lc.policy.MaxSize > 0 {
		totalSize := lc.totalSize(files)
		if totalSize > lc.policy.MaxSize {
			// Delete oldest files until we're under the limit
			for _, f := range files {
				if totalSize <= lc.policy.MaxSize {
					break
				}
				if !lc.containsFile(toDelete, f.Path) {
					toDelete = append(toDelete, f)
					totalSize -= f.Size
				}
			}
		}
	}

	// Ensure minimum files are kept
	if lc.policy.MinFiles > 0 {
		keepCount := len(files) - len(toDelete)
		if keepCount < lc.policy.MinFiles {
			// Remove oldest files from deletion list
			sort.Slice(toDelete, func(i, j int) bool {
				return toDelete[i].ModTime.After(toDelete[j].ModTime)
			})
			for keepCount < lc.policy.MinFiles && len(toDelete) > 0 {
				toDelete = toDelete[:len(toDelete)-1]
				keepCount++
			}
		}
	}

	// Delete marked files
	deleted := 0
	for _, f := range toDelete {
		if err := os.Remove(f.Path); err != nil {
			log.Printf("Warning: failed to remove WAL file %s: %v", f.Path, err)
		} else {
			log.Printf("Removed WAL file: %s (age: %s, size: %d bytes)",
				f.Path, time.Since(f.ModTime).Round(time.Second), f.Size)
			deleted++
		}
	}

	if deleted > 0 {
		log.Printf("Cleanup complete: removed %d WAL files", deleted)
	}

	return nil
}

// GetTotalSize returns the total size of all WAL files.
func (lc *LogCleaner) GetTotalSize() (int64, error) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	files, err := lc.getWALFiles()
	if err != nil {
		return 0, err
	}

	return lc.totalSize(files), nil
}

// GetFileCount returns the number of WAL files.
func (lc *LogCleaner) GetFileCount() (int, error) {
	lc.mu.Lock()
	defer lc.mu.Unlock()

	files, err := lc.getWALFiles()
	if err != nil {
		return 0, err
	}

	return len(files), nil
}

// totalSize calculates the total size of a list of WAL files.
func (lc *LogCleaner) totalSize(files []walFileInfo) int64 {
	var total int64
	for _, f := range files {
		total += f.Size
	}
	return total
}

// containsFile checks if a file path is in the list.
func (lc *LogCleaner) containsFile(files []walFileInfo, path string) bool {
	for _, f := range files {
		if f.Path == path {
			return true
		}
	}
	return false
}

// walFileInfo contains information about a WAL file.
type walFileInfo struct {
	Path    string
	Size    int64
	ModTime time.Time
}

// getWALFiles returns information about all WAL files in the directory.
func (lc *LogCleaner) getWALFiles() ([]walFileInfo, error) {
	pattern := filepath.Join(lc.walDir, "*.wal")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, err
	}

	var files []walFileInfo
	for _, match := range matches {
		info, err := os.Stat(match)
		if err != nil {
			continue
		}
		files = append(files, walFileInfo{
			Path:    match,
			Size:    info.Size(),
			ModTime: info.ModTime(),
		})
	}

	return files, nil
}

// TruncateWAL truncates a WAL file at the specified LSN.
// All entries after the given LSN are removed.
func TruncateWAL(walPath string, truncateLSN uint64) error {
	// Read all entries
	reader, err := NewWALReader(walPath)
	if err != nil {
		return fmt.Errorf("failed to open WAL for truncation: %w", err)
	}
	defer reader.Close()

	var keepEntries []*LogEntry
	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // Skip corrupted entries
		}
		if entry.LSN <= truncateLSN {
			keepEntries = append(keepEntries, entry)
		}
	}

	// Create a temporary file
	tmpPath := walPath + ".tmp"
	writer, err := NewWALWriter(tmpPath, SyncImmediate)
	if err != nil {
		return fmt.Errorf("failed to create temporary WAL: %w", err)
	}

	// Write kept entries
	for _, entry := range keepEntries {
		if err := writer.Write(entry); err != nil {
			writer.Close()
			os.Remove(tmpPath)
			return fmt.Errorf("failed to write entry during truncation: %w", err)
		}
	}

	writer.Close()

	// Replace original file
	if err := os.Rename(tmpPath, walPath); err != nil {
		return fmt.Errorf("failed to replace WAL file: %w", err)
	}

	log.Printf("WAL truncated at LSN %d, kept %d entries", truncateLSN, len(keepEntries))
	return nil
}

// TruncateWALAfterTime truncates a WAL file, removing all entries after the given time.
func TruncateWALAfterTime(walPath string, after time.Time) error {
	// Read all entries
	reader, err := NewWALReader(walPath)
	if err != nil {
		return fmt.Errorf("failed to open WAL for truncation: %w", err)
	}
	defer reader.Close()

	var keepEntries []*LogEntry
	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // Skip corrupted entries
		}
		entryTime := time.Unix(0, entry.Timestamp)
		if entryTime.Before(after) || entryTime.Equal(after) {
			keepEntries = append(keepEntries, entry)
		}
	}

	// Create a temporary file
	tmpPath := walPath + ".tmp"
	writer, err := NewWALWriter(tmpPath, SyncImmediate)
	if err != nil {
		return fmt.Errorf("failed to create temporary WAL: %w", err)
	}

	// Write kept entries
	for _, entry := range keepEntries {
		if err := writer.Write(entry); err != nil {
			writer.Close()
			os.Remove(tmpPath)
			return fmt.Errorf("failed to write entry during truncation: %w", err)
		}
	}

	writer.Close()

	// Replace original file
	if err := os.Rename(tmpPath, walPath); err != nil {
		return fmt.Errorf("failed to replace WAL file: %w", err)
	}

	log.Printf("WAL truncated after %s, kept %d entries", after.Format(time.RFC3339), len(keepEntries))
	return nil
}

// GetWALStats returns statistics about a WAL file.
func GetWALStats(walPath string) (*WALStats, error) {
	reader, err := NewWALReader(walPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open WAL: %w", err)
	}
	defer reader.Close()

	stats := &WALStats{
		Path: walPath,
	}

	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			stats.CorruptedEntries++
			continue
		}

		stats.TotalEntries++

		switch entry.OpType {
		case OpPut:
			stats.PutOperations++
		case OpDelete:
			stats.DeleteOperations++
		case OpCommit:
			stats.Commits++
		case OpRollback:
			stats.Rollbacks++
		case OpCheckpoint:
			stats.Checkpoints++
		}

		if entry.LSN > stats.MaxLSN {
			stats.MaxLSN = entry.LSN
		}

		entryTime := time.Unix(0, entry.Timestamp)
		if stats.OldestEntry.IsZero() || entryTime.Before(stats.OldestEntry) {
			stats.OldestEntry = entryTime
		}
		if entryTime.After(stats.NewestEntry) {
			stats.NewestEntry = entryTime
		}
	}

	// Get file size
	info, err := os.Stat(walPath)
	if err == nil {
		stats.FileSize = info.Size()
	}

	return stats, nil
}

// WALStats contains statistics about a WAL file.
type WALStats struct {
	Path             string
	FileSize         int64
	TotalEntries     int
	CorruptedEntries int
	PutOperations    int
	DeleteOperations int
	Commits          int
	Rollbacks        int
	Checkpoints      int
	MaxLSN           uint64
	OldestEntry      time.Time
	NewestEntry      time.Time
}

// String returns a human-readable representation of the stats.
func (s *WALStats) String() string {
	return fmt.Sprintf(
		"WAL Stats for %s:\n"+
			"  File Size: %d bytes\n"+
			"  Total Entries: %d\n"+
			"  Corrupted Entries: %d\n"+
			"  Put Operations: %d\n"+
			"  Delete Operations: %d\n"+
			"  Commits: %d\n"+
			"  Rollbacks: %d\n"+
			"  Checkpoints: %d\n"+
			"  Max LSN: %d\n"+
			"  Oldest Entry: %s\n"+
			"  Newest Entry: %s",
		s.Path, s.FileSize, s.TotalEntries, s.CorruptedEntries,
		s.PutOperations, s.DeleteOperations, s.Commits, s.Rollbacks,
		s.Checkpoints, s.MaxLSN, s.OldestEntry.Format(time.RFC3339),
		s.NewestEntry.Format(time.RFC3339),
	)
}
