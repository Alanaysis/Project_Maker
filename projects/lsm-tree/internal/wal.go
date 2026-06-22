package internal

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"hash/crc32"
	"io"
	"os"
)

// WALRecordType represents the type of a WAL record.
type WALRecordType uint8

const (
	WALPut    WALRecordType = 1
	WALDelete WALRecordType = 2
)

// WALRecord represents a single entry in the Write-Ahead Log.
// Format: [type:1][key_len:4][key][val_len:4][value][crc32:4]
type WALRecord struct {
	Type  WALRecordType
	Key   []byte
	Value []byte
}

// WAL (Write-Ahead Log) ensures durability of writes.
// All writes are first written to the WAL before being applied to the MemTable.
// On crash recovery, the WAL is replayed to reconstruct the MemTable.
type WAL struct {
	file     *os.File
	writer   *bufio.Writer
	filePath string
}

// NewWAL creates a new WAL instance for the given file path.
func NewWAL(filePath string) (*WAL, error) {
	f, err := os.OpenFile(filePath, os.O_CREATE|os.O_RDWR|os.O_APPEND, 0644)
	if err != nil {
		return nil, fmt.Errorf("wal: failed to open file: %w", err)
	}
	return &WAL{
		file:     f,
		writer:   bufio.NewWriter(f),
		filePath: filePath,
	}, nil
}

// WritePut writes a put record to the WAL.
func (w *WAL) WritePut(key, value []byte) error {
	return w.writeRecord(WALRecord{Type: WALPut, Key: key, Value: value})
}

// WriteDelete writes a delete record to the WAL.
func (w *WAL) WriteDelete(key []byte) error {
	return w.writeRecord(WALRecord{Type: WALDelete, Key: key, Value: nil})
}

// writeRecord writes a single record to the WAL.
// Record format: [type:1][key_len:4][key][val_len:4][value][crc32:4]
func (w *WAL) writeRecord(rec WALRecord) error {
	// Write record type
	if err := w.writer.WriteByte(byte(rec.Type)); err != nil {
		return err
	}

	// Write key length and key
	if err := binary.Write(w.writer, binary.LittleEndian, uint32(len(rec.Key))); err != nil {
		return err
	}
	if _, err := w.writer.Write(rec.Key); err != nil {
		return err
	}

	// Write value length and value
	if err := binary.Write(w.writer, binary.LittleEndian, uint32(len(rec.Value))); err != nil {
		return err
	}
	if _, err := w.writer.Write(rec.Value); err != nil {
		return err
	}

	// Calculate and write CRC32 checksum
	checksum := crc32.ChecksumIEEE(append(rec.Key, rec.Value...))
	if err := binary.Write(w.writer, binary.LittleEndian, checksum); err != nil {
		return err
	}

	return w.writer.Flush()
}

// Sync forces any buffered data to be written to disk.
func (w *WAL) Sync() error {
	if err := w.writer.Flush(); err != nil {
		return err
	}
	return w.file.Sync()
}

// Close closes the WAL file.
func (w *WAL) Close() error {
	if err := w.writer.Flush(); err != nil {
		return err
	}
	return w.file.Close()
}

// Path returns the file path of the WAL.
func (w *WAL) Path() string {
	return w.filePath
}

// Replay reads all records from the WAL and applies them to the given MemTable.
// This is used during crash recovery to rebuild the MemTable state.
func WALReplay(filePath string, memTable *MemTable) error {
	f, err := os.Open(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("wal: failed to open for replay: %w", err)
	}
	defer f.Close()

	reader := bufio.NewReader(f)
	for {
		rec, err := readRecord(reader)
		if err != nil {
			if err == io.EOF {
				break
			}
			return fmt.Errorf("wal: replay error: %w", err)
		}

		switch rec.Type {
		case WALPut:
			memTable.Put(rec.Key, rec.Value)
		case WALDelete:
			memTable.Delete(rec.Key)
		}
	}
	return nil
}

// readRecord reads a single record from the WAL.
func readRecord(reader *bufio.Reader) (*WALRecord, error) {
	// Read record type
	typeByte, err := reader.ReadByte()
	if err != nil {
		return nil, err
	}

	// Read key length
	var keyLen uint32
	if err := binary.Read(reader, binary.LittleEndian, &keyLen); err != nil {
		return nil, err
	}

	// Read key
	key := make([]byte, keyLen)
	if _, err := io.ReadFull(reader, key); err != nil {
		return nil, err
	}

	// Read value length
	var valLen uint32
	if err := binary.Read(reader, binary.LittleEndian, &valLen); err != nil {
		return nil, err
	}

	// Read value
	value := make([]byte, valLen)
	if _, err := io.ReadFull(reader, value); err != nil {
		return nil, err
	}

	// Read and verify CRC32 checksum
	var storedCRC uint32
	if err := binary.Read(reader, binary.LittleEndian, &storedCRC); err != nil {
		return nil, err
	}
	expectedCRC := crc32.ChecksumIEEE(append(key, value...))
	if storedCRC != expectedCRC {
		return nil, fmt.Errorf("wal: CRC mismatch for key %s", key)
	}

	return &WALRecord{
		Type:  WALRecordType(typeByte),
		Key:   key,
		Value: value,
	}, nil
}

// RemoveWAL removes the WAL file after a successful flush.
func RemoveWAL(filePath string) error {
	return os.Remove(filePath)
}
