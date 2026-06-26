package queue

import (
	"os"
	"testing"
)

// TestMessageCreation verifies message creation.
func TestMessageCreation(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))

	if msg.Key == nil {
		t.Error("key should not be nil")
	}
	if msg.Value == nil {
		t.Error("value should not be nil")
	}
	if msg.Offset != -1 {
		t.Errorf("expected offset -1, got %d", msg.Offset)
	}
	if msg.Partition != -1 {
		t.Errorf("expected partition -1, got %d", msg.Partition)
	}
	if msg.Timestamp == 0 {
		t.Error("timestamp should be non-zero")
	}
}

// TestMessageWithHeader verifies adding headers.
func TestMessageWithHeader(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))
	msg.WithHeader("type", "order").WithHeader("priority", "high")

	if msg.Headers["type"] != "order" {
		t.Errorf("expected type='order', got '%s'", msg.Headers["type"])
	}
	if msg.Headers["priority"] != "high" {
		t.Errorf("expected priority='high', got '%s'", msg.Headers["priority"])
	}
	if len(msg.Headers) != 2 {
		t.Errorf("expected 2 headers, got %d", len(msg.Headers))
	}
}

// TestMessageMarshalUnmarshal verifies serialization round-trip.
func TestMessageMarshalUnmarshal(t *testing.T) {
	original := NewMessage([]byte("test-key"), []byte("test-value"))
	original.Offset = 42
	original.Partition = 1
	original.WithHeader("type", "test")
	original.WithHeader("source", "test")

	// Marshal
	data, err := original.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("marshaled data should not be empty")
	}

	// Unmarshal
	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}

	// Verify
	if string(restored.Key) != string(original.Key) {
		t.Errorf("key mismatch: expected '%s', got '%s'", original.Key, restored.Key)
	}
	if string(restored.Value) != string(original.Value) {
		t.Errorf("value mismatch: expected '%s', got '%s'", original.Value, restored.Value)
	}
	if restored.Offset != original.Offset {
		t.Errorf("offset mismatch: expected %d, got %d", original.Offset, restored.Offset)
	}
	if restored.Partition != original.Partition {
		t.Errorf("partition mismatch: expected %d, got %d", original.Partition, restored.Partition)
	}
	if len(restored.Headers) != len(original.Headers) {
		t.Errorf("headers count mismatch: expected %d, got %d", len(original.Headers), len(restored.Headers))
	}
}

// TestMessageMarshalUnmarshalNilKey verifies handling of nil key.
func TestMessageMarshalUnmarshalNilKey(t *testing.T) {
	msg := NewMessage(nil, []byte("value"))
	data, err := msg.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}
	if restored.Key != nil {
		t.Error("key should be nil")
	}
}

// TestMessageChecksum verifies checksum consistency.
func TestMessageChecksum(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))
	cs1 := msg.Checksum()

	// Checksum should be consistent
	cs2 := msg.Checksum()
	if cs1 != cs2 {
		t.Errorf("checksum inconsistent: %d vs %d", cs1, cs2)
	}

	// Different message should have different checksum
	msg2 := NewMessage([]byte("key"), []byte("different-value"))
	cs3 := msg2.Checksum()
	if cs1 == cs3 {
		t.Error("different messages should have different checksums")
	}
}

// TestMessageSizeEstimate verifies size estimation.
func TestMessageSizeEstimate(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte("value"))
	size := msg.SizeEstimate()

	if size <= 0 {
		t.Errorf("expected positive size, got %d", size)
	}

	// Larger value should produce larger estimate
	msg2 := NewMessage([]byte("key"), []byte("a very long value that is definitely bigger than the first one"))
	size2 := msg2.SizeEstimate()
	if size2 <= size {
		t.Errorf("larger value should have larger size estimate: %d vs %d", size, size2)
	}
}

// TestMessageMarshalUnmarshalEmptyValue verifies empty value handling.
func TestMessageMarshalUnmarshalEmptyValue(t *testing.T) {
	msg := NewMessage([]byte("key"), []byte(""))
	data, err := msg.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}
	if string(restored.Value) != "" {
		t.Errorf("expected empty value, got '%s'", restored.Value)
	}
}

// TestMessageMarshalUnmarshalLargeValue verifies large value handling.
func TestMessageMarshalUnmarshalLargeValue(t *testing.T) {
	value := make([]byte, 1024)
	for i := range value {
		value[i] = byte(i % 256)
	}

	msg := NewMessage([]byte("key"), value)
	data, err := msg.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}
	if len(restored.Value) != len(value) {
		t.Errorf("value length mismatch: expected %d, got %d", len(value), len(restored.Value))
	}
	for i := range value {
		if restored.Value[i] != value[i] {
			t.Errorf("value mismatch at index %d", i)
			break
		}
	}
}

// TestMessageUnmarshalShortData verifies error on truncated data.
func TestMessageUnmarshalShortData(t *testing.T) {
	msg := &Message{}
	err := msg.Unmarshal([]byte{})
	if err == nil {
		t.Error("should error on empty data")
	}

	err = msg.Unmarshal([]byte{1, 2, 3})
	if err == nil {
		t.Error("should error on short data")
	}
}

// TestMessageWithHeadersOnly verifies message with only headers.
func TestMessageWithHeadersOnly(t *testing.T) {
	msg := NewMessage(nil, []byte("value"))
	msg.WithHeader("header1", "val1").WithHeader("header2", "val2")

	data, err := msg.Marshal()
	if err != nil {
		t.Fatalf("marshal failed: %v", err)
	}

	restored := &Message{}
	if err := restored.Unmarshal(data); err != nil {
		t.Fatalf("unmarshal failed: %v", err)
	}

	if len(restored.Headers) != 2 {
		t.Errorf("expected 2 headers, got %d", len(restored.Headers))
	}
}

// TestMessageCreateMultiple verifies creating multiple messages.
func TestMessageCreateMultiple(t *testing.T) {
	messages := make([]*Message, 10)
	for i := 0; i < 10; i++ {
		key := []byte(fmt.Sprintf("key-%d", i))
		value := []byte(fmt.Sprintf("value-%d", i))
		messages[i] = NewMessage(key, value)
	}

	// All should have unique timestamps (in practice)
	for i := 0; i < 10; i++ {
		if messages[i].Key == nil || messages[i].Value == nil {
			t.Errorf("message %d should have non-nil key/value", i)
		}
	}
}
