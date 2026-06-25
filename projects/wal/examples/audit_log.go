package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/copyninja/wal/internal/wal"
)

// AuditAction represents the type of audited action.
type AuditAction string

const (
	ActionCreate AuditAction = "CREATE"
	ActionRead   AuditAction = "READ"
	ActionUpdate AuditAction = "UPDATE"
	ActionDelete AuditAction = "DELETE"
	ActionLogin  AuditAction = "LOGIN"
	ActionLogout AuditAction = "LOGOUT"
)

// AuditEntry represents a single audit log entry.
type AuditEntry struct {
	ID        string      `json:"id"`
	UserID    string      `json:"user_id"`
	Action    AuditAction `json:"action"`
	Resource  string      `json:"resource"`
	Details   string      `json:"details"`
	IPAddress string      `json:"ip_address"`
	UserAgent string      `json:"user_agent"`
	Timestamp time.Time   `json:"timestamp"`
	Success   bool        `json:"success"`
}

// AuditLogger provides audit logging functionality using WAL.
type AuditLogger struct {
	writer    *wal.WALWriter
	entries   []*AuditEntry
	nextID    int
}

// NewAuditLogger creates a new audit logger.
func NewAuditLogger(walPath string) (*AuditLogger, error) {
	writer, err := wal.NewWALWriter(walPath, wal.SyncImmediate)
	if err != nil {
		return nil, fmt.Errorf("failed to create WAL writer: %w", err)
	}

	return &AuditLogger{
		writer:  writer,
		entries: make([]*AuditEntry, 0),
		nextID:  1,
	}, nil
}

// LogAction logs an auditable action.
func (al *AuditLogger) LogAction(userID string, action AuditAction, resource string, details string, ipAddress string, userAgent string, success bool) error {
	entry := &AuditEntry{
		ID:        fmt.Sprintf("audit-%d", al.nextID),
		UserID:    userID,
		Action:    action,
		Resource:  resource,
		Details:   details,
		IPAddress: ipAddress,
		UserAgent: userAgent,
		Timestamp: time.Now(),
		Success:   success,
	}

	// Serialize entry to JSON
	entryData, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("failed to marshal audit entry: %w", err)
	}

	// Write to WAL
	walEntry := &wal.LogEntry{
		TxID:   uint64(al.nextID),
		OpType: wal.OpPut,
		Key:    entry.ID,
		Value:  entryData,
	}

	if err := al.writer.Write(walEntry); err != nil {
		return fmt.Errorf("failed to write audit entry to WAL: %w", err)
	}

	// Commit the entry
	commitEntry := &wal.LogEntry{
		TxID:   uint64(al.nextID),
		OpType: wal.OpCommit,
	}
	if err := al.writer.Write(commitEntry); err != nil {
		return fmt.Errorf("failed to commit audit entry: %w", err)
	}

	// Add to in-memory store
	al.entries = append(al.entries, entry)
	al.nextID++

	return nil
}

// GetEntries returns all audit entries.
func (al *AuditLogger) GetEntries() []*AuditEntry {
	return al.entries
}

// GetEntriesByUser returns audit entries for a specific user.
func (al *AuditLogger) GetEntriesByUser(userID string) []*AuditEntry {
	var result []*AuditEntry
	for _, entry := range al.entries {
		if entry.UserID == userID {
			result = append(result, entry)
		}
	}
	return result
}

// GetEntriesByAction returns audit entries for a specific action.
func (al *AuditLogger) GetEntriesByAction(action AuditAction) []*AuditEntry {
	var result []*AuditEntry
	for _, entry := range al.entries {
		if entry.Action == action {
			result = append(result, entry)
		}
	}
	return result
}

// GetEntriesByTimeRange returns audit entries within a time range.
func (al *AuditLogger) GetEntriesByTimeRange(start, end time.Time) []*AuditEntry {
	var result []*AuditEntry
	for _, entry := range al.entries {
		if entry.Timestamp.After(start) && entry.Timestamp.Before(end) {
			result = append(result, entry)
		}
	}
	return result
}

// GetFailedEntries returns all failed audit entries.
func (al *AuditLogger) GetFailedEntries() []*AuditEntry {
	var result []*AuditEntry
	for _, entry := range al.entries {
		if !entry.Success {
			result = append(result, entry)
		}
	}
	return result
}

// Close closes the audit logger.
func (al *AuditLogger) Close() error {
	return al.writer.Close()
}

// Recover recovers audit entries from WAL.
func (al *AuditLogger) Recover(walPath string) error {
	reader, err := wal.NewWALReader(walPath)
	if err != nil {
		return fmt.Errorf("failed to open WAL reader: %w", err)
	}
	defer reader.Close()

	// Track committed transactions
	committedTxns := make(map[uint64]bool)
	var walEntries []*wal.LogEntry

	// First pass: identify committed transactions
	for {
		entry, err := reader.ReadNext()
		if err != nil {
			break
		}
		if entry.OpType == wal.OpCommit {
			committedTxns[entry.TxID] = true
		} else if entry.OpType == wal.OpPut {
			walEntries = append(walEntries, entry)
		}
	}

	// Second pass: replay committed entries
	maxID := 0
	for _, entry := range walEntries {
		if !committedTxns[entry.TxID] {
			continue
		}

		var auditEntry AuditEntry
		if err := json.Unmarshal(entry.Value, &auditEntry); err != nil {
			log.Printf("Warning: failed to unmarshal audit entry: %v", err)
			continue
		}

		al.entries = append(al.entries, &auditEntry)
		if int(entry.TxID) > maxID {
			maxID = int(entry.TxID)
		}
	}

	al.nextID = maxID + 1
	return nil
}

// GenerateReport generates an audit report.
func (al *AuditLogger) GenerateReport() string {
	total := len(al.entries)
	successful := 0
	failed := 0
	actionCounts := make(map[AuditAction]int)
	userCounts := make(map[string]int)

	for _, entry := range al.entries {
		if entry.Success {
			successful++
		} else {
			failed++
		}
		actionCounts[entry.Action]++
		userCounts[entry.UserID]++
	}

	report := fmt.Sprintf("Audit Report\n")
	report += fmt.Sprintf("============\n")
	report += fmt.Sprintf("Total Entries: %d\n", total)
	report += fmt.Sprintf("Successful: %d (%.1f%%)\n", successful, float64(successful)/float64(total)*100)
	report += fmt.Sprintf("Failed: %d (%.1f%%)\n", failed, float64(failed)/float64(total)*100)
	report += fmt.Sprintf("\nActions:\n")
	for action, count := range actionCounts {
		report += fmt.Sprintf("  %s: %d\n", action, count)
	}
	report += fmt.Sprintf("\nUsers:\n")
	for user, count := range userCounts {
		report += fmt.Sprintf("  %s: %d entries\n", user, count)
	}

	return report
}

func main() {
	log.Println("Audit Log with WAL Example")
	log.Println("==========================")

	// Create temporary directory
	tmpDir := filepath.Join(os.TempDir(), "wal-audit-log")
	os.MkdirAll(tmpDir, 0755)
	defer os.RemoveAll(tmpDir)

	walPath := filepath.Join(tmpDir, "audit.wal")

	// Example 1: Log various actions
	log.Println("\n1. Logging Audit Events")
	auditLogger, err := NewAuditLogger(walPath)
	if err != nil {
		log.Fatalf("Failed to create audit logger: %v", err)
	}

	// Log some actions
	auditLogger.LogAction("user:1", ActionLogin, "auth", "User logged in", "192.168.1.1", "Mozilla/5.0", true)
	log.Println("  Logged: user:1 LOGIN")

	auditLogger.LogAction("user:1", ActionRead, "users:1", "Read user profile", "192.168.1.1", "Mozilla/5.0", true)
	log.Println("  Logged: user:1 READ users:1")

	auditLogger.LogAction("user:1", ActionUpdate, "users:1", "Updated email", "192.168.1.1", "Mozilla/5.0", true)
	log.Println("  Logged: user:1 UPDATE users:1")

	auditLogger.LogAction("user:2", ActionLogin, "auth", "Failed login attempt", "192.168.1.2", "curl/7.68.0", false)
	log.Println("  Logged: user:2 LOGIN (failed)")

	auditLogger.LogAction("user:1", ActionDelete, "users:3", "Deleted user account", "192.168.1.1", "Mozilla/5.0", true)
	log.Println("  Logged: user:1 DELETE users:3")

	auditLogger.LogAction("user:1", ActionLogout, "auth", "User logged out", "192.168.1.1", "Mozilla/5.0", true)
	log.Println("  Logged: user:1 LOGOUT")

	auditLogger.Close()

	// Example 2: Recover from WAL
	log.Println("\n2. Recovering Audit Entries from WAL")
	recoveredLogger, err := NewAuditLogger(walPath)
	if err != nil {
		log.Fatalf("Failed to create recovered audit logger: %v", err)
	}
	defer recoveredLogger.Close()

	err = recoveredLogger.Recover(walPath)
	if err != nil {
		log.Fatalf("Failed to recover audit entries: %v", err)
	}

	log.Printf("  Recovered %d audit entries", len(recoveredLogger.GetEntries()))

	// Example 3: Query audit entries
	log.Println("\n3. Querying Audit Entries")

	// Get entries for user:1
	userEntries := recoveredLogger.GetEntriesByUser("user:1")
	log.Printf("  Entries for user:1: %d", len(userEntries))
	for _, entry := range userEntries {
		log.Printf("    %s %s - %s (success: %v)",
			entry.Timestamp.Format(time.RFC3339), entry.Action, entry.Resource, entry.Success)
	}

	// Get failed entries
	failedEntries := recoveredLogger.GetFailedEntries()
	log.Printf("\n  Failed entries: %d", len(failedEntries))
	for _, entry := range failedEntries {
		log.Printf("    %s %s by %s - %s",
			entry.Timestamp.Format(time.RFC3339), entry.Action, entry.UserID, entry.Details)
	}

	// Get entries by action
	loginEntries := recoveredLogger.GetEntriesByAction(ActionLogin)
	log.Printf("\n  Login entries: %d", len(loginEntries))

	// Example 4: Generate report
	log.Println("\n4. Audit Report")
	report := recoveredLogger.GenerateReport()
	log.Println(report)

	log.Println("Audit log example complete!")
}
