package main

import (
	"testing"
)

func TestIntToHex(t *testing.T) {
	tests := []struct {
		input    int64
		expected int64
	}{
		{0, 0},
		{1, 1},
		{255, 255},
		{65536, 65536},
		{-1, -1},
	}

	for _, tt := range tests {
		result := IntToHex(tt.input)
		roundTrip := BytesToInt(result)
		if roundTrip != tt.expected {
			t.Errorf("IntToHex(%d) -> BytesToInt = %d, want %d", tt.input, roundTrip, tt.expected)
		}
	}
}

func TestIntToHexLength(t *testing.T) {
	result := IntToHex(42)
	if len(result) != 8 {
		t.Errorf("IntToHex should return 8 bytes, got %d", len(result))
	}
}

func TestBytesToInt(t *testing.T) {
	// Encode then decode round-trip
	original := int64(123456789)
	data := IntToHex(original)
	result := BytesToInt(data)
	if result != original {
		t.Errorf("BytesToInt round-trip failed: got %d, want %d", result, original)
	}
}

func TestReverseBytes(t *testing.T) {
	tests := []struct {
		input    []byte
		expected []byte
	}{
		{[]byte{1, 2, 3, 4}, []byte{4, 3, 2, 1}},
		{[]byte{1}, []byte{1}},
		{[]byte{1, 2}, []byte{2, 1}},
		{[]byte{}, []byte{}},
	}

	for _, tt := range tests {
		// Copy input since ReverseBytes modifies in-place
		input := make([]byte, len(tt.input))
		copy(input, tt.input)

		result := ReverseBytes(input)
		if len(result) != len(tt.expected) {
			t.Errorf("ReverseBytes length mismatch: got %d, want %d", len(result), len(tt.expected))
			continue
		}
		for i := range result {
			if result[i] != tt.expected[i] {
				t.Errorf("ReverseBytes[%d] = %d, want %d", i, result[i], tt.expected[i])
			}
		}
	}
}

func TestPadBytes(t *testing.T) {
	tests := []struct {
		data     []byte
		length   int
		expected int
	}{
		{[]byte{1, 2, 3}, 5, 5},
		{[]byte{1, 2, 3}, 3, 3},
		{[]byte{1, 2, 3, 4, 5}, 3, 3}, // truncate
		{[]byte{}, 4, 4},
	}

	for _, tt := range tests {
		result := PadBytes(tt.data, tt.length)
		if len(result) != tt.expected {
			t.Errorf("PadBytes len=%d -> %d, want %d", len(tt.data), len(result), tt.expected)
		}
	}
}

func TestPadBytesPadsWithZeros(t *testing.T) {
	result := PadBytes([]byte{1, 2}, 4)
	if len(result) != 4 {
		t.Fatalf("Expected length 4, got %d", len(result))
	}
	// Leading bytes should be zero (left-padded)
	if result[0] != 0 || result[1] != 0 {
		t.Error("Leading bytes should be zero-padded")
	}
	// Trailing bytes should contain the data
	if result[2] != 1 || result[3] != 2 {
		t.Error("Trailing bytes should contain original data")
	}
}

func TestPadBytesTruncate(t *testing.T) {
	result := PadBytes([]byte{1, 2, 3, 4, 5}, 3)
	if len(result) != 3 {
		t.Fatalf("Expected length 3, got %d", len(result))
	}
	if result[0] != 1 || result[1] != 2 || result[2] != 3 {
		t.Error("Truncated result should contain first N bytes")
	}
}

func TestFormatHash(t *testing.T) {
	var hash [32]byte
	hash[0] = 0xAB
	hash[1] = 0xCD
	hash[31] = 0xEF

	result := FormatHash(hash)
	if len(result) != 64 {
		t.Errorf("FormatHash should return 64 hex chars, got %d", len(result))
	}
	if result[:2] != "ab" {
		t.Errorf("FormatHash first byte should be 'ab', got '%s'", result[:2])
	}
}

func TestContains(t *testing.T) {
	slice := []string{"apple", "banana", "cherry"}

	if !Contains(slice, "apple") {
		t.Error("Contains should find 'apple'")
	}
	if !Contains(slice, "banana") {
		t.Error("Contains should find 'banana'")
	}
	if Contains(slice, "grape") {
		t.Error("Contains should not find 'grape'")
	}
	if Contains([]string{}, "anything") {
		t.Error("Contains on empty slice should return false")
	}
}

func TestUnique(t *testing.T) {
	tests := []struct {
		input    []string
		expected int
	}{
		{[]string{"a", "b", "c"}, 3},
		{[]string{"a", "a", "b", "b"}, 2},
		{[]string{"a", "a", "a"}, 1},
		{[]string{}, 0},
	}

	for _, tt := range tests {
		result := Unique(tt.input)
		if len(result) != tt.expected {
			t.Errorf("Unique(%v) returned %d items, want %d", tt.input, len(result), tt.expected)
		}
	}
}

func TestUniquePreservesOrder(t *testing.T) {
	input := []string{"c", "a", "b", "a", "c"}
	result := Unique(input)

	if len(result) != 3 {
		t.Fatalf("Expected 3 unique items, got %d", len(result))
	}
	if result[0] != "c" || result[1] != "a" || result[2] != "b" {
		t.Errorf("Unique should preserve first-occurrence order, got %v", result)
	}
}
