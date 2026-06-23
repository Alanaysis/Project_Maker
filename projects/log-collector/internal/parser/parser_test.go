package parser

import (
	"testing"
	"time"
)

func TestParseJSON(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		level   Level
		message string
		wantErr bool
	}{
		{
			name:    "basic JSON log",
			line:    `{"level":"info","msg":"server started","port":8080}`,
			level:   LevelInfo,
			message: "server started",
		},
		{
			name:    "JSON with timestamp",
			line:    `{"level":"error","message":"connection failed","ts":"2024-01-01T12:00:00Z"}`,
			level:   LevelError,
			message: "connection failed",
		},
		{
			name:    "JSON with unknown level",
			line:    `{"msg":"test"}`,
			level:   LevelUnknown,
			message: "test",
		},
		{
			name:    "invalid JSON",
			line:    `{not json}`,
			wantErr: true,
		},
	}

	p := New(FormatJSON)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entry, err := p.Parse(tt.line, "test", 1)
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

func TestParseLogfmt(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		level   Level
		message string
	}{
		{
			name:    "basic logfmt",
			line:    "level=info msg=server_started port=8080",
			level:   LevelInfo,
			message: "server_started",
		},
		{
			name:    "logfmt with quoted values",
			line:    `level=error msg="connection failed" host="db.example.com"`,
			level:   LevelError,
			message: "connection failed",
		},
	}

	p := New(FormatLogfmt)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entry, err := p.Parse(tt.line, "test", 1)
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

func TestParseCommon(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		level   Level
		message string
	}{
		{
			name:    "standard common format",
			line:    "2024-01-15 10:30:00 [INFO] Application started successfully",
			level:   LevelInfo,
			message: "Application started successfully",
		},
		{
			name:    "error level",
			line:    "2024-01-15 10:30:01 [ERROR] Database connection timeout",
			level:   LevelError,
			message: "Database connection timeout",
		},
		{
			name:    "debug level",
			line:    "2024-01-15 10:30:02 [DEBUG] Processing request #1234",
			level:   LevelDebug,
			message: "Processing request #1234",
		},
	}

	p := New(FormatCommon)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entry, err := p.Parse(tt.line, "test", 1)
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

func TestParseCommonTimestamp(t *testing.T) {
	p := New(FormatCommon)
	entry, err := p.Parse("2024-01-15 10:30:00 [INFO] test", "test", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
	if !entry.Timestamp.Equal(expected) {
		t.Errorf("Timestamp = %v, want %v", entry.Timestamp, expected)
	}
}

func TestParseAuto(t *testing.T) {
	tests := []struct {
		name  string
		line  string
		level Level
	}{
		{
			name:  "auto-detect JSON",
			line:  `{"level":"warn","msg":"high memory"}`,
			level: LevelWarn,
		},
		{
			name:  "auto-detect logfmt",
			line:  "level=error msg=timeout",
			level: LevelError,
		},
		{
			name:  "auto-detect common",
			line:  "2024-01-15 10:30:00 [FATAL] system crash",
			level: LevelFatal,
		},
		{
			name:  "auto-detect plain text",
			line:  "just a plain text log line",
			level: LevelUnknown,
		},
	}

	p := New(FormatAuto)

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			entry, err := p.Parse(tt.line, "test", 1)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if entry.Level != tt.level {
				t.Errorf("Level = %v, want %v", entry.Level, tt.level)
			}
		})
	}
}

func TestParseMetadata(t *testing.T) {
	p := New(FormatJSON)
	entry, err := p.Parse(`{"msg":"test"}`, "app.log", 42)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Source != "app.log" {
		t.Errorf("Source = %q, want %q", entry.Source, "app.log")
	}
	if entry.LineNum != 42 {
		t.Errorf("LineNum = %d, want %d", entry.LineNum, 42)
	}
	if entry.Raw != `{"msg":"test"}` {
		t.Errorf("Raw = %q, want %q", entry.Raw, `{"msg":"test"}`)
	}
}

func TestParseEmptyLine(t *testing.T) {
	p := New(FormatAuto)
	_, err := p.Parse("", "test", 1)
	if err == nil {
		t.Fatal("expected error for empty line")
	}
}

func TestParseLevel(t *testing.T) {
	tests := []struct {
		input string
		want  Level
	}{
		{"DEBUG", LevelDebug},
		{"dbg", LevelDebug},
		{"INFO", LevelInfo},
		{"inf", LevelInfo},
		{"WARN", LevelWarn},
		{"WARNING", LevelWarn},
		{"ERROR", LevelError},
		{"err", LevelError},
		{"FATAL", LevelFatal},
		{"PANIC", LevelFatal},
		{"unknown", LevelUnknown},
		{"", LevelUnknown},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := ParseLevel(tt.input)
			if got != tt.want {
				t.Errorf("ParseLevel(%q) = %v, want %v", tt.input, got, tt.want)
			}
		})
	}
}

func TestLevelString(t *testing.T) {
	tests := []struct {
		level Level
		want  string
	}{
		{LevelDebug, "DEBUG"},
		{LevelInfo, "INFO"},
		{LevelWarn, "WARN"},
		{LevelError, "ERROR"},
		{LevelFatal, "FATAL"},
		{LevelUnknown, "UNKNOWN"},
	}

	for _, tt := range tests {
		if got := tt.level.String(); got != tt.want {
			t.Errorf("Level(%d).String() = %q, want %q", tt.level, got, tt.want)
		}
	}
}

func TestJSONFields(t *testing.T) {
	p := New(FormatJSON)
	entry, err := p.Parse(`{"level":"info","msg":"test","user":"alice","action":"login"}`, "test", 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if entry.Fields["user"] != "alice" {
		t.Errorf("Fields[user] = %q, want %q", entry.Fields["user"], "alice")
	}
	if entry.Fields["action"] != "login" {
		t.Errorf("Fields[action] = %q, want %q", entry.Fields["action"], "login")
	}
}
