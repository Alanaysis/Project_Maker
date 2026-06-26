package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"mapreduce/src"
)

// LogAnalysisExample demonstrates MapReduce for analyzing server log files.
//
// This example processes simulated HTTP server logs and computes:
// - Request counts by status code
// - Request counts by HTTP method
// - Top IP addresses by request count
//
// This is a common real-world use case for MapReduce in log analysis pipelines.
func main() {
	tempDir := filepath.Join(os.TempDir(), "mapreduce-log")
	inputDir := filepath.Join(tempDir, "input")
	outputDir := filepath.Join(tempDir, "output")

	os.RemoveAll(tempDir)
	os.MkdirAll(inputDir, 0755)
	os.MkdirAll(outputDir, 0755)

	logEntries := []struct {
		filename string
		entries  []string
	}{
		{
			"server-log-0.log",
			[]string{
				"192.168.1.1 GET /index.html 200",
				"192.168.1.2 POST /api/users 201",
				"192.168.1.1 GET /about.html 200",
				"192.168.1.3 GET /index.html 404",
				"192.168.1.1 DELETE /api/users/1 200",
				"192.168.1.2 GET /api/data 500",
				"192.168.1.4 PUT /api/users/2 200",
				"192.168.1.1 GET /contact.html 200",
			},
		},
		{
			"server-log-1.log",
			[]string{
				"192.168.1.5 GET /index.html 200",
				"192.168.1.2 POST /api/orders 201",
				"192.168.1.3 GET /products.html 200",
				"192.168.1.1 GET /api/data 200",
				"192.168.1.5 GET /about.html 404",
				"192.168.1.3 GET /index.html 200",
				"192.168.1.2 GET /api/users 200",
				"192.168.1.4 POST /api/login 401",
			},
		},
		{
			"server-log-2.log",
			[]string{
				"192.168.1.1 GET /index.html 200",
				"192.168.1.6 GET /products.html 200",
				"192.168.1.3 POST /api/users 201",
				"192.168.1.5 GET /api/data 200",
				"192.168.1.2 GET /index.html 200",
				"192.168.1.6 DELETE /api/orders/1 200",
				"192.168.1.1 GET /api/users 200",
				"192.168.1.3 GET /about.html 200",
			},
		},
	}

	var inputFiles []string
	for _, data := range logEntries {
		filename := filepath.Join(inputDir, data.filename)
		content := strings.Join(data.entries, "\n") + "\n"
		os.WriteFile(filename, []byte(content), 0644)
		inputFiles = append(inputFiles, filename)
	}

	fmt.Println("=== Log Analysis Example ===")
	fmt.Printf("Log files: %d\n", len(inputFiles))
	fmt.Println()

	master := mr.NewMaster(mr.MasterConfig{
		InputFiles:     inputFiles,
		OutputDir:      outputDir,
		TempDir:        filepath.Join(tempDir, "temp"),
		NumReduceTasks: 3,
	})

	worker := master.NewWorker("worker-1")

	// Map function: parse log lines and emit multiple key-value pairs
	worker.SetMapFunc(func(key string, value string) []mr.KeyValue {
		var result []mr.KeyValue
		parts := strings.Fields(value)
		if len(parts) < 4 {
			return nil
		}

		ip := parts[0]
		method := parts[1]
		status := parts[3]

		result = append(result, mr.KeyValue{Key: fmt.Sprintf("status:%s", status), Value: "1"})
		result = append(result, mr.KeyValue{Key: fmt.Sprintf("method:%s", method), Value: "1"})
		result = append(result, mr.KeyValue{Key: fmt.Sprintf("ip:%s", ip), Value: "1"})

		return result
	})

	worker.SetReduceFunc(func(key string, values []string) string {
		count := 0
		for _, v := range values {
			if v == "1" {
				count++
			}
		}
		return fmt.Sprintf("%d", count)
	})

	fmt.Println("Running MapReduce log analysis...")
	master.RunWithWorkers(mr.SingleWorkerMode)

	fmt.Println("\n=== Analysis Results ===")
	fmt.Println(strings.Repeat("=", 40))

	for i := 0; i < 3; i++ {
		outputFile := filepath.Join(outputDir, fmt.Sprintf("reduce-%d", i))
		if data, err := os.ReadFile(outputFile); err == nil && len(data) > 0 {
			fmt.Printf("\n--- Partition %d ---\n", i)
			fmt.Print(string(data))
		}
	}

	os.RemoveAll(tempDir)
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("Example completed!")
}
