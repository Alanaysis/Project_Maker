# WAL Tests

This directory contains tests for the WAL (Write-Ahead Logging) implementation.

## Test Files

- `wal_test.go` - Tests for basic WAL operations (serialization, writing, reading)
- `recovery_test.go` - Tests for crash recovery scenarios
- `checkpoint_test.go` - Tests for checkpoint mechanism
- `retention_test.go` - Tests for log retention and cleanup

## Running Tests

### Run All Tests

```bash
cd projects/wal
go test ./test/...
```

### Run Specific Test

```bash
# Run only WAL tests
go test -run TestWAL ./test/...

# Run only recovery tests
go test -run TestRecovery ./test/...

# Run only checkpoint tests
go test -run TestCheckpoint ./test/...

# Run only retention tests
go test -run TestRetentionPolicy ./test/...
go test -run TestLogCleaner ./test/...
go test -run TestTruncateWAL ./test/...
go test -run TestGetWALStats ./test/...
```

### Run with Verbose Output

```bash
go test -v ./test/...
```

### Run with Coverage

```bash
go test -coverprofile=coverage.out ./test/...
go tool cover -html=coverage.out
```

## Test Categories

### 1. WAL Basic Tests (wal_test.go)

- **TestLogEntrySerialization** - Tests serialization and deserialization of log entries
- **TestLogEntryChecksumValidation** - Tests checksum validation
- **TestWALWriterBasicWrite** - Tests basic write operations
- **TestWALWriterBatchWrite** - Tests batch write operations
- **TestWALWriterConcurrentWrite** - Tests concurrent write safety
- **TestWALReaderBasicRead** - Tests basic read operations
- **TestWALReaderReadByLSN** - Tests reading entries by LSN
- **TestWALWriterSyncModes** - Tests different sync modes

### 2. Recovery Tests (recovery_test.go)

- **TestRecoveryNormal** - Tests normal recovery scenario
- **TestRecoveryCrash** - Tests recovery after crash (uncommitted transactions)
- **TestRecoveryMultipleTransactions** - Tests recovery with multiple transactions
- **TestRecoveryDeleteOperation** - Tests recovery of delete operations
- **TestRecoveryMultipleOperations** - Tests recovery with multiple operations
- **TestRecoveryLargeDataset** - Tests recovery with large dataset
- **TestValidateWAL** - Tests WAL file validation
- **TestValidateWALCorrupted** - Tests validation of corrupted WAL
- **TestListWALFiles** - Tests listing WAL files

### 3. Checkpoint Tests (checkpoint_test.go)

- **TestCheckpointCreation** - Tests checkpoint creation
- **TestCheckpointLoadLast** - Tests loading the last checkpoint
- **TestCheckpointDirtyPages** - Tests dirty page tracking
- **TestCheckpointLogCleanup** - Tests log cleanup after checkpoint
- **TestCheckpointScheduler** - Tests automatic checkpoint scheduling
- **TestRotateWAL** - Tests WAL file rotation
- **TestGetWALSize** - Tests getting WAL file size
- **TestNeedsRotation** - Tests rotation detection
- **TestCheckpointWithRecovery** - Tests checkpoint with recovery

### 4. Retention Tests (retention_test.go)

- **TestRetentionPolicyDefaults** - Tests default retention policy values
- **TestLogCleanerFileCount** - Tests file count-based cleanup
- **TestLogCleanerMinFiles** - Tests minimum file count enforcement
- **TestLogCleanerSizeBased** - Tests size-based cleanup
- **TestTruncateWAL** - Tests WAL truncation by LSN
- **TestTruncateWALAfterTime** - Tests WAL truncation by time
- **TestGetWALStats** - Tests WAL statistics gathering
- **TestWALStatsString** - Tests stats string representation
- **TestLogCleanerGetTotalSize** - Tests total size calculation
- **TestLogCleanerGetFileCount** - Tests file count retrieval
- **TestLogCleanerEmptyDirectory** - Tests cleanup on empty directory
- **TestLogCleanerWithNonWALFiles** - Tests that non-WAL files are not affected

## Writing New Tests

When adding new tests:

1. Follow the naming convention: `Test<Feature><Scenario>`
2. Use `t.TempDir()` for temporary directories
3. Clean up resources using `defer`
4. Use descriptive error messages
5. Test both success and failure scenarios

Example:

```go
func TestNewFeature(t *testing.T) {
    tmpDir := t.TempDir()
    
    // Setup
    writer, err := wal.NewWALWriter(filepath.Join(tmpDir, "test.wal"), wal.SyncImmediate)
    if err != nil {
        t.Fatalf("Failed to create WAL writer: %v", err)
    }
    defer writer.Close()
    
    // Test
    entry := &wal.LogEntry{
        TxID:   1,
        OpType: wal.OpPut,
        Key:    "test",
        Value:  []byte("value"),
    }
    
    if err := writer.Write(entry); err != nil {
        t.Fatalf("Failed to write entry: %v", err)
    }
    
    // Verify
    if entry.LSN == 0 {
        t.Error("LSN was not assigned")
    }
}
```
