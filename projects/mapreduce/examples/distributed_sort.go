package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"mapreduce/src"
)

// DistributedSortingExample demonstrates how MapReduce can sort large datasets.
//
// The sorting is done in two phases:
// 1. Map phase: Each line is treated as a single element to sort
// 2. Reduce phase: Each reduce task sorts its portion, then we merge
//
// This demonstrates the "External Sort" pattern used in real MapReduce systems
// like Apache Hadoop, where data too large for memory is sorted in chunks.
func main() {
	tempDir := filepath.Join(os.TempDir(), "mapreduce-sort")
	inputDir := filepath.Join(tempDir, "input")
	outputDir := filepath.Join(tempDir, "output")

	os.RemoveAll(tempDir)
	os.MkdirAll(inputDir, 0755)
	os.MkdirAll(outputDir, 0755)

	inputData := []struct {
		name    string
		content string
	}{
		{"input-0.txt", "93\n47\n12\n85\n31\n"},
		{"input-1.txt", "66\n28\n74\n53\n19\n"},
		{"input-2.txt", "81\n35\n62\n44\n77\n"},
	}

	var inputFiles []string
	for _, data := range inputData {
		filename := filepath.Join(inputDir, data.name)
		os.WriteFile(filename, []byte(data.content), 0644)
		inputFiles = append(inputFiles, filename)
	}

	fmt.Println("=== Distributed Sorting Example ===")
	fmt.Printf("Input files: %d\n", len(inputFiles))
	fmt.Println()

	master := mr.NewMaster(mr.MasterConfig{
		InputFiles:     inputFiles,
		OutputDir:      outputDir,
		TempDir:        filepath.Join(tempDir, "temp"),
		NumReduceTasks: 3,
	})

	worker := master.NewWorker("worker-1")

	// Map function: emit each line as a key-value pair for sorting
	worker.SetMapFunc(func(key string, value string) []mr.KeyValue {
		value = strings.TrimSpace(value)
		if value == "" {
			return nil
		}
		return []mr.KeyValue{{Key: value, Value: value}}
	})

	// Reduce function: sort the values within this partition
	worker.SetReduceFunc(func(key string, values []string) string {
		sort.Strings(values)
		return strings.Join(values, ",")
	})

	fmt.Println("Running MapReduce sort job...")
	master.RunWithWorkers(mr.SingleWorkerMode)

	fmt.Println("\nSorted results (per partition):")
	fmt.Println(strings.Repeat("=", 40))

	for i := 0; i < 3; i++ {
		outputFile := filepath.Join(outputDir, fmt.Sprintf("reduce-%d", i))
		if data, err := os.ReadFile(outputFile); err == nil && len(data) > 0 {
			fmt.Printf("Partition %d: %s\n", i, strings.TrimSpace(string(data)))
		}
	}

	allValues := make([]string, 0)
	for i := 0; i < 3; i++ {
		outputFile := filepath.Join(outputDir, fmt.Sprintf("reduce-%d", i))
		if data, err := os.ReadFile(outputFile); err == nil {
			lines := strings.Split(strings.TrimSpace(string(data)), "\n")
			for _, line := range lines {
				parts := strings.Split(line, "\t")
				if len(parts) >= 2 {
					vals := strings.Split(parts[1], ",")
					allValues = append(allValues, vals...)
				}
			}
		}
	}
	sort.Strings(allValues)

	fmt.Println("\nFully sorted output:")
	fmt.Println(strings.Repeat("-", 40))
	for _, v := range allValues {
		fmt.Println(v)
	}

	os.RemoveAll(tempDir)
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("Example completed!")
}
