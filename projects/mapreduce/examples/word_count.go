package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"mapreduce/src"
)

// WordCountExample demonstrates the classic MapReduce word count problem.
//
// Map phase: Split each line into words and emit (word, 1) pairs
// Reduce phase: Sum all the 1s for each word to get the total count
//
// This is the "Hello World" of MapReduce and illustrates the core concepts:
// - Data parallelism: each line is processed independently
// - Key grouping: all occurrences of the same word are grouped together
// - Aggregation: summing counts across all map outputs
func main() {
	tempDir := filepath.Join(os.TempDir(), "mapreduce-wordcount")
	inputDir := filepath.Join(tempDir, "input")
	outputDir := filepath.Join(tempDir, "output")

	os.RemoveAll(tempDir)
	os.MkdirAll(inputDir, 0755)
	os.MkdirAll(outputDir, 0755)

	files := []string{
		"hello world hello go mapreduce",
		"world of mapreduce is great",
		"go is a great programming language",
		"mapreduce processes large datasets",
		"hello from mapreduce world",
	}

	var inputFiles []string
	for i, content := range files {
		filename := filepath.Join(inputDir, fmt.Sprintf("input-%d.txt", i))
		os.WriteFile(filename, []byte(content), 0644)
		inputFiles = append(inputFiles, filename)
	}

	fmt.Println("=== Word Count Example ===")
	fmt.Printf("Input files: %d\n", len(inputFiles))
	fmt.Println()

	master := mr.NewMaster(mr.MasterConfig{
		InputFiles:     inputFiles,
		OutputDir:      outputDir,
		TempDir:        filepath.Join(tempDir, "temp"),
		NumReduceTasks: 3,
	})

	worker := master.NewWorker("worker-1")

	// Map function: split text into words, emit (word, 1) for each
	worker.SetMapFunc(func(key string, value string) []mr.KeyValue {
		var result []mr.KeyValue
		words := strings.Fields(value)
		for _, word := range words {
			word = strings.ToLower(strings.Trim(word, ".,!?;:\"'()[]{}"))
			if word != "" {
				result = append(result, mr.KeyValue{Key: word, Value: "1"})
			}
		}
		return result
	})

	// Reduce function: sum all values for each key
	worker.SetReduceFunc(func(key string, values []string) string {
		count := 0
		for _, v := range values {
			if v == "1" {
				count++
			}
		}
		return fmt.Sprintf("%d", count)
	})

	fmt.Println("Running MapReduce job...")
	master.RunWithWorkers(mr.SingleWorkerMode)

	fmt.Println("\nResults:")
	fmt.Println(strings.Repeat("=", 40))

	outputFile := filepath.Join(outputDir, "reduce-0")
	if data, err := os.ReadFile(outputFile); err == nil {
		fmt.Print(string(data))
	}

	os.RemoveAll(tempDir)
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("Example completed!")
}
