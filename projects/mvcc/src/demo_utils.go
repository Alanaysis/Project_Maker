package mvcc

import (
	"fmt"
	"math/rand"
	"strings"
	"sync"
	"time"
)

// DemoOutput provides a formatted output helper for demo programs.
type DemoOutput struct {
	mu       sync.Mutex
	prefix   string
	lines    []string
}

// NewDemoOutput creates a new demo output with the given prefix.
func NewDemoOutput(prefix string) *DemoOutput {
	return &DemoOutput{
		prefix: prefix,
		lines:  make([]string, 0),
	}
}

// Print formats and stores a line for output.
func (d *DemoOutput) Print(format string, args ...interface{}) {
	d.mu.Lock()
	defer d.mu.Unlock()
	msg := fmt.Sprintf(format, args...)
	line := fmt.Sprintf("[%s] %s", d.prefix, msg)
	d.lines = append(d.lines, line)
	fmt.Println(line)
}

// Println prints a blank line separator.
func (d *DemoOutput) Println() {
	fmt.Println(strings.Repeat("-", 60))
}

// PrintSection prints a section header.
func (d *DemoOutput) PrintSection(title string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	header := fmt.Sprintf("=== %s ===", title)
	fmt.Println(header)
}

// RandString generates a random string of the given length.
func RandString(n int) string {
	chars := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = chars[rand.Intn(len(chars))]
	}
	return string(b)
}

// Sleep simulates work duration.
func Sleep(ms int64) {
	time.Sleep(time.Duration(ms) * time.Millisecond)
}
