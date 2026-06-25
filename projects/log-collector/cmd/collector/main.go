// Log Collector - A distributed log collection system.
//
// Usage:
//
//	collector [flags] [file...]
//	collector -query "level:error" -limit 50
//	collector -stats
//	collector -tcp :5514
//	collector -udp :5515
//	collector -watch app.log error.log
//	collector -filter "level:error" -output logs.out
//
// When run with file arguments, it collects and stores logs from those files.
// When run with -query or -stats, it queries previously stored logs.
// When run with -tcp or -udp, it listens for network log connections.
// When run with -watch, it tails files for new content.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/project/log-collector/internal/collector"
	"github.com/project/log-collector/internal/filter"
	"github.com/project/log-collector/internal/parser"
	"github.com/project/log-collector/internal/query"
	"github.com/project/log-collector/internal/storage"
	"github.com/project/log-collector/internal/transport"
)

func main() {
	// Collection flags
	format := flag.String("format", "auto", "Log format: auto, json, logfmt, common, regex")
	regexPattern := flag.String("regex", "", "Regex pattern for regex format (named groups: time, level, msg)")
	watch := flag.Bool("watch", false, "Watch files for new content (tail -f mode)")

	// Network flags
	tcpAddr := flag.String("tcp", "", "Listen for TCP connections (e.g., :5514)")
	udpAddr := flag.String("udp", "", "Listen for UDP connections (e.g., :5515)")

	// Filter flags
	levelFilter := flag.String("level", "", "Minimum log level filter (DEBUG, INFO, WARN, ERROR, FATAL)")
	keywordFilter := flag.String("keyword", "", "Keyword filter (entries must contain this)")
	keywordExclude := flag.Bool("keyword-exclude", false, "Exclude entries matching keyword")
	regexFilter := flag.String("regex-filter", "", "Regex filter pattern for messages")
	regexExclude := flag.Bool("regex-exclude", false, "Exclude entries matching regex filter")

	// Output flags
	outputFile := flag.String("output", "", "Write logs to file instead of stdout")
	outputMaxSize := flag.Int64("output-max-size", 0, "Max output file size in bytes before rotation (0 = no limit)")

	// Query flags
	queryStr := flag.String("query", "", "Query logs (e.g., 'level:error source:app.log')")
	statsFlag := flag.Bool("stats", false, "Show storage statistics")
	recent := flag.Int("recent", 0, "Show N most recent entries")
	errorsFlag := flag.Int("errors", 0, "Show N most recent errors")
	search := flag.String("search", "", "Search log messages")
	limit := flag.Int("limit", 100, "Maximum results to return")
	dbPath := flag.String("db", "logs.db", "Database file path (for future persistence)")
	_ = dbPath

	flag.Parse()

	store := storage.New()

	if *statsFlag || *recent > 0 || *errorsFlag > 0 || *queryStr != "" || *search != "" {
		// Query mode
		runQueryMode(store, *queryStr, *search, *recent, *errorsFlag, *statsFlag, *limit)
	} else if *tcpAddr != "" || *udpAddr != "" {
		// Network mode
		runNetworkMode(store, *tcpAddr, *udpAddr, *format, *regexPattern,
			*levelFilter, *keywordFilter, *keywordExclude,
			*regexFilter, *regexExclude,
			*outputFile, *outputMaxSize)
	} else if *watch {
		// Watch mode
		runWatchMode(store, *format, *regexPattern,
			*levelFilter, *keywordFilter, *keywordExclude,
			*regexFilter, *regexExclude,
			*outputFile, *outputMaxSize)
	} else {
		// Collection mode
		runCollectMode(store, *format, *regexPattern,
			*levelFilter, *keywordFilter, *keywordExclude,
			*regexFilter, *regexExclude,
			*outputFile, *outputMaxSize)
	}
}

// buildFilterChain creates a filter chain from command-line flags.
func buildFilterChain(levelStr, keyword string, keywordExclude bool,
	regexPat string, regexExclude bool) *filter.Chain {

	var filters []filter.Filter

	// Level filter
	if levelStr != "" {
		var lvl filter.Level
		switch strings.ToUpper(levelStr) {
		case "DEBUG":
			lvl = filter.LevelDebug
		case "INFO":
			lvl = filter.LevelInfo
		case "WARN", "WARNING":
			lvl = filter.LevelWarn
		case "ERROR":
			lvl = filter.LevelError
		case "FATAL":
			lvl = filter.LevelFatal
		default:
			lvl = filter.LevelUnknown
		}
		filters = append(filters, &filter.LevelFilter{MinLevel: lvl})
	}

	// Keyword filter
	if keyword != "" {
		filters = append(filters, &filter.KeywordFilter{
			Keyword: keyword,
			Exclude: keywordExclude,
		})
	}

	// Regex filter
	if regexPat != "" {
		rf, err := filter.NewRegexFilter(regexPat, regexExclude)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: invalid regex filter %q: %v\n", regexPat, err)
		} else {
			filters = append(filters, rf)
		}
	}

	if len(filters) == 0 {
		return nil
	}
	return filter.NewChain(filters...)
}

// createParser creates a parser based on format and optional regex pattern.
func createParser(format, regexPattern string) (*parser.Parser, error) {
	switch strings.ToLower(format) {
	case "json":
		return parser.New(parser.FormatJSON), nil
	case "logfmt":
		return parser.New(parser.FormatLogfmt), nil
	case "common":
		return parser.New(parser.FormatCommon), nil
	case "regex":
		if regexPattern == "" {
			return nil, fmt.Errorf("regex format requires -regex flag with a pattern")
		}
		return parser.NewWithRegex(regexPattern)
	default:
		return parser.New(parser.FormatAuto), nil
	}
}

// createFileWriter creates a file writer if outputFile is specified.
func createFileWriter(outputFile string, maxSize int64) (*transport.FileWriter, error) {
	if outputFile == "" {
		return nil, nil
	}
	return transport.NewFileWriter(transport.FileWriterConfig{
		Path:    outputFile,
		MaxSize: maxSize,
	})
}

// storeEntry converts a parser entry to a storage entry and stores it.
func storeEntry(store *storage.Storage, entry *parser.Entry) {
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

// outputEntry writes an entry to the file writer or returns a formatted string.
func outputEntry(fw *transport.FileWriter, entry *storage.Entry) {
	if fw != nil {
		fw.WriteEntry(entry.Timestamp, entry.Level.String(), entry.Source, entry.Message)
	}
}

// processRawLog parses, filters, stores, and outputs a single raw log line.
func processRawLog(store *storage.Storage, p *parser.Parser, fc *filter.Chain,
	fw *transport.FileWriter, raw collector.RawLog) {

	entry, err := p.Parse(raw.Line, raw.Source, raw.LineNum)
	if err != nil {
		// Store unparsable lines as unknown
		se := storage.Entry{
			Timestamp: time.Now(),
			Level:     storage.LevelUnknown,
			Message:   raw.Line,
			Source:    raw.Source,
			LineNum:   raw.LineNum,
			Raw:       raw.Line,
		}
		if fc == nil {
			store.Store(se)
			outputEntry(fw, &se)
		}
		return
	}

	se := storage.Entry{
		Timestamp: entry.Timestamp,
		Level:     storage.Level(entry.Level),
		Message:   entry.Message,
		Fields:    entry.Fields,
		Source:    entry.Source,
		LineNum:   entry.LineNum,
		Raw:       entry.Raw,
	}

	// Apply filter
	if fc != nil {
		fe := filter.Entry{
			Level:   filter.Level(entry.Level),
			Message: entry.Message,
			Source:  entry.Source,
			Fields:  entry.Fields,
		}
		if !fc.Match(fe) {
			return // Filtered out
		}
	}

	store.Store(se)
	outputEntry(fw, &se)
}

// processRawLogNetwork parses, filters, stores, and outputs a network raw log.
func processRawLogNetwork(store *storage.Storage, p *parser.Parser, fc *filter.Chain,
	fw *transport.FileWriter, raw transport.RawLog, lineNum *int) {

	*lineNum++
	cr := collector.RawLog{
		Line:    raw.Line,
		Source:  raw.Source,
		LineNum: *lineNum,
	}
	processRawLog(store, p, fc, fw, cr)
}

// runCollectMode collects logs from files or stdin.
func runCollectMode(store *storage.Storage, format, regexPattern string,
	levelStr, keyword string, keywordExclude bool,
	regexPat string, regexExclude bool,
	outputFile string, outputMaxSize int64) {

	p, err := createParser(format, regexPattern)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fc := buildFilterChain(levelStr, keyword, keywordExclude, regexPat, regexExclude)

	fw, err := createFileWriter(outputFile, outputMaxSize)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	if fw != nil {
		defer fw.Close()
	}

	files := flag.Args()

	// Set up sources
	var sources []collector.Source
	if len(files) == 0 {
		sources = []collector.Source{{Name: "stdin", Path: "-"}}
	} else {
		for _, f := range files {
			sources = append(sources, collector.Source{Name: f, Path: f})
		}
	}

	// Create pipeline
	rawCh := make(chan collector.RawLog, 1000)
	c := collector.New(sources, rawCh)

	if err := c.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	// Process raw logs
	go func() {
		for raw := range rawCh {
			processRawLog(store, p, fc, fw, raw)
		}
	}()

	<-c.Done()
	time.Sleep(100 * time.Millisecond)

	stats := store.Stats()
	fmt.Fprintf(os.Stderr, "Collected %d log entries\n", stats.TotalEntries)
	if stats.TotalEntries > 0 {
		fmt.Fprintf(os.Stderr, "Level distribution: ")
		for lvl, count := range stats.LevelCounts {
			fmt.Fprintf(os.Stderr, "%s=%d ", lvl, count)
		}
		fmt.Fprintln(os.Stderr)
	}

	if outputFile != "" {
		fmt.Fprintf(os.Stderr, "Output written to: %s\n", outputFile)
	}

	fmt.Fprintln(os.Stderr, "\nEntering interactive mode. Type 'help' for commands, 'quit' to exit.")
	runInteractive(store)
}

// runWatchMode watches files for new content.
func runWatchMode(store *storage.Storage, format, regexPattern string,
	levelStr, keyword string, keywordExclude bool,
	regexPat string, regexExclude bool,
	outputFile string, outputMaxSize int64) {

	files := flag.Args()
	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "Error: -watch requires at least one file argument")
		os.Exit(1)
	}

	p, err := createParser(format, regexPattern)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fc := buildFilterChain(levelStr, keyword, keywordExclude, regexPat, regexExclude)

	fw, err := createFileWriter(outputFile, outputMaxSize)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	if fw != nil {
		defer fw.Close()
	}

	outputCh := make(chan collector.RawLog, 1000)
	mt := collector.NewMultiTailer(files, outputCh, 500*time.Millisecond)

	if err := mt.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Fprintf(os.Stderr, "Watching %d file(s) for new content. Press Ctrl+C to stop.\n", len(files))

	// Process new lines
	go func() {
		for raw := range outputCh {
			processRawLog(store, p, fc, fw, raw)
			// Also print to stderr for real-time monitoring
			fmt.Fprintf(os.Stderr, "[%s] %s\n", raw.Source, raw.Line)
		}
	}()

	// Wait for interrupt
	<-mt.Done()
}

// runNetworkMode listens for network log connections.
func runNetworkMode(store *storage.Storage, tcpAddr, udpAddr, format, regexPattern string,
	levelStr, keyword string, keywordExclude bool,
	regexPat string, regexExclude bool,
	outputFile string, outputMaxSize int64) {

	p, err := createParser(format, regexPattern)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	fc := buildFilterChain(levelStr, keyword, keywordExclude, regexPat, regexExclude)

	fw, err := createFileWriter(outputFile, outputMaxSize)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	if fw != nil {
		defer fw.Close()
	}

	outputCh := make(chan transport.RawLog, 1000)
	lineNum := 0

	// Start TCP receiver
	if tcpAddr != "" {
		tcp := transport.NewTCPReceiver(tcpAddr, outputCh)
		if err := tcp.Start(); err != nil {
			fmt.Fprintf(os.Stderr, "TCP error: %v\n", err)
			os.Exit(1)
		}
		defer tcp.Stop()
		fmt.Fprintf(os.Stderr, "TCP receiver listening on %s\n", tcp.Addr())
	}

	// Start UDP receiver
	if udpAddr != "" {
		udp := transport.NewUDPReceiver(udpAddr, outputCh)
		if err := udp.Start(); err != nil {
			fmt.Fprintf(os.Stderr, "UDP error: %v\n", err)
			os.Exit(1)
		}
		defer udp.Stop()
		fmt.Fprintf(os.Stderr, "UDP receiver listening on %s\n", udp.Addr())
	}

	fmt.Fprintln(os.Stderr, "Press Ctrl+C to stop.")

	// Process received logs
	for raw := range outputCh {
		processRawLogNetwork(store, p, fc, fw, raw, &lineNum)
	}
}

// runQueryMode runs in query mode.
func runQueryMode(store *storage.Storage, queryStr, searchStr string, recentN, errorsN int, showStats bool, limit int) {
	engine := query.NewEngine(store)

	if store.Count() == 0 {
		fmt.Println("No logs in storage. Collect some logs first:")
		fmt.Println("  cat app.log | collector")
		fmt.Println("  collector app.log error.log")
		fmt.Println("  collector -tcp :5514")
		fmt.Println("  collector -watch app.log")
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

Collection Commands:
  collector [file...]                  Collect logs from files
  collector -watch [file...]           Watch files for new content
  collector -tcp :5514                 Listen for TCP log connections
  collector -udp :5515                 Listen for UDP log connections
  collector -format regex -regex PATTERN  Use custom regex parser

Filter Commands:
  -level <LEVEL>      Minimum log level (DEBUG, INFO, WARN, ERROR, FATAL)
  -keyword <TEXT>     Entries must contain this keyword
  -keyword-exclude    Exclude entries matching keyword
  -regex-filter <RE>  Regex pattern for message filtering
  -regex-exclude      Exclude entries matching regex filter

Output Commands:
  -output <FILE>      Write logs to file
  -output-max-size N  Max file size before rotation (bytes)

Interactive Commands:
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
  cat app.log | collector -level error
  collector -watch -keyword timeout app.log
  collector -tcp :5514 -output server.log
  collector -format regex -regex '^\d{4}-\d{2}-\d{2} \[(?P<level>\w+)\] (?P<msg>.+)$' app.log
  log> level:error
  log> search "connection timeout"`)
}
