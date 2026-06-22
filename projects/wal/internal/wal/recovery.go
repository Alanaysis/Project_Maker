package wal

import (
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// RecoveryManager handles crash recovery.
type RecoveryManager struct {
	walPath          string
	storage          Storage
	lastCheckpoint   *Checkpoint
	committedTxns    map[uint64]bool
	activeTxns       map[uint64]bool
}

// NewRecoveryManager creates a new recovery manager.
func NewRecoveryManager(walPath string, storage Storage) *RecoveryManager {
	return &RecoveryManager{
		walPath:       walPath,
		storage:       storage,
		committedTxns: make(map[uint64]bool),
		activeTxns:    make(map[uint64]bool),
	}
}

// Recover performs crash recovery by replaying the WAL.
func (rm *RecoveryManager) Recover() error {
	log.Println("Starting crash recovery...")

	// 1. Find the latest WAL file
	latestWAL, err := rm.findLatestWAL()
	if err != nil {
		return fmt.Errorf("failed to find latest WAL: %w", err)
	}

	if latestWAL == "" {
		log.Println("No WAL files found, recovery complete")
		return nil
	}

	log.Printf("Recovering from WAL: %s", latestWAL)

	// 2. Load the last checkpoint
	checkpoint, err := rm.loadLastCheckpoint(latestWAL)
	if err != nil {
		log.Printf("Warning: failed to load checkpoint: %v", err)
	} else {
		rm.lastCheckpoint = checkpoint
		log.Printf("Loaded checkpoint at LSN: %d", checkpoint.LSN)
	}

	// 3. Read all entries from the WAL
	reader, err := NewWALReader(latestWAL)
	if err != nil {
		return fmt.Errorf("failed to open WAL reader: %w", err)
	}
	defer reader.Close()

	entries, err := reader.ReadAll()
	if err != nil {
		return fmt.Errorf("failed to read WAL entries: %w", err)
	}

	log.Printf("Read %d entries from WAL", len(entries))

	// 4. Process entries
	if err := rm.processEntries(entries); err != nil {
		return fmt.Errorf("failed to process entries: %w", err)
	}

	// 5. Apply committed transactions
	if err := rm.applyCommittedTransactions(entries); err != nil {
		return fmt.Errorf("failed to apply committed transactions: %w", err)
	}

	log.Println("Recovery complete")
	return nil
}

// findLatestWAL finds the latest WAL file in the directory.
func (rm *RecoveryManager) findLatestWAL() (string, error) {
	dir := filepath.Dir(rm.walPath)
	pattern := filepath.Join(dir, "*.wal")

	matches, err := filepath.Glob(pattern)
	if err != nil {
		return "", err
	}

	if len(matches) == 0 {
		return "", nil
	}

	// Sort by modification time (newest first)
	sort.Slice(matches, func(i, j int) bool {
		infoI, _ := os.Stat(matches[i])
		infoJ, _ := os.Stat(matches[j])
		return infoI.ModTime().After(infoJ.ModTime())
	})

	return matches[0], nil
}

// loadLastCheckpoint loads the last checkpoint from the WAL.
func (rm *RecoveryManager) loadLastCheckpoint(walPath string) (*Checkpoint, error) {
	reader, err := NewWALReader(walPath)
	if err != nil {
		return nil, err
	}
	defer reader.Close()

	var lastCheckpoint *Checkpoint

	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			continue // Skip corrupted entries
		}

		if entry.OpType == OpCheckpoint {
			checkpoint := &Checkpoint{
				LSN:       entry.LSN,
				Timestamp: entry.Timestamp,
			}
			lastCheckpoint = checkpoint
		}
	}

	return lastCheckpoint, nil
}

// processEntries processes all WAL entries to identify committed transactions.
func (rm *RecoveryManager) processEntries(entries []*LogEntry) error {
	// First pass: identify committed transactions
	for _, entry := range entries {
		switch entry.OpType {
		case OpCommit:
			rm.committedTxns[entry.TxID] = true
			delete(rm.activeTxns, entry.TxID)
		case OpRollback:
			delete(rm.activeTxns, entry.TxID)
			delete(rm.committedTxns, entry.TxID)
		default:
			// Track active transactions
			rm.activeTxns[entry.TxID] = true
		}
	}

	log.Printf("Found %d committed transactions", len(rm.committedTxns))
	log.Printf("Found %d active (uncommitted) transactions", len(rm.activeTxns))

	return nil
}

// applyCommittedTransactions applies all committed transactions to storage.
func (rm *RecoveryManager) applyCommittedTransactions(entries []*LogEntry) error {
	// Second pass: apply committed transactions
	for _, entry := range entries {
		if entry.OpType == OpCheckpoint || entry.OpType == OpCommit || entry.OpType == OpRollback {
			continue
		}

		// Only apply entries from committed transactions
		if !rm.committedTxns[entry.TxID] {
			continue
		}

		if err := rm.applyEntry(entry); err != nil {
			return fmt.Errorf("failed to apply entry LSN %d: %w", entry.LSN, err)
		}
	}

	return nil
}

// applyEntry applies a single log entry to storage.
func (rm *RecoveryManager) applyEntry(entry *LogEntry) error {
	switch entry.OpType {
	case OpPut:
		return rm.storage.Put(entry.Key, entry.Value)
	case OpDelete:
		return rm.storage.Delete(entry.Key)
	default:
		return nil
	}
}

// GetCommittedTransactions returns the set of committed transaction IDs.
func (rm *RecoveryManager) GetCommittedTransactions() map[uint64]bool {
	return rm.committedTxns
}

// GetActiveTransactions returns the set of active (uncommitted) transaction IDs.
func (rm *RecoveryManager) GetActiveTransactions() map[uint64]bool {
	return rm.activeTxns
}

// ValidateWAL validates the integrity of a WAL file.
func ValidateWAL(walPath string) error {
	reader, err := NewWALReader(walPath)
	if err != nil {
		return fmt.Errorf("failed to open WAL: %w", err)
	}
	defer reader.Close()

	entryCount := 0
	corruptedCount := 0

	for {
		entry, err := reader.ReadNext()
		if err == io.EOF {
			break
		}
		if err != nil {
			corruptedCount++
			continue
		}
		entryCount++
		_ = entry
	}

	if corruptedCount > 0 {
		return fmt.Errorf("WAL contains %d corrupted entries out of %d total",
			corruptedCount, entryCount+corruptedCount)
	}

	return nil
}

// ListWALFiles lists all WAL files in a directory.
func ListWALFiles(dir string) ([]string, error) {
	pattern := filepath.Join(dir, "*.wal")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, err
	}

	// Sort by name
	sort.Strings(matches)

	// Filter to only include .wal files
	var walFiles []string
	for _, match := range matches {
		if strings.HasSuffix(match, ".wal") {
			walFiles = append(walFiles, match)
		}
	}

	return walFiles, nil
}
