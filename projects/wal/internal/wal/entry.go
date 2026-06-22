package wal

import (
	"bytes"
	"encoding/binary"
	"hash/crc32"
	"time"
)

// OperationType represents the type of operation in a log entry.
type OperationType uint8

const (
	// OpPut represents a put (insert/update) operation.
	OpPut OperationType = 1
	// OpDelete represents a delete operation.
	OpDelete OperationType = 2
	// OpCommit represents a transaction commit.
	OpCommit OperationType = 3
	// OpRollback represents a transaction rollback.
	OpRollback OperationType = 4
	// OpCheckpoint represents a checkpoint marker.
	OpCheckpoint OperationType = 5
)

// LogEntry represents a single log entry in the WAL.
type LogEntry struct {
	// LSN is the Log Sequence Number, a unique identifier for this entry.
	LSN uint64
	// TxID is the transaction ID that this entry belongs to.
	TxID uint64
	// OpType is the type of operation.
	OpType OperationType
	// Key is the key being operated on (for Put/Delete operations).
	Key string
	// Value is the value being stored (for Put operations).
	Value []byte
	// Timestamp is the time when this entry was created.
	Timestamp int64
	// Checksum is the CRC32 checksum of the entry data.
	Checksum uint32
}

// NewLogEntry creates a new log entry with the given parameters.
func NewLogEntry(txID uint64, opType OperationType, key string, value []byte) *LogEntry {
	return &LogEntry{
		TxID:      txID,
		OpType:    opType,
		Key:       key,
		Value:     value,
		Timestamp: time.Now().UnixNano(),
	}
}

// Serialize converts the log entry to a byte slice.
func (e *LogEntry) Serialize() ([]byte, error) {
	buf := new(bytes.Buffer)

	// Write LSN
	if err := binary.Write(buf, binary.LittleEndian, e.LSN); err != nil {
		return nil, err
	}

	// Write TxID
	if err := binary.Write(buf, binary.LittleEndian, e.TxID); err != nil {
		return nil, err
	}

	// Write OpType
	if err := binary.Write(buf, binary.LittleEndian, uint8(e.OpType)); err != nil {
		return nil, err
	}

	// Write Key length and Key
	keyBytes := []byte(e.Key)
	if err := binary.Write(buf, binary.LittleEndian, uint32(len(keyBytes))); err != nil {
		return nil, err
	}
	if _, err := buf.Write(keyBytes); err != nil {
		return nil, err
	}

	// Write Value length and Value
	if err := binary.Write(buf, binary.LittleEndian, uint32(len(e.Value))); err != nil {
		return nil, err
	}
	if _, err := buf.Write(e.Value); err != nil {
		return nil, err
	}

	// Write Timestamp
	if err := binary.Write(buf, binary.LittleEndian, e.Timestamp); err != nil {
		return nil, err
	}

	// Calculate and write checksum
	data := buf.Bytes()
	checksum := crc32.ChecksumIEEE(data)
	if err := binary.Write(buf, binary.LittleEndian, checksum); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}

// DeserializeLogEntry converts a byte slice back to a log entry.
func DeserializeLogEntry(data []byte) (*LogEntry, error) {
	if len(data) < 4 {
		return nil, ErrCorruptedLog
	}

	buf := bytes.NewReader(data)
	entry := &LogEntry{}

	// Read LSN
	if err := binary.Read(buf, binary.LittleEndian, &entry.LSN); err != nil {
		return nil, err
	}

	// Read TxID
	if err := binary.Read(buf, binary.LittleEndian, &entry.TxID); err != nil {
		return nil, err
	}

	// Read OpType
	var opType uint8
	if err := binary.Read(buf, binary.LittleEndian, &opType); err != nil {
		return nil, err
	}
	entry.OpType = OperationType(opType)

	// Read Key
	var keyLen uint32
	if err := binary.Read(buf, binary.LittleEndian, &keyLen); err != nil {
		return nil, err
	}
	key := make([]byte, keyLen)
	if _, err := buf.Read(key); err != nil {
		return nil, err
	}
	entry.Key = string(key)

	// Read Value
	var valueLen uint32
	if err := binary.Read(buf, binary.LittleEndian, &valueLen); err != nil {
		return nil, err
	}
	value := make([]byte, valueLen)
	if _, err := buf.Read(value); err != nil {
		return nil, err
	}
	entry.Value = value

	// Read Timestamp
	if err := binary.Read(buf, binary.LittleEndian, &entry.Timestamp); err != nil {
		return nil, err
	}

	// Read checksum
	var checksum uint32
	if err := binary.Read(buf, binary.LittleEndian, &checksum); err != nil {
		return nil, err
	}

	// Verify checksum
	dataWithoutChecksum := data[:len(data)-4]
	expectedChecksum := crc32.ChecksumIEEE(dataWithoutChecksum)
	if checksum != expectedChecksum {
		return nil, ErrChecksumMismatch
	}

	entry.Checksum = checksum
	return entry, nil
}

// Size returns the serialized size of the log entry.
func (e *LogEntry) Size() int {
	// LSN(8) + TxID(8) + OpType(1) + KeyLen(4) + Key + ValueLen(4) + Value + Timestamp(8) + Checksum(4)
	return 8 + 8 + 1 + 4 + len(e.Key) + 4 + len(e.Value) + 8 + 4
}
