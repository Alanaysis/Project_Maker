package parser

import (
	"testing"
)

func TestRegexParserBasic(t *testing.T) {
	pattern := `^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<msg>.+)$`
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	tests := []struct {
		name    string
		line    string
		level   Level
		message string
		wantErr bool
	}{
		{
			name:    "info level",
			line:    "2024-01-15 10:30:00 [INFO] Application started",
			level:   LevelInfo,
			message: "Application started",
		},
		{
			name:    "error level",
			line:    "2024-01-15 10:30:01 [ERROR] Database connection failed",
			level:   LevelError,
			message: "Database connection failed",
		},
		{
			name:    "debug level",
			line:    "2024-01-15 10:30:02 [DEBUG] Processing request #1234",
			level:   LevelDebug,
			message: "Processing request #1234",
		},
		{
			name:    "no match",
			line:    "this line does not match the pattern",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entry, err := p.Parse(tt.line, "test.log", 1)
			if tt.wantErr {
				if err == nil {
					t.Fatal("expected error")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if entry.Level != tt.level {
				t.Errorf("Level = %v, want %v", entry.Level, tt.level)
			}
			if entry.Message != tt.message {
				t.Errorf("Message = %q, want %q", entry.Message, tt.message)
			}
		})
	}
}

func TestRegexParserCustomFields(t *testing.T) {
	pattern := `^(?P<ip>\S+) (?P<time>\S+) \[(?P<level>\w+)\] (?P<msg>.+)$`
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	entry, err := p.Parse("192.168.1.1 2024-01-15 [INFO] request received", "access.log", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Fields["ip"] != "192.168.1.1" {
		t.Errorf("Fields[ip] = %q, want %q", entry.Fields["ip"], "192.168.1.1")
	}
	if entry.Message != "request received" {
		t.Errorf("Message = %q, want %q", entry.Message, "request received")
	}
}

func TestRegexParserTimestamp(t *testing.T) {
	pattern := `^(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?) (?P<msg>.+)$`
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	entry, err := p.Parse("2024-01-15T10:30:00Z test message", "test.log", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Timestamp.Year() != 2024 {
		t.Errorf("Timestamp year = %d, want 2024", entry.Timestamp.Year())
	}
	if entry.Timestamp.Month() != 1 {
		t.Errorf("Timestamp month = %d, want 1", entry.Timestamp.Month())
	}
}

func TestRegexParserMetadata(t *testing.T) {
	pattern := `^\[(?P<level>\w+)\] (?P<msg>.+)$`
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	entry, err := p.Parse("[WARN] disk space low", "system.log", 42)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Source != "system.log" {
		t.Errorf("Source = %q, want %q", entry.Source, "system.log")
	}
	if entry.LineNum != 42 {
		t.Errorf("LineNum = %d, want %d", entry.LineNum, 42)
	}
	if entry.Raw != "[WARN] disk space low" {
		t.Errorf("Raw = %q, want %q", entry.Raw, "[WARN] disk space low")
	}
}

func TestRegexParserInvalidPattern(t *testing.T) {
	_, err := NewRegexParser("[invalid")
	if err == nil {
		t.Fatal("expected error for invalid regex")
	}
}

func TestRegexParserApachePattern(t *testing.T) {
	pattern := CommonPatterns["apache"]
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	line := `192.168.1.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326`
	entry, err := p.Parse(line, "access.log", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Fields["remote"] != "192.168.1.1" {
		t.Errorf("Fields[remote] = %q, want %q", entry.Fields["remote"], "192.168.1.1")
	}
	if entry.Fields["method"] != "GET" {
		t.Errorf("Fields[method] = %q, want %q", entry.Fields["method"], "GET")
	}
	if entry.Fields["status"] != "200" {
		t.Errorf("Fields[status] = %q, want %q", entry.Fields["status"], "200")
	}
}

func TestRegexParserSyslogPattern(t *testing.T) {
	pattern := CommonPatterns["syslog"]
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	line := `Jan 15 10:30:00 myhost sshd[1234]: Accepted publickey for user`
	entry, err := p.Parse(line, "syslog", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Fields["host"] != "myhost" {
		t.Errorf("Fields[host] = %q, want %q", entry.Fields["host"], "myhost")
	}
	if entry.Fields["app"] != "sshd" {
		t.Errorf("Fields[app] = %q, want %q", entry.Fields["app"], "sshd")
	}
	if entry.Message != "Accepted publickey for user" {
		t.Errorf("Message = %q, want %q", entry.Message, "Accepted publickey for user")
	}
}

func TestRegexParserGenericPattern(t *testing.T) {
	pattern := CommonPatterns["generic"]
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	tests := []struct {
		line  string
		level Level
	}{
		{"2024-01-15 10:30:00 INFO server started", LevelInfo},
		{"2024-01-15T10:30:00 ERROR connection failed", LevelError},
		{"2024-01-15 10:30:00.123 WARN slow query", LevelWarn},
	}

	for _, tt := range tests {
		entry, err := p.Parse(tt.line, "test", 1)
		if err != nil {
			t.Fatalf("unexpected error for %q: %v", tt.line, err)
		}
		if entry.Level != tt.level {
			t.Errorf("line %q: Level = %v, want %v", tt.line, entry.Level, tt.level)
		}
	}
}

func TestRegexParserNoNamedGroups(t *testing.T) {
	// Pattern without named groups should still work
	pattern := `^\d+ .+$`
	p, err := NewRegexParser(pattern)
	if err != nil {
		t.Fatalf("NewRegexParser error: %v", err)
	}

	entry, err := p.Parse("12345 some message", "test", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Level != LevelUnknown {
		t.Errorf("Level = %v, want UNKNOWN", entry.Level)
	}
	if entry.Message != "" {
		t.Errorf("Message = %q, want empty", entry.Message)
	}
}

func TestCommonPatternsValid(t *testing.T) {
	for name, pattern := range CommonPatterns {
		t.Run(name, func(t *testing.T) {
			_, err := NewRegexParser(pattern)
			if err != nil {
				t.Errorf("pattern %q is invalid: %v", name, err)
			}
		})
	}
}
