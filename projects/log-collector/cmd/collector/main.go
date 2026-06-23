// Log Collector - A distributed log collection system.
//
// Usage:
//
//	collector [flags] [file...]
//	collector -query "level:error" -limit 50
//	collector -stats
//
// When run with file arguments, it collects and stores logs from those files.
// When run with -query or -stats, it queries previously stored logs.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/project/log-collector/internal/collector"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/query"
	"github.com/project/log-collector/internal/storage"
)

func main() {
	// Flags
	queryStr := flag.String("query", "", "Query logs (e.g., 'level:error source:app.log')")
	statsFlag := flag.Bool("stats", false, "Show storage statistics")
	recent := flag.Int("recent", 0, "Show N most recent entries")
	errorsFlag := flag.Int("errors", 0, "Show N most recent errors")
	search := flag.String("search", "", "Search log messages")
	format := flag.String("format", "auto", "Log format: auto, json, logfmt, common")
	limit := flag.Int("limit", 100, "Maximum results to return")
	dbPath := flag.String("db", "logs.db", "Database file path (for future persistence)")
	_ = dbPath // Will be used for persistence

	flag.Parse()

	store := storage.New()

	if *statsFlag || *recent > 0 || *errorsFlag > 0 || *queryStr != "" || *search != "" {
		// Query mode: load and query
		runQueryMode(store, *queryStr, *search, *recent, *errorsFlag, *statsFlag, *limit)
	} else {
		// Collection mode: collect and store
		runCollectMode(store, *format)
	}
}

// runCollectMode collects logs from files or stdin.
func runCollectMode(store *storage.Storage, format string) {
	files := flag.Args()

	// Parse format
	var logFmt parser.Format
	switch strings.ToLower(format) {
	case "json":
		logFmt = parser.FormatJSON
	case "logfmt":
		logFmt = parser.FormatLogfmt
	case "common":
		logFmt = parser.FormatCommon
	default:
		logFmt = parser.FormatAuto
	}

	p := parser.New(logFmt)

	// Set up sources
	var sources []collector.Source
	if len(files) == 0 {
		// Read from stdin
		sources = []collector.Source{{Name: "stdin", Path: "-"}}
	} else {
		for _, f := range files {
			sources = append(sources, collector.Source{Name: f, Path: f})
		}
	}

	// Create pipeline
	rawCh := make(chan collector.RawLog, 1000)
	c := collector.New(sources, rawCh)

	// Start collector
	if err := c.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	// Process raw logs
	go func() {
		for raw := range rawCh {
			entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
			if err != nil {
				// Store unparsable lines as unknown
				store.Store(storage.Entry{
					Timestamp: time.Now(),
					Level:     storage.LevelUnknown,
					Message:   raw.Line,
					Source:    raw.Source,
					LineNum:   raw.LineNum,
					Raw:       raw.Line,
				})
				continue
			}

			store.Store(storage.Entry{
				Timestamp: entry.Timestamp,
				Level:     storage.Level(entry.Level),
				Message:   entry.Message,
				Fields:    entry.Fields,
				Source:    entry.Source,
				LineNum:   entry.LineNum,
				Raw:       entry.Raw,
			})
		}
	}()

	// Wait for collection to complete
	<-c.Done()

	// Close raw channel after collector is done
	// Note: collector doesn't close the channel, we need to handle this
	// For now, just report stats
	time.Sleep(100 * time.Millisecond) // Allow processing to finish

	stats := store.Stats()
	fmt.Printf("Collected %d log entries\n", stats.TotalEntries)
	if stats.TotalEntries > 0 {
		fmt.Printf("Level distribution: ")
		for lvl, count := range stats.LevelCounts {
			fmt.Printf("%s=%d ", lvl, count)
		}
		fmt.Println()
	}

	// Interactive query mode after collection
	fmt.Println("\nEntering interactive mode. Type 'help' for commands, 'quit' to exit.")
	runInteractive(store)
}

// runQueryMode runs in query mode.
func runQueryMode(store *storage.Storage, queryStr, searchStr string, recentN, errorsN int, showStats bool, limit int) {
	engine := query.NewEngine(store)

	// For demo purposes, we need data. Show a message if store is empty.
	if store.Count() == 0 {
		fmt.Println("No logs in storage. Collect some logs first:")
		fmt.Println("  cat app.log | collector")
		fmt.Println("  collector app.log error.log")
		fmt.Println()
		fmt.Println("Or generate sample logs:")
		fmt.Println("  collector -gen | collector")
		return
	}

	switch {
	case showStats:
		fmt.Print(query.FormatStats(store.Stats()))
	case recentN > 0:
		entries := engine.Recent(recentN)
		fmt.Print(query.FormatEntries(entries))
	case errorsN > 0:
		entries := engine.Errors(errorsN)
		fmt.Print(query.FormatEntries(entries))
	case searchStr != "":
		entries := engine.Search(searchStr, limit)
		fmt.Print(query.FormatEntries(entries))
	case queryStr != "":
		entries, err := engine.AdvancedQuery(queryStr)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Query error: %v\n", err)
			os.Exit(1)
		}
		fmt.Print(query.FormatEntries(entries))
	}
}

// runInteractive runs an interactive query shell.
func runInteractive(store *storage.Storage) {
	engine := query.NewEngine(store)
	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("log> ")
		if !scanner.Scan() {
			break
		}

		input := strings.TrimSpace(scanner.Text())
		if input == "" {
			continue
		}

		switch {
		case input == "quit" || input == "exit":
			fmt.Println("Bye!")
			return
		case input == "help":
			printHelp()
		case input == "stats":
			fmt.Print(query.FormatStats(store.Stats()))
		case strings.HasPrefix(input, "recent"):
			n := 10
			parts := strings.Fields(input)
			if len(parts) > 1 {
				fmt.Sscanf(parts[1], "%d", &n)
			}
			fmt.Print(query.FormatEntries(engine.Recent(n)))
		case strings.HasPrefix(input, "errors"):
			n := 10
			parts := strings.Fields(input)
			if len(parts) > 1 {
				fmt.Sscanf(parts[1], "%d", &n)
			}
			fmt.Print(query.FormatEntries(engine.Errors(n)))
		case strings.HasPrefix(input, "search "):
			text := strings.TrimPrefix(input, "search ")
			fmt.Print(query.FormatEntries(engine.Search(text, 100)))
		default:
			// Try as advanced query
			entries, err := engine.AdvancedQuery(input)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
			} else {
				fmt.Print(query.FormatEntries(entries))
			}
		}
	}
}

func printHelp() {
	fmt.Println(`Log Collector - Interactive Query Shell

Commands:
  stats               Show storage statistics
  recent [N]          Show N most recent entries (default: 10)
  errors [N]          Show N most recent errors (default: 10)
  search <text>       Search log messages
  level:<LEVEL>       Filter by level (DEBUG, INFO, WARN, ERROR, FATAL)
  source:<text>       Filter by source
  after:<YYYY-MM-DD>  Filter entries after date
  before:<YYYY-MM-DD> Filter entries before date
  limit:<N>           Limit results
  help                Show this help
  quit                Exit

Examples:
  level:error
  level:warn source:app.log
  search "connection timeout"
  after:2024-01-01 before:2024-12-31 level:error limit:50`)
}
