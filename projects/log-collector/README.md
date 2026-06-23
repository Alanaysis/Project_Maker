# Log Collector

A distributed log collection system implemented in Go, built for learning log architecture, parsing, and aggregation.

## Overview

This project implements a working log collector that can:
- Collect log lines from files or stdin
- Parse multiple log formats (JSON, Logfmt, Common)
- Store logs in-memory with indexing for fast queries
- Query logs by level, time range, source, and text search
- Provide an interactive query shell

## Architecture

```
                   ┌─────────────────────────────────────────────────┐
                   │              Log Collector Pipeline              │
                   │                                                  │
  Log Sources      │   ┌───────────┐   ┌─────────┐   ┌───────────┐ │
  ┌─────────┐      │   │           │   │         │   │           │ │
  │ app.log │──────┼──▶│ Collector │──▶│ Parser  │──▶│  Storage  │ │
  │ err.log │      │   │           │   │         │   │           │ │
  │  stdin  │      │   └───────────┘   └─────────┘   └─────┬─────┘ │
  └─────────┘      │                                       │       │
                   │                               ┌───────┴─────┐ │
                   │                               │   Query     │ │
                   │                               │   Engine    │ │
                   │                               └─────────────┘ │
                   └─────────────────────────────────────────────────┘
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
│   │   └── collector_test.go
│   ├── parser/
│   │   ├── parser.go            # Multi-format log parsing
│   │   └── parser_test.go
│   ├── storage/
│   │   ├── storage.go           # In-memory storage with indexing
│   │   └── storage_test.go
│   └── query/
│       ├── query.go             # Query engine and formatting
│       └── query_test.go
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

### Auto-detect

When format is set to `auto` (default), the parser tries each format in order: JSON -> Logfmt -> Common. If none match, the line is stored as-is with `UNKNOWN` level.

## Command Line Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-format` | `auto` | Log format: auto, json, logfmt, common |
| `-query` | | Query string (e.g., `level:error source:app.log`) |
| `-stats` | | Show storage statistics |
| `-recent` | | Show N most recent entries |
| `-errors` | | Show N most recent errors |
| `-search` | | Search log messages |
| `-limit` | `100` | Maximum results to return |
| `-db` | `logs.db` | Database file path (future persistence) |

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

1. **Collector** reads raw log lines from sources
2. **Parser** converts raw lines into structured entries
3. **Storage** indexes and stores entries for fast retrieval
4. **Query Engine** provides search and filtering capabilities

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

## Learning Resources

- [Structured Logging](https://www.dataset.com/blog/the-10-commandments-of-logging/) - Logging best practices
- [Logfmt](https://brandur.org/logfmt) - The logfmt format
- [RFC 5424](https://tools.ietf.org/html/rfc5424) - The Syslog Protocol
- [ELK Stack](https://www.elastic.co/what-is/elk-stack) - Production log aggregation

## License

This project is for educational purposes.

---

[返回主目录](../../README.md)
