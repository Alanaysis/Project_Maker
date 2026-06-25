package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"

	"github.com/learning/stream-processing/internal/core"
	"github.com/learning/stream-processing/internal/operator"
	"github.com/learning/stream-processing/internal/pipeline"
	"github.com/learning/stream-processing/internal/state"
)

// RawLog represents a raw log line from a web server.
type RawLog struct {
	IP        string
	Timestamp string
	Method    string
	Path      string
	Status    int
	Size      int
}

// ProcessedLog represents a cleaned and enriched log entry.
type ProcessedLog struct {
	IP        string
	Timestamp time.Time
	Method    string
	Path      string
	Status    int
	Size      int
	Category  string
	IsValid   bool
}

func main() {
	fmt.Println("=== ETL Pipeline Example ===")
	fmt.Println()

	demoLogETL()
	demoDataEnrichment()
	demoAggregationETL()
}

// demoLogETL shows a complete ETL pipeline for web logs.
func demoLogETL() {
	fmt.Println("--- Web Log ETL Pipeline ---")
	fmt.Println("  Input: Raw log lines")
	fmt.Println("  Output: Structured, validated, categorized logs")

	// Stage 1: Parse raw logs
	parseStage := pipeline.NewPipeline()
	parseStage.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		line := v.(string)
		return parseLogLine(line)
	}))

	// Stage 2: Validate and filter
	validateStage := pipeline.NewPipeline()
	validateStage.AddOperator(operator.NewFilterOperator(func(e core.Event) bool {
		log := e.Value.(RawLog)
		return log.Status > 0 && log.IP != ""
	}))

	// Stage 3: Enrich and categorize
	enrichStage := pipeline.NewPipeline()
	enrichStage.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		log := v.(RawLog)
		return ProcessedLog{
			IP:        log.IP,
			Timestamp: parseTimestamp(log.Timestamp),
			Method:    log.Method,
			Path:      log.Path,
			Status:    log.Status,
			Size:      log.Size,
			Category:  categorizePath(log.Path),
			IsValid:   true,
		}
	}))

	// Chain stages
	input := core.NewStream(100)
	go func() {
		defer input.Close()

		logs := []string{
			`192.168.1.1 - - [24/Jun/2024:10:00:00 +0000] "GET /index.html HTTP/1.1" 200 1234`,
			`192.168.1.2 - - [24/Jun/2024:10:00:01 +0000] "POST /api/users HTTP/1.1" 201 567`,
			`192.168.1.3 - - [24/Jun/2024:10:00:02 +0000] "GET /static/style.css HTTP/1.1" 304 0`,
			`invalid log line`,
			`192.168.1.4 - - [24/Jun/2024:10:00:03 +0000] "GET /api/data HTTP/1.1" 500 890`,
		}

		for _, line := range logs {
			input.Emit(core.NewEvent("log", line))
		}
	}()

	// Execute stages
	parsed := parseStage.Execute(input)
	validated := validateStage.Execute(parsed)
	enriched := enrichStage.Execute(validated)

	// Collect results
	var results []ProcessedLog
	for e := range enriched.Events() {
		results = append(results, e.Value.(ProcessedLog))
	}

	fmt.Printf("  Processed %d/%d logs\n", len(results), 4) // 4 valid logs
	for _, r := range results {
		fmt.Printf("    [%s] %s %s -> %d (%s)\n",
			r.IP, r.Method, r.Path, r.Status, r.Category)
	}
	fmt.Println()
}

// demoDataEnrichment shows data enrichment using keyed state.
func demoDataEnrichment() {
	fmt.Println("--- Data Enrichment Pipeline ---")
	fmt.Println("  Enrich events with data from a lookup table")

	// Create lookup state
	lookup := state.NewKeyedState()
	lookup.Put("user", "U001", map[string]string{"name": "Alice", "dept": "Engineering"})
	lookup.Put("user", "U002", map[string]string{"name": "Bob", "dept": "Marketing"})
	lookup.Put("user", "U003", map[string]string{"name": "Charlie", "dept": "Sales"})

	// Create enrichment pipeline
	p := pipeline.NewPipeline()
	p.AddOperator(operator.NewMapOperator(func(v interface{}) interface{} {
		event := v.(map[string]string)
		userID := event["user_id"]

		// Look up user info
		userInfo, ok := lookup.Get("user", userID)
		if !ok {
			return map[string]interface{}{
				"user_id":  userID,
				"action":   event["action"],
				"enriched": false,
			}
		}

		user := userInfo.(map[string]string)
		return map[string]interface{}{
			"user_id":  userID,
			"name":     user["name"],
			"dept":     user["dept"],
			"action":   event["action"],
			"enriched": true,
		}
	}))

	// Generate events
	input := core.NewStream(100)
	go func() {
		defer input.Close()

		events := []map[string]string{
			{"user_id": "U001", "action": "login"},
			{"user_id": "U002", "action": "view"},
			{"user_id": "U004", "action": "purchase"}, // Unknown user
			{"user_id": "U003", "action": "logout"},
		}

		for _, e := range events {
			input.Emit(core.NewEvent("activity", e))
		}
	}()

	output := p.Execute(input)

	for e := range output.Events() {
		result := e.Value.(map[string]interface{})
		if result["enriched"].(bool) {
			fmt.Printf("  %s (%s, %s) - %s\n",
				result["user_id"], result["name"], result["dept"], result["action"])
		} else {
			fmt.Printf("  %s (unknown) - %s\n", result["user_id"], result["action"])
		}
	}
	fmt.Println()
}

// demoAggregationETL shows aggregation as part of ETL.
func demoAggregationETL() {
	fmt.Println("--- Aggregation ETL ---")
	fmt.Println("  Aggregate sales data by category")

	type Sale struct {
		Category string
		Amount   float64
		Region   string
	}

	// Key by category
	keyByOp := operator.NewKeyByOperator(func(v interface{}) string {
		return v.(Sale).Category
	})

	// Aggregate by key
	reduceOp := operator.NewReduceByKeyOperator(func(a, b interface{}) interface{} {
		s1 := a.(Sale)
		s2 := b.(Sale)
		return Sale{
			Category: s1.Category,
			Amount:   s1.Amount + s2.Amount,
			Region:   s1.Region, // Keep first region
		}
	})

	// Process
	input := core.NewStream(100)
	go func() {
		defer input.Close()

		sales := []Sale{
			{"Electronics", 1500.00, "North"},
			{"Clothing", 250.00, "South"},
			{"Electronics", 2300.00, "North"},
			{"Food", 800.00, "East"},
			{"Clothing", 450.00, "West"},
			{"Electronics", 1800.00, "South"},
			{"Food", 600.00, "East"},
		}

		for _, s := range sales {
			input.Emit(core.NewEvent(s.Category, s))
		}
	}()

	// Key by category
	keyed := core.NewStream(100)
	go func() {
		defer keyed.Close()
		for e := range input.Events() {
			keyByOp.Process(e, keyed)
		}
	}()

	// Aggregate
	output := core.NewStream(100)
	go func() {
		defer output.Close()
		for e := range keyed.Events() {
			reduceOp.Process(e, output)
		}
		reduceOp.Flush(output)
	}()

	// Display results
	fmt.Println("  Sales by Category:")
	for e := range output.Events() {
		sale := e.Value.(Sale)
		fmt.Printf("    %s: $%.2f\n", sale.Category, sale.Amount)
	}
	fmt.Println()
}

// Helper functions

func parseLogLine(line string) RawLog {
	// Simple log parser (simplified for demo)
	parts := strings.Fields(line)
	if len(parts) < 7 {
		return RawLog{}
	}

	status, _ := strconv.Atoi(parts[8])
	size, _ := strconv.Atoi(parts[9])

	return RawLog{
		IP:        parts[0],
		Timestamp: parts[3] + " " + parts[4],
		Method:    strings.Trim(parts[5], "\""),
		Path:      parts[6],
		Status:    status,
		Size:      size,
	}
}

func parseTimestamp(ts string) time.Time {
	t, _ := time.Parse("[02/Jan/2006:15:04:05 -0700]", ts)
	return t
}

func categorizePath(path string) string {
	if strings.HasPrefix(path, "/api/") {
		return "API"
	}
	if strings.HasPrefix(path, "/static/") {
		return "Static"
	}
	if path == "/" || strings.HasSuffix(path, ".html") {
		return "Page"
	}
	return "Other"
}
