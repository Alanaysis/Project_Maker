package filter

import (
	"testing"
)

func TestLevelFilter(t *testing.T) {
	tests := []struct {
		name     string
		minLevel Level
		level    Level
		want     bool
	}{
		{"debug passes debug filter", LevelDebug, LevelDebug, true},
		{"info passes debug filter", LevelDebug, LevelInfo, true},
		{"error passes debug filter", LevelDebug, LevelError, true},
		{"debug fails info filter", LevelInfo, LevelDebug, false},
		{"info passes info filter", LevelInfo, LevelInfo, true},
		{"error passes info filter", LevelInfo, LevelError, true},
		{"info fails error filter", LevelError, LevelInfo, false},
		{"error passes error filter", LevelError, LevelError, true},
		{"fatal passes error filter", LevelError, LevelFatal, true},
		{"unknown fails debug filter", LevelDebug, LevelUnknown, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f := &LevelFilter{MinLevel: tt.minLevel}
			entry := Entry{Level: tt.level, Message: "test"}
			if got := f.Match(entry); got != tt.want {
				t.Errorf("LevelFilter(%v).Match(%v) = %v, want %v", tt.minLevel, tt.level, got, tt.want)
			}
		})
	}
}

func TestKeywordFilter(t *testing.T) {
	tests := []struct {
		name          string
		keyword       string
		caseSensitive bool
		exclude       bool
		message       string
		want          bool
	}{
		{"match keyword", "error", false, false, "an error occurred", true},
		{"no match keyword", "error", false, false, "all is well", false},
		{"case insensitive", "ERROR", false, false, "an error occurred", true},
		{"case sensitive match", "Error", true, false, "an Error occurred", true},
		{"case sensitive no match", "Error", true, false, "an error occurred", false},
		{"exclude match", "error", false, true, "an error occurred", false},
		{"exclude no match", "error", false, true, "all is well", true},
		{"partial match", "timeout", false, false, "connection timeout error", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f := &KeywordFilter{
				Keyword:       tt.keyword,
				CaseSensitive: tt.caseSensitive,
				Exclude:       tt.exclude,
			}
			entry := Entry{Level: LevelInfo, Message: tt.message}
			if got := f.Match(entry); got != tt.want {
				t.Errorf("KeywordFilter(%q).Match(%q) = %v, want %v", tt.keyword, tt.message, got, tt.want)
			}
		})
	}
}

func TestRegexFilter(t *testing.T) {
	tests := []struct {
		name    string
		pattern string
		exclude bool
		message string
		want    bool
		wantErr bool
	}{
		{"simple match", `error`, false, "an error occurred", true, false},
		{"simple no match", `error`, false, "all is well", false, false},
		{"digit match", `\d{3}`, false, "status code 500", true, false},
		{"digit no match", `\d{3}`, false, "status ok", false, false},
		{"complex pattern", `timeout|refused`, false, "connection timeout", true, false},
		{"complex no match", `timeout|refused`, false, "connection ok", false, false},
		{"exclude match", `error`, true, "an error occurred", false, false},
		{"exclude no match", `error`, true, "all is well", true, false},
		{"invalid regex", `[invalid`, false, "test", false, true},
		{"anchored pattern", `^start`, false, "start of line", true, false},
		{"anchored no match", `^start`, false, "not start", false, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f, err := NewRegexFilter(tt.pattern, tt.exclude)
			if tt.wantErr {
				if err == nil {
					t.Fatal("expected error for invalid regex")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			entry := Entry{Level: LevelInfo, Message: tt.message}
			if got := f.Match(entry); got != tt.want {
				t.Errorf("RegexFilter(%q).Match(%q) = %v, want %v", tt.pattern, tt.message, got, tt.want)
			}
		})
	}
}

func TestSourceFilter(t *testing.T) {
	tests := []struct {
		name    string
		source  string
		exclude bool
		entry   string
		want    bool
	}{
		{"match source", "app.log", false, "app.log", true},
		{"partial match", "app", false, "app.log", true},
		{"no match", "error", false, "app.log", false},
		{"exclude match", "app.log", true, "app.log", false},
		{"exclude no match", "error", true, "app.log", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			f := &SourceFilter{Source: tt.source, Exclude: tt.exclude}
			entry := Entry{Level: LevelInfo, Message: "test", Source: tt.entry}
			if got := f.Match(entry); got != tt.want {
				t.Errorf("SourceFilter(%q).Match(%q) = %v, want %v", tt.source, tt.entry, got, tt.want)
			}
		})
	}
}

func TestChain(t *testing.T) {
	levelFilter := &LevelFilter{MinLevel: LevelError}
	keywordFilter := &KeywordFilter{Keyword: "timeout"}

	chain := NewChain(levelFilter, keywordFilter)

	// Both match
	entry1 := Entry{Level: LevelError, Message: "connection timeout"}
	if !chain.Match(entry1) {
		t.Error("expected chain to match entry with error level and timeout keyword")
	}

	// Only level matches
	entry2 := Entry{Level: LevelError, Message: "server started"}
	if chain.Match(entry2) {
		t.Error("expected chain to reject entry without timeout keyword")
	}

	// Only keyword matches
	entry3 := Entry{Level: LevelInfo, Message: "connection timeout"}
	if chain.Match(entry3) {
		t.Error("expected chain to reject entry with info level")
	}

	// Neither matches
	entry4 := Entry{Level: LevelInfo, Message: "server started"}
	if chain.Match(entry4) {
		t.Error("expected chain to reject entry with neither match")
	}
}

func TestMatchAny(t *testing.T) {
	levelFilter := &LevelFilter{MinLevel: LevelError}
	keywordFilter := &KeywordFilter{Keyword: "timeout"}

	any := &MatchAny{Filters: []Filter{levelFilter, keywordFilter}}

	// Both match
	entry1 := Entry{Level: LevelError, Message: "connection timeout"}
	if !any.Match(entry1) {
		t.Error("expected any to match when both match")
	}

	// Only level matches
	entry2 := Entry{Level: LevelError, Message: "server started"}
	if !any.Match(entry2) {
		t.Error("expected any to match when level matches")
	}

	// Only keyword matches
	entry3 := Entry{Level: LevelInfo, Message: "connection timeout"}
	if !any.Match(entry3) {
		t.Error("expected any to match when keyword matches")
	}

	// Neither matches
	entry4 := Entry{Level: LevelInfo, Message: "server started"}
	if any.Match(entry4) {
		t.Error("expected any to reject when neither matches")
	}
}

func TestApply(t *testing.T) {
	entries := []Entry{
		{Level: LevelInfo, Message: "server started"},
		{Level: LevelError, Message: "connection timeout"},
		{Level: LevelWarn, Message: "high memory"},
		{Level: LevelError, Message: "database error"},
		{Level: LevelInfo, Message: "request processed"},
	}

	// Apply level filter
	levelFilter := &LevelFilter{MinLevel: LevelError}
	result := Apply(entries, levelFilter)
	if len(result) != 2 {
		t.Fatalf("expected 2 error entries, got %d", len(result))
	}

	// Apply keyword filter
	keywordFilter := &KeywordFilter{Keyword: "error"}
	result = Apply(entries, keywordFilter)
	if len(result) != 2 {
		t.Fatalf("expected 2 entries with 'error', got %d", len(result))
	}

	// Apply chain
	chain := NewChain(levelFilter, keywordFilter)
	result = Apply(entries, chain)
	if len(result) != 1 {
		t.Fatalf("expected 1 entry matching both filters, got %d", len(result))
	}
	if result[0].Message != "database error" {
		t.Errorf("expected 'database error', got %q", result[0].Message)
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
