# Log Collector

A distributed log collection system implemented in Go, built for learning log architecture, parsing, filtering, and aggregation.

## Overview

This project implements a working log collector that can:
- Collect log lines from files, stdin, TCP, and UDP
- Parse multiple log formats (JSON, Logfmt, Common, Regex)
- Filter logs by level, keyword, and regex patterns
- Store logs in-memory with indexing for fast queries
- Query logs by level, time range, source, and text search
- Watch files for new content (tail -f mode)
- Output logs to files with optional rotation
- Provide an interactive query shell

## Architecture

```
                   ┌──────────────────────────────────────────────────────────┐
                   │                  Log Collector Pipeline                    │
                   │                                                           │
  Log Sources       │   ┌───────────┐   ┌─────────┐   ┌────────┐   ┌───────┐│
  ┌─────────┐       │   │           │   │         │   │        │   │       ││
  │ app.log │──────┼──▶│ Collector │──▶│ Parser  │──▶│ Filter │──▶│Storage││
  │ err.log │       │   │           │   │         │   │        │   │       ││
  │  stdin  │       │   └───────────┘   └─────────┘   └────────┘   └───┬───┘│
  │  TCP    │       │                                                   │    │
  │  UDP    │       │                                           ┌───────┴──┐ │
  └─────────┘       │                                           │  Query   │ │
                    │                                           │  Engine  │ │
                    │                                           └──────────┘ │
                    └──────────────────────────────────────────────────────────┘
```

## Project Structure

```
log-collector/
├── cmd/
│   └── collector/
│       └── main.go              # Entry point with CLI
├── internal/
│   ├── collector/
│   │   ├── collector.go         # Log collection from sources
│   │   ├── tailer.go            # File watching (tail -f)
│   │   ├── collector_test.go
│   │   └── tailer_test.go
│   ├── parser/
│   │   ├── parser.go            # Multi-format log parsing
│   │   ├── regex_parser.go      # Regex-based log parsing
│   │   ├── parser_test.go
│   │   └── regex_parser_test.go
│   ├── filter/
│   │   ├── filter.go            # Log filtering (level, keyword, regex)
│   │   └── filter_test.go
│   ├── storage/
│   │   ├── storage.go           # In-memory storage with indexing
│   │   └── storage_test.go
│   ├── transport/
│   │   ├── tcp.go               # TCP log receiver
│   │   ├── udp.go               # UDP log receiver
│   │   ├── filewriter.go        # File output with rotation
│   │   └── transport_test.go
│   └── query/
│       ├── query.go             # Query engine and formatting
│       └── query_test.go
├── tests/
│   └── integration_test.go      # End-to-end integration tests
├── docs/                        # Documentation
├── go.mod                       # Go module file
├── README.md                    # This file
└── LEARNING_NOTES.md            # Learning notes
```

## Quick Start

### Prerequisites

- Go 1.21 or later

### Build and Run

```bash
# Build
go build -o collector ./cmd/collector

# Collect logs from stdin (pipe)
echo '{"level":"info","msg":"hello"}' | ./collector

# Collect logs from files
./collector app.log error.log

# Watch files for new content
./collector -watch app.log error.log

# Listen for TCP log connections
./collector -tcp :5514

# Listen for UDP log connections
./collector -udp :5515

# Filter logs by level
./collector -level error app.log

# Filter logs by keyword
./collector -keyword timeout app.log

# Use custom regex parser
./collector -format regex -regex '^\d{4}-\d{2}-\d{2} \[(?P<level>\w+)\] (?P<msg>.+)$' app.log

# Output to file with rotation
./collector -output logs.out -output-max-size 10485760 app.log

# Query mode (interactive)
./collector
log> level:error
log> recent 20
log> search "timeout"
log> stats
log> quit
```

### Run Tests

```bash
# Run all tests
go test ./...

# Run tests with verbose output
go test ./... -v

# Run tests for a specific package
go test ./internal/parser -v
go test ./internal/filter -v
go test ./internal/transport -v

# Show test coverage
go test ./... -cover
```

## Supported Log Formats

### JSON

```json
{"level":"info","msg":"server started","port":8080,"ts":"2024-01-01T12:00:00Z"}
```

### Logfmt

```
level=info msg=server_started port=8080 ts=2024-01-01T12:00:00Z
```

### Common

```
2024-01-15 10:30:00 [INFO] Application started successfully
```

### Regex (Custom)

Define your own pattern with named capture groups:

```bash
./collector -format regex \
  -regex '^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<msg>.+)$' \
  app.log
```

Recognized named groups:
- `time`, `ts`, `timestamp`: Parsed as timestamp
- `level`, `severity`, `lvl`: Parsed as log level
- `msg`, `message`: Used as the message
- Any other named group is stored as a field

Built-in patterns are available for common formats: Apache, Syslog, Generic, Access.

### Auto-detect

When format is set to `auto` (default), the parser tries each format in order: JSON -> Logfmt -> Common. If none match, the line is stored as-is with `UNKNOWN` level.

## Log Filtering

### Level Filter

Filter entries by minimum log level:

```bash
./collector -level error app.log          # Only ERROR and FATAL
./collector -level warn app.log           # WARN, ERROR, and FATAL
```

### Keyword Filter

Filter entries by keyword presence:

```bash
./collector -keyword timeout app.log      # Only entries containing "timeout"
./collector -keyword debug -keyword-exclude app.log  # Exclude entries with "debug"
```

### Regex Filter

Filter entries by regex pattern:

```bash
./collector -regex-filter "connection.*timeout" app.log
./collector -regex-filter "\d{3}.*error" -regex-exclude app.log
```

### Composing Filters

Multiple filters are combined with AND logic:

```bash
./collector -level error -keyword timeout app.log   # ERROR+ AND contains "timeout"
```

## Network Transport

### TCP Receiver

```bash
# Start TCP receiver
./collector -tcp :5514

# Send logs from another terminal
echo '{"level":"info","msg":"hello"}' | nc localhost 5514
```

### UDP Receiver

```bash
# Start UDP receiver
./collector -udp :5515

# Send logs from another terminal
echo "2024-01-15 10:30:00 [INFO] test" | nc -u localhost 5515
```

### File Output with Rotation

```bash
# Write to file
./collector -output server.log app.log

# Write to file with rotation at 10MB
./collector -output server.log -output-max-size 10485760 -tcp :5514
```

## Command Line Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-format` | `auto` | Log format: auto, json, logfmt, common, regex |
| `-regex` | | Regex pattern for regex format |
| `-watch` | | Watch files for new content (tail -f mode) |
| `-tcp` | | Listen for TCP connections (e.g., `:5514`) |
| `-udp` | | Listen for UDP connections (e.g., `:5515`) |
| `-level` | | Minimum log level filter |
| `-keyword` | | Keyword filter |
| `-keyword-exclude` | | Exclude entries matching keyword |
| `-regex-filter` | | Regex filter pattern |
| `-regex-exclude` | | Exclude entries matching regex filter |
| `-output` | | Write logs to file |
| `-output-max-size` | `0` | Max output file size before rotation |
| `-query` | | Query string |
| `-stats` | | Show storage statistics |
| `-recent` | | Show N most recent entries |
| `-errors` | | Show N most recent errors |
| `-search` | | Search log messages |
| `-limit` | `100` | Maximum results to return |

## Interactive Query Commands

| Command | Description |
|---------|-------------|
| `stats` | Show storage statistics |
| `recent [N]` | Show N most recent entries (default: 10) |
| `errors [N]` | Show N most recent errors (default: 10) |
| `search <text>` | Search log messages |
| `level:<LEVEL>` | Filter by level (DEBUG, INFO, WARN, ERROR, FATAL) |
| `source:<text>` | Filter by source |
| `after:<YYYY-MM-DD>` | Filter entries after date |
| `before:<YYYY-MM-DD>` | Filter entries before date |
| `limit:<N>` | Limit results |
| `help` | Show help |
| `quit` | Exit |

## Key Concepts

### Log Pipeline

The system follows a producer-consumer pipeline pattern:

1. **Collector** reads raw log lines from sources (files, stdin, network)
2. **Parser** converts raw lines into structured entries
3. **Filter** applies level, keyword, and regex filters
4. **Storage** indexes and stores entries for fast retrieval
5. **Query Engine** provides search and filtering capabilities

### Log Levels

| Level | Priority | Description |
|-------|----------|-------------|
| DEBUG | 0 | Detailed debug information |
| INFO | 1 | General informational messages |
| WARN | 2 | Warning conditions |
| ERROR | 3 | Error conditions |
| FATAL | 4 | Fatal/crash conditions |

### Storage Indexing

The in-memory storage maintains three indexes:
- **Time index**: entries ordered by timestamp
- **Level index**: entries grouped by log level
- **Source index**: entries grouped by source file

This enables fast queries that don't need to scan all entries.

### Filter Chain

Filters are composable using chain (AND) or match-any (OR) logic:
- **Chain**: All filters must match
- **MatchAny**: At least one filter must match

## Use Cases

### Centralized Logging

```bash
# On the log server
./collector -tcp :5514 -output /var/log/central.log -level warn

# On application servers
echo '{"level":"error","msg":"db timeout"}' | nc logserver 5514
```

### Log Analysis

```bash
# Collect and analyze
./collector app.log error.log

# Interactive analysis
log> stats
log> level:error
log> search "timeout"
log> after:2024-01-15 before:2024-01-16 level:error limit:50
```

### Real-time Monitoring

```bash
# Watch for errors in real-time
./collector -watch -level error app.log

# Watch with keyword filter
./collector -watch -keyword "critical" -keyword-exclude false app.log
```

## Learning Resources

- [Structured Logging](https://www.dataset.com/blog/the-10-commandments-of-logging/) - Logging best practices
- [Logfmt](https://brandur.org/logfmt) - The logfmt format
- [RFC 5424](https://tools.ietf.org/html/rfc5424) - The Syslog Protocol
- [ELK Stack](https://www.elastic.co/what-is/elk-stack) - Production log aggregation

## License

This project is for educational purposes.

---

[返回主目录](../../README.md)
