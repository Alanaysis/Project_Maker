// Package main benchmarks the message queue throughput.
//
// This benchmark measures:
// 1. Produce throughput (messages/second)
// 2. Consume throughput (messages/second)
// 3. Effect of batching on throughput
// 4. Effect of partition count on throughput
//
// Expected throughput depends on:
// - Disk I/O speed (SSD vs HDD)
// - Batch size (larger batches = fewer fsync calls)
// - Number of partitions (more partitions = more parallelism)
// - Ack mode (AckNone is fastest, AckAll is slowest)
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"high-throughput-message-queue/src"
)

func main() {
	fmt.Println("=== High Throughput Message Queue Benchmark ===\n")

	// Run benchmarks
	runProduceBenchmark()
	runConsumeBenchmark()
	runBatchingBenchmark()
	runPartitionScalingBenchmark()
}

// runProduceBenchmark measures raw produce throughput.
func runProduceBenchmark() {
	fmt.Println("--- Produce Throughput Benchmark ---")

	dataDir := filepath.Join(os.TempDir(), "mq-bench-produce")
	os.RemoveAll(dataDir)
	os.MkdirAll(dataDir, 0755)
	defer os.RemoveAll(dataDir)

	storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))
	topicConfig := queue.NewTopicConfig("bench", 4)
	storage.CreateTopic(topicConfig)

	producer := queue.NewProducer(queue.ProducerConfig{
		Storage:      storage,
		TopicName:    "bench",
		BatchSize:    100,
		BatchTimeout: 1000000000,
		Acks:         queue.AckLeader,
	})

	// Warm up
	for i := 0; i < 100; i++ {
		msg := queue.NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte("warmup-value"))
		producer.Send(msg)
	}
	producer.Flush()

	// Benchmark
	numMessages := 10000
	start := time.Now()

	var wg sync.WaitGroup
	numProducers := 4
	msgsPerProducer := numMessages / numProducers

	for p := 0; p < numProducers; p++ {
		wg.Add(1)
		go func(producerID int) {
			defer wg.Done()

			localProducer := queue.NewProducer(queue.ProducerConfig{
				Storage:      storage,
				TopicName:    "bench",
				BatchSize:    100,
				BatchTimeout: 1000000000,
				Acks:         queue.AckLeader,
			})

			for i := 0; i < msgsPerProducer; i++ {
				key := []byte(fmt.Sprintf("key-%d-%d", producerID, i))
				value := []byte(fmt.Sprintf("value-%d-%d", producerID, i))
				msg := queue.NewMessage(key, value)
				localProducer.Send(msg)
			}
			localProducer.Flush()
		}(p)
	}

	wg.Wait()
	elapsed := time.Since(start)

	messagesPerSec := float64(numMessages) / elapsed.Seconds()
	throughputMB := float64(numMessages*12) / (1024 * 1024) / elapsed.Seconds()

	fmt.Printf("  Messages: %d\n", numMessages)
	fmt.Printf("  Producers: %d\n", numProducers)
	fmt.Printf("  Time: %v\n", elapsed.Round(time.Millisecond))
	fmt.Printf("  Throughput: %.0f msg/sec\n", messagesPerSec)
	fmt.Printf("  Throughput: %.2f MB/sec\n", throughputMB)
	fmt.Println()
}

// runConsumeBenchmark measures raw consume throughput.
func runConsumeBenchmark() {
	fmt.Println("--- Consume Throughput Benchmark ---")

	dataDir := filepath.Join(os.TempDir(), "mq-bench-consume")
	os.RemoveAll(dataDir)
	os.MkdirAll(dataDir, 0755)
	defer os.RemoveAll(dataDir)

	storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))
	topicConfig := queue.NewTopicConfig("bench", 4)
	storage.CreateTopic(topicConfig)

	// Produce messages first
	producer := queue.NewProducer(queue.ProducerConfig{
		Storage:      storage,
		TopicName:    "bench",
		BatchSize:    100,
		BatchTimeout: 1000000000,
		Acks:         queue.AckLeader,
	})

	numMessages := 10000
	for i := 0; i < numMessages; i++ {
		msg := queue.NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte(fmt.Sprintf("value-%d", i)))
		producer.Send(msg)
	}
	producer.Flush()

	// Consume messages
	consumer := queue.NewConsumer(queue.ConsumerConfig{
		Storage: storage,
		Topic:   "bench",
		GroupID: "bench-consumer",
	})

	start := time.Now()
	totalReceived := 0

	for totalReceived < numMessages {
		messages, err := consumer.Poll(1000)
		if err != nil {
			log.Printf("Poll error: %v", err)
			break
		}
		if len(messages) == 0 {
			break
		}
		totalReceived += len(messages)
	}

	elapsed := time.Since(start)
	messagesPerSec := float64(totalReceived) / elapsed.Seconds()

	fmt.Printf("  Messages received: %d / %d\n", totalReceived, numMessages)
	fmt.Printf("  Time: %v\n", elapsed.Round(time.Millisecond))
	fmt.Printf("  Throughput: %.0f msg/sec\n", messagesPerSec)
	fmt.Println()
}

// runBatchingBenchmark shows the impact of batch size on throughput.
func runBatchingBenchmark() {
	fmt.Println("--- Batching Impact Benchmark ---")

	batchSizes := []int{1, 10, 50, 100, 500}

	for _, batchSize := range batchSizes {
		dataDir := filepath.Join(os.TempDir(), fmt.Sprintf("mq-bench-batch-%d", batchSize))
		os.RemoveAll(dataDir)
		os.MkdirAll(dataDir, 0755)
		defer os.RemoveAll(dataDir)

		storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))
		topicConfig := queue.NewTopicConfig("bench", 1)
		storage.CreateTopic(topicConfig)

		producer := queue.NewProducer(queue.ProducerConfig{
			Storage:      storage,
			TopicName:    "bench",
			BatchSize:    batchSize,
			BatchTimeout: 1000000000,
			Acks:         queue.AckNone, // Fastest mode
		})

		numMessages := 5000
		start := time.Now()

		for i := 0; i < numMessages; i++ {
			msg := queue.NewMessage([]byte(fmt.Sprintf("key-%d", i)), []byte("benchmark-value"))
			producer.Send(msg)
		}
		producer.Flush()

		elapsed := time.Since(start)
		msgsPerSec := float64(numMessages) / elapsed.Seconds()

		fmt.Printf("  Batch size %4d: %.0f msg/sec (%v)\n",
			batchSize, msgsPerSec, elapsed.Round(time.Millisecond))
	}
	fmt.Println()
}

// runPartitionScalingBenchmark shows how partition count affects throughput.
func runPartitionScalingBenchmark() {
	fmt.Println("--- Partition Scaling Benchmark ---")

	partitionCounts := []int{1, 2, 4, 8}

	for _, numParts := range partitionCounts {
		dataDir := filepath.Join(os.TempDir(), fmt.Sprintf("mq-bench-parts-%d", numParts))
		os.RemoveAll(dataDir)
		os.MkdirAll(dataDir, 0755)
		defer os.RemoveAll(dataDir)

		storage := queue.NewStorage(queue.DefaultStorageConfig(dataDir))
		topicConfig := queue.NewTopicConfig("bench", numParts)
		storage.CreateTopic(topicConfig)

		producer := queue.NewProducer(queue.ProducerConfig{
			Storage:      storage,
			TopicName:    "bench",
			BatchSize:    100,
			BatchTimeout: 1000000000,
			Acks:         queue.AckNone,
		})

		numMessages := 5000
		start := time.Now()

		for i := 0; i < numMessages; i++ {
			key := []byte(fmt.Sprintf("key-%d", i%numParts))
			msg := queue.NewMessage(key, []byte("benchmark-value"))
			producer.Send(msg)
		}
		producer.Flush()

		elapsed := time.Since(start)
		msgsPerSec := float64(numMessages) / elapsed.Seconds()

		fmt.Printf("  Partitions %2d: %.0f msg/sec (%v)\n",
			numParts, msgsPerSec, elapsed.Round(time.Millisecond))
	}
	fmt.Println()

	// Print runtime info
	fmt.Println("--- Runtime Info ---")
	fmt.Printf("  Go version: %s\n", runtime.Version())
	fmt.Printf("  Num CPU: %d\n", runtime.NumCPU())
	fmt.Printf("  GOMAXPROCS: %d\n", runtime.GOMAXPROCS(0))
	fmt.Println()
}
