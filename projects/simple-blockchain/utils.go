package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"log"
)

// IntToHex converts an int64 to a byte array
func IntToHex(num int64) []byte {
	buf := new(bytes.Buffer)
	err := binary.Write(buf, binary.BigEndian, num)
	if err != nil {
		log.Panic(err)
	}
	return buf.Bytes()
}

// BytesToInt converts a byte array to int64
func BytesToInt(data []byte) int64 {
	var num int64
	buf := bytes.NewReader(data)
	err := binary.Read(buf, binary.BigEndian, &num)
	if err != nil {
		log.Panic(err)
	}
	return num
}

// ReverseBytes reverses a byte array
func ReverseBytes(data []byte) []byte {
	for i, j := 0, len(data)-1; i < j; i, j = i+1, j-1 {
		data[i], data[j] = data[j], data[i]
	}
	return data
}

// PadBytes pads a byte array to a specific length
func PadBytes(data []byte, length int) []byte {
	if len(data) >= length {
		return data[:length]
	}
	padded := make([]byte, length)
	copy(padded[length-len(data):], data)
	return padded
}

// FormatHash formats a hash for display
func FormatHash(hash [32]byte) string {
	return fmt.Sprintf("%x", hash)
}

// Contains checks if a slice contains an element
func Contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// Unique removes duplicates from a string slice
func Unique(slice []string) []string {
	seen := make(map[string]bool)
	result := []string{}
	for _, s := range slice {
		if !seen[s] {
			seen[s] = true
			result = append(result, s)
		}
	}
	return result
}
