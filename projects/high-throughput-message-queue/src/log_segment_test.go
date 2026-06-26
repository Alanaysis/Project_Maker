package queue

import (
	"os"
	"testing"
)

// TestLogSegmentCreation verifies log segment creation.
func TestLogSegmentCreation(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("failed to create segment: %v", err)
	}
	defer seg.Close()

	if seg.BaseOffset() != 0 {
		t.Errorf("expected base offset 0, got %d", seg.BaseOffset())
	}
	if seg.Size() != 0 {
		t.Errorf("expected size 0, got %d", seg.Size())
	}
}

// TestLogSegmentAppend verifies appending messages to a segment.
func TestLogSegmentAppend(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("failed to create segment: %v", err)
	}
	defer seg.Close()

	msg := NewMessage([]byte("key"), []byte("value"))
	offset, err := seg.Append(msg)
	if err != nil {
		t.Fatalf("append failed: %v", err)
	}

	if offset != 0 {
		t.Errorf("expected offset 0, got %d", offset)
	}
	if seg.Size() == 0 {
		t.Error("segment size should be > 0 after append")
	}
}

// TestLogSegmentMultipleAppends verifies multiple appends.
func TestLogSegmentMultipleAppends(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("failed to create segment: %v", err)
	}
	defer seg.Close()

	numMessages := 10
	for i := 0; i < numMessages; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		offset, err := seg.Append(msg)
		if err != nil {
			t.Fatalf("append %d failed: %v", i, err)
		}
		if offset != int64(i) {
			t.Errorf("expected offset %d, got %d", i, offset)
		}
	}

	if seg.NextOffset() != int64(numMessages) {
		t.Errorf("expected next offset %d, got %d", numMessages, seg.NextOffset())
	}
}

// TestLogSegmentRead verifies reading messages from a segment.
func TestLogSegmentRead(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("failed to create segment: %v", err)
	}
	defer seg.Close()

	// Write messages
	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		seg.Append(msg)
	}

	// Read from offset 0
	messages, err := seg.Read(0, 10)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}
	if len(messages) != 5 {
		t.Errorf("expected 5 messages, got %d", len(messages))
	}

	// Verify message content
	for i, msg := range messages {
		if string(msg.Key) != fmt.Sprintf("key-%d", i) {
			t.Errorf("message %d key mismatch: expected 'key-%d', got '%s'", i, i, msg.Key)
		}
		if string(msg.Value) != fmt.Sprintf("value-%d", i) {
			t.Errorf("message %d value mismatch: expected 'value-%d', got '%s'", i, i, msg.Value)
		}
		if msg.Offset != int64(i) {
			t.Errorf("message %d offset mismatch: expected %d, got %d", i, i, msg.Offset)
		}
	}
}

// TestLogSegmentReadFromOffset verifies reading from a specific offset.
func TestLogSegmentReadFromOffset(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("failed to create segment: %v", err)
	}
	defer seg.Close()

	// Write 10 messages
	for i := 0; i < 10; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		seg.Append(msg)
	}

	// Read from offset 5
	messages, err := seg.Read(5, 10)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}

	// Should get messages from offset 5 onwards (up to 10 max)
	if len(messages) == 0 {
		t.Error("expected some messages when reading from offset 5")
	}
}

// TestLogSegmentOpen verifies opening an existing segment.
func TestLogSegmentOpen(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	// Create and write to a segment
	seg1, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}

	for i := 0; i < 5; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		seg1.Append(msg)
	}
	seg1.Close()

	// Open the segment for reading
	seg2, err := OpenLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("open failed: %v", err)
	}
	defer seg2.Close()

	if seg2.BaseOffset() != 0 {
		t.Errorf("expected base offset 0, got %d", seg2.BaseOffset())
	}
	if seg2.Size() == 0 {
		t.Error("opened segment should have non-zero size")
	}
}

// TestLogSegmentDelete verifies segment deletion.
func TestLogSegmentDelete(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}

	// Write some data
	msg := NewMessage([]byte("key"), []byte("value"))
	seg.Append(msg)
	seg.Close()

	// Verify file exists
	segPath := dir + "/00000000000000000000"
	if _, err := os.Stat(segPath); os.IsNotExist(err) {
		t.Error("segment file should exist before delete")
	}

	// Delete
	seg.Delete()

	// Verify file is gone
	_, err = os.Stat(segPath)
	if !os.IsNotExist(err) {
		t.Error("segment file should be removed after delete")
	}
}

// TestLogSegmentLargeMessage verifies handling of large messages.
func TestLogSegmentLargeMessage(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}
	defer seg.Close()

	// Create a large message (1MB)
	largeValue := make([]byte, 1024*1024)
	for i := range largeValue {
		largeValue[i] = byte(i % 256)
	}

	msg := NewMessage([]byte("large-key"), largeValue)
	offset, err := seg.Append(msg)
	if err != nil {
		t.Fatalf("append failed: %v", err)
	}

	if offset != 0 {
		t.Errorf("expected offset 0, got %d", offset)
	}

	// Read back
	messages, err := seg.Read(0, 1)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}
	if len(messages) != 1 {
		t.Errorf("expected 1 message, got %d", len(messages))
	}
	if len(messages[0].Value) != len(largeValue) {
		t.Errorf("value length mismatch: expected %d, got %d", len(largeValue), len(messages[0].Value))
	}
}

// TestLogSegmentSegmentFilename verifies segment filename parsing.
func TestLogSegmentFilenameParsing(t *testing.T) {
	offset, err := parseOffsetFilename("00000000000000000000")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if offset != 0 {
		t.Errorf("expected offset 0, got %d", offset)
	}

	offset, err = parseOffsetFilename("00000000000000000042")
	if err != nil {
		t.Fatalf("parse failed: %v", err)
	}
	if offset != 42 {
		t.Errorf("expected offset 42, got %d", offset)
	}

	_, err = parseOffsetFilename("invalid")
	if err == nil {
		t.Error("should error on invalid filename")
	}
}

// TestLogSegmentAppendAfterClose verifies error after close.
func TestLogSegmentAppendAfterClose(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}
	seg.Close()

	msg := NewMessage([]byte("key"), []byte("value"))
	_, err = seg.Append(msg)
	if err == nil {
		t.Error("should error when appending to closed segment")
	}
}

// TestLogSegmentMaxMessagesLimit verifies max messages parameter.
func TestLogSegmentMaxMessagesLimit(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}
	defer seg.Close()

	// Write 10 messages
	for i := 0; i < 10; i++ {
		msg := NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		seg.Append(msg)
	}

	// Limit to 3 messages
	messages, err := seg.Read(0, 3)
	if err != nil {
		t.Fatalf("read failed: %v", err)
	}
	if len(messages) > 3 {
		t.Errorf("expected at most 3 messages, got %d", len(messages))
	}
}

// TestLogSegmentReadInvalidOffset verifies error on invalid offset.
func TestLogSegmentReadInvalidOffset(t *testing.T) {
	dir := t.TempDir()
	storageConfig := DefaultStorageConfig(dir)

	seg, err := NewLogSegment(dir, "00000000000000000000", storageConfig)
	if err != nil {
		t.Fatalf("create failed: %v", err)
	}
	defer seg.Close()

	// Read from offset before base offset
	_, err = seg.Read(-1, 10)
	if err == nil {
		t.Error("should error on negative offset")
	}
}
