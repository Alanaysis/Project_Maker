package mr

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// readInputFile reads an input file and returns it as a list of KeyValue pairs.
func readInputFile(filename string) []KeyValue {
	file, err := os.Open(filename)
	if err != nil {
		panic(fmt.Sprintf("Failed to open input file %s: %v", filename, err))
	}
	defer file.Close()

	var kvs []KeyValue
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		kvs = append(kvs, KeyValue{Key: "", Value: line})
	}
	return kvs
}

// PartitionWriter manages intermediate key-value pairs for a single reduce partition.
type PartitionWriter struct {
	partition int
	tasks     map[string][]string
}

func (pw *PartitionWriter) add(key, value string) {
	pw.tasks[key] = append(pw.tasks[key], value)
}

func (pw *PartitionWriter) writeToFile(dir string, mapTaskID int) {
	filename := fmt.Sprintf("map-%d-reduce-%d", mapTaskID, pw.partition)
	filepath := filepath.Join(dir, filename)

	file, err := os.Create(filepath)
	if err != nil {
		panic(fmt.Sprintf("Failed to create temp file %s: %v", filepath, err))
	}
	defer file.Close()

	writer := bufio.NewWriter(file)
	for key, values := range pw.tasks {
		for _, value := range values {
			entry := map[string]string{"key": key, "value": value}
			data, _ := json.Marshal(entry)
			writer.WriteString(string(data) + "\n")
		}
	}
	writer.Flush()
}

// readPartitionFile reads intermediate data from a partition file.
func readPartitionFile(dir string, mapTaskID, reduceTaskID int) []KeyValue {
	filename := fmt.Sprintf("map-%d-reduce-%d", mapTaskID, reduceTaskID)
	filepath := filepath.Join(dir, filename)

	file, err := os.Open(filepath)
	if err != nil {
		return nil
	}
	defer file.Close()

	var kvs []KeyValue
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		var entry map[string]string
		if err := json.Unmarshal([]byte(scanner.Text()), &entry); err != nil {
			continue
		}
		kvs = append(kvs, KeyValue{Key: entry["key"], Value: entry["value"]})
	}
	return kvs
}

// sortedKeys returns the keys of a map sorted in ascending order.
func sortedKeys(m map[string][]string) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// writeOutput writes a reduce task result to an output file.
func writeOutput(dir string, reduceTaskID int, key, value string) {
	filename := fmt.Sprintf("reduce-%d", reduceTaskID)
	filepath := filepath.Join(dir, filename)

	file, err := os.OpenFile(filepath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		panic(fmt.Sprintf("Failed to create output file %s: %v", filepath, err))
	}
	defer file.Close()

	fmt.Fprintf(file, "%s\t%s\n", key, value)
}
