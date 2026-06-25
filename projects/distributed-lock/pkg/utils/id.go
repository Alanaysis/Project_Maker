// Package utils provides utility functions for distributed locks.
package utils

import (
	"fmt"
	"os"
	"sync/atomic"

	"github.com/google/uuid"
)

var counter uint64

// GenerateID generates a unique identifier for lock ownership.
// Format: hostname-pid-uuid
func GenerateID() string {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}
	return fmt.Sprintf("%s-%d-%s", hostname, os.Getpid(), uuid.New().String())
}

// GenerateShortID generates a shorter unique identifier.
// Format: uuid (first 8 chars)
func GenerateShortID() string {
	return uuid.New().String()[:8]
}

// GenerateSequenceID generates a monotonically increasing sequence ID.
func GenerateSequenceID(prefix string) string {
	n := atomic.AddUint64(&counter, 1)
	return fmt.Sprintf("%s-%d", prefix, n)
}
