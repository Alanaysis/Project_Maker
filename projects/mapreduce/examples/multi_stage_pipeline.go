package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"mapreduce/src"
)

// MultiStagePipelineExample demonstrates chaining multiple MapReduce jobs together.
//
// This example shows a two-stage pipeline:
// Stage 1: Count word frequencies in input text
// Stage 2: Group words by their frequency (frequency -> list of words)
//
// Multi-stage MapReduce is how complex data processing pipelines are built
// in practice. Each stage's output becomes the next stage's input.
func main() {
	tempDir := filepath.Join(os.TempDir(), "mapreduce-pipeline")

	stage1InputDir := filepath.Join(tempDir, "stage1-input")
	stage1OutputDir := filepath.Join(tempDir, "stage1-output")
	stage1TempDir := filepath.Join(tempDir, "stage1-temp")

	stage2InputDir := filepath.Join(tempDir, "stage2-input")
	stage2OutputDir := filepath.Join(tempDir, "stage2-output")
	stage2TempDir := filepath.Join(tempDir, "stage2-temp")

	os.RemoveAll(tempDir)
	os.MkdirAll(stage1InputDir, 0755)
	os.MkdirAll(stage1OutputDir, 0755)
	os.MkdirAll(stage1TempDir, 0755)
	os.MkdirAll(stage2InputDir, 0755)
	os.MkdirAll(stage2OutputDir, 0755)
	os.MkdirAll(stage2TempDir, 0755)

	contents := []string{
		"the quick brown fox jumps over the lazy dog",
		"the fox and the dog played in the park",
		"the quick fox was very quick and the dog was lazy",
	}

	var inputFiles []string
	for i, content := range contents {
		filename := filepath.Join(stage1InputDir, fmt.Sprintf("text-%d.txt", i))
		os.WriteFile(filename, []byte(content), 0644)
		inputFiles = append(inputFiles, filename)
	}

	fmt.Println("=== Multi-Stage MapReduce Pipeline ===")
	fmt.Println("Stage 1: Word Count")
	fmt.Println("Stage 2: Group by Frequency")
	fmt.Println()

	fmt.Println("--- Stage 1: Word Count ---")

	master1 := mr.NewMaster(mr.MasterConfig{
		InputFiles:     inputFiles,
		OutputDir:      stage1OutputDir,
		TempDir:        stage1TempDir,
		NumReduceTasks: 2,
	})

	worker1 := master1.NewWorker("worker-stage1")

	worker1.SetMapFunc(func(key string, value string) []mr.KeyValue {
		var result []mr.KeyValue
		words := strings.Fields(value)
		for _, word := range words {
			word = strings.ToLower(strings.Trim(word, ".,!?;:\"'()"))
			if word != "" {
				result = append(result, mr.KeyValue{Key: word, Value: "1"})
			}
		}
		return result
	})

	worker1.SetReduceFunc(func(key string, values []string) string {
		count := 0
		for _, v := range values {
			if v == "1" {
				count++
			}
		}
		return fmt.Sprintf("%s\t%d", key, count)
	})

	master1.RunWithWorkers(mr.SingleWorkerMode)

	stage1Results := make(map[string]int)
	for i := 0; i < 2; i++ {
		outputFile := filepath.Join(stage1OutputDir, fmt.Sprintf("reduce-%d", i))
		if data, err := os.ReadFile(outputFile); err == nil {
			lines := strings.Split(strings.TrimSpace(string(data)), "\n")
			for _, line := range lines {
				parts := strings.Split(line, "\t")
				if len(parts) == 2 {
					stage1Results[parts[0]] = 0
					fmt.Printf("  %s: %s\n", parts[0], parts[1])
				}
			}
		}
	}

	fmt.Println("\n--- Stage 2: Group by Frequency ---")

	var stage2Files []string
	for word := range stage1Results {
		filename := filepath.Join(stage2InputDir, fmt.Sprintf("word-%s.txt", word))
		os.WriteFile(filename, []byte("1"), 0644)
		stage2Files = append(stage2Files, filename)
	}

	master2 := mr.NewMaster(mr.MasterConfig{
		InputFiles:     stage2Files,
		OutputDir:      stage2OutputDir,
		TempDir:        stage2TempDir,
		NumReduceTasks: 2,
	})

	worker2 := master2.NewWorker("worker-stage2")

	worker2.SetMapFunc(func(key string, value string) []mr.KeyValue {
		return []mr.KeyValue{
			{Key: fmt.Sprintf("freq:%s", value), Value: key},
		}
	})

	worker2.SetReduceFunc(func(key string, values []string) string {
		return strings.Join(values, ",")
	})

	master2.RunWithWorkers(mr.SingleWorkerMode)

	fmt.Println("\nWords grouped by frequency:")
	fmt.Println(strings.Repeat("-", 40))
	for i := 0; i < 2; i++ {
		outputFile := filepath.Join(stage2OutputDir, fmt.Sprintf("reduce-%d", i))
		if data, err := os.ReadFile(outputFile); err == nil && len(data) > 0 {
			fmt.Printf("Partition %d:\n%s\n", i, string(data))
		}
	}

	os.RemoveAll(tempDir)
	fmt.Println(strings.Repeat("=", 40))
	fmt.Println("Pipeline completed!")
}
