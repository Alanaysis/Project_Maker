package transport

import (
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestTCPReceiver(t *testing.T) {
	output := make(chan RawLog, 100)
	receiver := NewTCPReceiver("127.0.0.1:0", output) // Port 0 = auto-assign

	if err := receiver.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}
	defer receiver.Stop()

	addr := receiver.Addr()

	// Connect and send log lines
	conn, err := net.Dial("tcp", addr)
	if err != nil {
		t.Fatalf("Dial error: %v", err)
	}

	fmt.Fprintln(conn, "first log line")
	fmt.Fprintln(conn, "second log line")
	fmt.Fprintln(conn, "third log line")
	conn.Close()

	// Wait for lines to arrive
	time.Sleep(200 * time.Millisecond)

	close(output)
	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 3 {
		t.Fatalf("expected 3 log lines, got %d", len(logs))
	}

	expected := []string{"first log line", "second log line", "third log line"}
	for i, exp := range expected {
		if logs[i].Line != exp {
			t.Errorf("log[%d].Line = %q, want %q", i, logs[i].Line, exp)
		}
	}

	// Verify source contains tcp prefix
	if !strings.HasPrefix(logs[0].Source, "tcp:") {
		t.Errorf("Source = %q, want tcp: prefix", logs[0].Source)
	}
}

func TestTCPReceiverMultipleClients(t *testing.T) {
	output := make(chan RawLog, 100)
	receiver := NewTCPReceiver("127.0.0.1:0", output)

	if err := receiver.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}
	defer receiver.Stop()

	addr := receiver.Addr()

	// Connect two clients
	conn1, err := net.Dial("tcp", addr)
	if err != nil {
		t.Fatalf("Dial 1 error: %v", err)
	}

	conn2, err := net.Dial("tcp", addr)
	if err != nil {
		t.Fatalf("Dial 2 error: %v", err)
	}

	fmt.Fprintln(conn1, "from client 1")
	fmt.Fprintln(conn2, "from client 2")
	conn1.Close()
	conn2.Close()

	time.Sleep(200 * time.Millisecond)

	close(output)
	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 log lines, got %d", len(logs))
	}
}

func TestTCPReceiverSkipsEmptyLines(t *testing.T) {
	output := make(chan RawLog, 100)
	receiver := NewTCPReceiver("127.0.0.1:0", output)

	if err := receiver.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}
	defer receiver.Stop()

	conn, err := net.Dial("tcp", receiver.Addr())
	if err != nil {
		t.Fatalf("Dial error: %v", err)
	}

	fmt.Fprintln(conn, "line 1")
	fmt.Fprintln(conn, "")
	fmt.Fprintln(conn, "")
	fmt.Fprintln(conn, "line 2")
	conn.Close()

	time.Sleep(200 * time.Millisecond)

	close(output)
	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 non-empty lines, got %d", len(logs))
	}
}

func TestUDPReceiver(t *testing.T) {
	output := make(chan RawLog, 100)
	receiver := NewUDPReceiver("127.0.0.1:0", output)

	if err := receiver.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}
	defer receiver.Stop()

	addr := receiver.Addr()

	// Send UDP packets
	conn, err := net.Dial("udp", addr)
	if err != nil {
		t.Fatalf("Dial error: %v", err)
	}
	defer conn.Close()

	fmt.Fprintln(conn, "udp log line 1")
	fmt.Fprintln(conn, "udp log line 2")

	time.Sleep(200 * time.Millisecond)

	close(output)
	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 2 {
		t.Fatalf("expected 2 UDP log lines, got %d", len(logs))
	}

	if logs[0].Line != "udp log line 1" {
		t.Errorf("line 1 = %q, want %q", logs[0].Line, "udp log line 1")
	}

	if !strings.HasPrefix(logs[0].Source, "udp:") {
		t.Errorf("Source = %q, want udp: prefix", logs[0].Source)
	}
}

func TestUDPReceiverSkipsEmpty(t *testing.T) {
	output := make(chan RawLog, 100)
	receiver := NewUDPReceiver("127.0.0.1:0", output)

	if err := receiver.Start(); err != nil {
		t.Fatalf("Start() error: %v", err)
	}
	defer receiver.Stop()

	conn, err := net.Dial("udp", receiver.Addr())
	if err != nil {
		t.Fatalf("Dial error: %v", err)
	}
	defer conn.Close()

	// Send empty line
	fmt.Fprintln(conn, "")
	// Send non-empty line
	fmt.Fprintln(conn, "valid line")

	time.Sleep(200 * time.Millisecond)

	close(output)
	var logs []RawLog
	for log := range output {
		logs = append(logs, log)
	}

	if len(logs) != 1 {
		t.Fatalf("expected 1 non-empty line, got %d", len(logs))
	}
}

func TestFileWriter(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	fw, err := NewFileWriter(FileWriterConfig{Path: path})
	if err != nil {
		t.Fatalf("NewFileWriter error: %v", err)
	}
	defer fw.Close()

	// Write some lines
	if err := fw.Write("line 1"); err != nil {
		t.Fatalf("Write error: %v", err)
	}
	if err := fw.Write("line 2"); err != nil {
		t.Fatalf("Write error: %v", err)
	}
	if err := fw.Write("line 3"); err != nil {
		t.Fatalf("Write error: %v", err)
	}

	fw.Close()

	// Read the file and verify
	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile error: %v", err)
	}

	lines := strings.Split(strings.TrimSpace(string(content)), "\n")
	if len(lines) != 3 {
		t.Fatalf("expected 3 lines in file, got %d", len(lines))
	}

	expected := []string{"line 1", "line 2", "line 3"}
	for i, exp := range expected {
		if lines[i] != exp {
			t.Errorf("line[%d] = %q, want %q", i, lines[i], exp)
		}
	}
}

func TestFileWriterWriteEntry(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	fw, err := NewFileWriter(FileWriterConfig{Path: path})
	if err != nil {
		t.Fatalf("NewFileWriter error: %v", err)
	}
	defer fw.Close()

	ts := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
	if err := fw.WriteEntry(ts, "INFO", "app.log", "server started"); err != nil {
		t.Fatalf("WriteEntry error: %v", err)
	}

	fw.Close()

	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("ReadFile error: %v", err)
	}

	expected := "2024-01-15 10:30:00 INFO  [app.log] server started"
	actual := strings.TrimSpace(string(content))
	if actual != expected {
		t.Errorf("content = %q, want %q", actual, expected)
	}
}

func TestFileWriterRotation(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "test.log")

	fw, err := NewFileWriter(FileWriterConfig{
		Path:    path,
		MaxSize: 50, // Very small for testing
	})
	if err != nil {
		t.Fatalf("NewFileWriter error: %v", err)
	}
	defer fw.Close()

	// Write enough to trigger rotation
	for i := 0; i < 10; i++ {
		fw.Write(fmt.Sprintf("log line number %d with some padding", i))
	}

	// Check that a rotated file exists
	entries, _ := os.ReadDir(dir)
	rotatedCount := 0
	for _, e := range entries {
		if e.Name() != "test.log" && strings.HasPrefix(e.Name(), "test.log.") {
			rotatedCount++
		}
	}

	if rotatedCount == 0 {
		t.Error("expected at least one rotated file")
	}
}

func TestFileWriterInvalidPath(t *testing.T) {
	_, err := NewFileWriter(FileWriterConfig{Path: "/nonexistent/dir/test.log"})
	if err == nil {
		t.Fatal("expected error for invalid path")
	}
}
