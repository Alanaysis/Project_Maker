package wal

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"sync"
	"time"
)

// Checkpoint represents a checkpoint in the WAL.
type Checkpoint struct {
	// LSN is the log sequence number at the checkpoint.
	LSN uint64
	// Timestamp is the time when the checkpoint was created.
	Timestamp int64
	// ActiveTxIDs is the list of active transaction IDs at the checkpoint.
	ActiveTxIDs []uint64
}

// CheckpointManager manages checkpoints in the WAL.
type CheckpointManager struct {
	mu           sync.Mutex
	walDir       string
	walWriter    *WALWriter
	interval     time.Duration
	dirtyPages   map[string]bool
	stopCh       chan struct{}
	lastCheckpoint *Checkpoint
}

// NewCheckpointManager creates a new checkpoint manager.
func NewCheckpointManager(walDir string, walWriter *WALWriter, interval time.Duration) *CheckpointManager {
	return &CheckpointManager{
		walDir:     walDir,
		walWriter:  walWriter,
		interval:   interval,
		dirtyPages: make(map[string]bool),
		stopCh:     make(chan struct{}),
	}
}

// MarkDirty marks a key as dirty (needs to be flushed).
func (cm *CheckpointManager) MarkDirty(key string) {
	cm.mu.Lock()
	defer cm.mu.Unlock()
	cm.dirtyPages[key] = true
}

// CreateCheckpoint creates a new checkpoint.
func (cm *CheckpointManager) CreateCheckpoint() error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	log.Println("Creating checkpoint...")

	// 1. Write checkpoint entry to WAL
	checkpointEntry := &LogEntry{
		TxID:      0, // System transaction
		OpType:    OpCheckpoint,
		Key:       "checkpoint",
		Value:     []byte(fmt.Sprintf("%d", time.Now().UnixNano())),
		Timestamp: time.Now().UnixNano(),
	}

	if err := cm.walWriter.Write(checkpointEntry); err != nil {
		return fmt.Errorf("failed to write checkpoint entry: %w", err)
	}

	// 2. Update last checkpoint
	cm.lastCheckpoint = &Checkpoint{
		LSN:       checkpointEntry.LSN,
		Timestamp: checkpointEntry.Timestamp,
	}

	// 3. Clear dirty pages
	cm.dirtyPages = make(map[string]bool)

	// 4. Clean old WAL files
	if err := cm.cleanOldWALFiles(); err != nil {
		log.Printf("Warning: failed to clean old WAL files: %v", err)
	}

	log.Printf("Checkpoint created at LSN: %d", checkpointEntry.LSN)
	return nil
}

// cleanOldWALFiles removes WAL files that are no longer needed.
func (cm *CheckpointManager) cleanOldWALFiles() error {
	files, err := ListWALFiles(cm.walDir)
	if err != nil {
		return err
	}

	if len(files) <= 1 {
		return nil // Keep at least one file
	}

	// Sort files by name (which should include timestamp or sequence number)
	sort.Strings(files)

	// Remove all but the latest file
	for i := 0; i < len(files)-1; i++ {
		if err := os.Remove(files[i]); err != nil {
			log.Printf("Warning: failed to remove old WAL file %s: %v", files[i], err)
		} else {
			log.Printf("Removed old WAL file: %s", files[i])
		}
	}

	return nil
}

// LoadLastCheckpoint loads the last checkpoint from the WAL directory.
func (cm *CheckpointManager) LoadLastCheckpoint() (*Checkpoint, error) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if cm.lastCheckpoint != nil {
		return cm.lastCheckpoint, nil
	}

	files, err := ListWALFiles(cm.walDir)
	if err != nil {
		return nil, err
	}

	if len(files) == 0 {
		return nil, nil
	}

	// Read the latest file
	latestFile := files[len(files)-1]
	reader, err := NewWALReader(latestFile)
	if err != nil {
		return nil, err
	}
	defer reader.Close()

	var lastCheckpoint *Checkpoint

	entries, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if entry.OpType == OpCheckpoint {
			lastCheckpoint = &Checkpoint{
				LSN:       entry.LSN,
				Timestamp: entry.Timestamp,
			}
		}
	}

	cm.lastCheckpoint = lastCheckpoint
	return lastCheckpoint, nil
}

// GetDirtyPages returns the list of dirty pages.
func (cm *CheckpointManager) GetDirtyPages() []string {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	pages := make([]string, 0, len(cm.dirtyPages))
	for page := range cm.dirtyPages {
		pages = append(pages, page)
	}
	return pages
}

// StartPeriodicCheckpoint starts periodic checkpoint creation.
func (cm *CheckpointManager) StartPeriodicCheckpoint() {
	go func() {
		ticker := time.NewTicker(cm.interval)
		defer ticker.Stop()

		for {
			select {
			case <-ticker.C:
				if err := cm.CreateCheckpoint(); err != nil {
					log.Printf("Failed to create checkpoint: %v", err)
				}
			case <-cm.stopCh:
				return
			}
		}
	}()
}

// Stop stops the periodic checkpoint creation.
func (cm *CheckpointManager) Stop() {
	close(cm.stopCh)
}

// CheckpointScheduler manages checkpoint scheduling.
type CheckpointScheduler struct {
	mu              sync.Mutex
	checkpointMgr   *CheckpointManager
	checkpointInterval time.Duration
	maxDirtyPages   int
	stopCh          chan struct{}
}

// NewCheckpointScheduler creates a new checkpoint scheduler.
func NewCheckpointScheduler(checkpointMgr *CheckpointManager, interval time.Duration, maxDirtyPages int) *CheckpointScheduler {
	return &CheckpointScheduler{
		checkpointMgr:      checkpointMgr,
		checkpointInterval: interval,
		maxDirtyPages:      maxDirtyPages,
		stopCh:             make(chan struct{}),
	}
}

// Start starts the checkpoint scheduler.
func (cs *CheckpointScheduler) Start() {
	go cs.scheduleLoop()
}

// scheduleLoop runs the checkpoint scheduling loop.
func (cs *CheckpointScheduler) scheduleLoop() {
	ticker := time.NewTicker(cs.checkpointInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			cs.checkIfNeeded()
		case <-cs.stopCh:
			return
		}
	}
}

// checkIfNeeded checks if a checkpoint is needed and creates one if so.
func (cs *CheckpointScheduler) checkIfNeeded() {
	cs.mu.Lock()
	defer cs.mu.Unlock()

	dirtyPages := cs.checkpointMgr.GetDirtyPages()
	if len(dirtyPages) >= cs.maxDirtyPages {
		log.Printf("Dirty page limit reached (%d/%d), creating checkpoint",
			len(dirtyPages), cs.maxDirtyPages)
		if err := cs.checkpointMgr.CreateCheckpoint(); err != nil {
			log.Printf("Failed to create checkpoint: %v", err)
		}
	}
}

// Stop stops the checkpoint scheduler.
func (cs *CheckpointScheduler) Stop() {
	close(cs.stopCh)
}

// RotateWAL creates a new WAL file and returns the old one's path.
func RotateWAL(walDir string, currentWriter *WALWriter) (*WALWriter, string, error) {
	// Close current writer
	oldPath := ""
	if currentWriter != nil {
		oldPath = currentWriter.path
		if err := currentWriter.Close(); err != nil {
			return nil, "", fmt.Errorf("failed to close current WAL: %w", err)
		}
	}

	// Create new WAL file
	timestamp := time.Now().UnixNano()
	newPath := filepath.Join(walDir, fmt.Sprintf("wal.%d.wal", timestamp))

	newWriter, err := NewWALWriter(newPath, SyncImmediate)
	if err != nil {
		return nil, "", fmt.Errorf("failed to create new WAL: %w", err)
	}

	return newWriter, oldPath, nil
}

// GetWALSize returns the size of a WAL file.
func GetWALSize(walPath string) (int64, error) {
	info, err := os.Stat(walPath)
	if err != nil {
		return 0, err
	}
	return info.Size(), nil
}

// NeedsRotation checks if the WAL file needs rotation.
func NeedsRotation(walPath string, maxSize int64) (bool, error) {
	size, err := GetWALSize(walPath)
	if err != nil {
		return false, err
	}
	return size >= maxSize, nil
}
