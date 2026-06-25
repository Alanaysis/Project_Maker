package main

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	hyperloglog "github.com/hyperloglog/internal"
)

func main() {
	fmt.Println("=== HyperLogLog 性能测试 ===")
	fmt.Println()

	// 测试数据生成
	fmt.Println("生成测试数据...")
	dataSets := generateTestData(1000000)

	// 测试不同精度的性能
	precisions := []uint8{8, 10, 12, 14}

	fmt.Println("性能测试结果:")
	fmt.Println(strings.Repeat("-", 80))
	fmt.Printf("%-10s %-15s %-15s %-15s %-15s\n", "精度(p)", "添加耗时", "估算耗时", "内存占用", "估算基数")
	fmt.Println(strings.Repeat("-", 80))

	for _, p := range precisions {
		hll, _ := hyperloglog.New(p)

		// 测试添加性能
		start := time.Now()
		for _, data := range dataSets {
			hll.Add(data)
		}
		addDuration := time.Since(start)

		// 测试估算性能
		start = time.Now()
		estimate := hll.Estimate()
		estimateDuration := time.Since(start)

		fmt.Printf("%-10d %-15s %-15s %-15d %-15d\n",
			p,
			formatDuration(addDuration),
			formatDuration(estimateDuration),
			hll.MemoryUsage(),
			estimate)
	}
	fmt.Println(strings.Repeat("-", 80))
	fmt.Println()

	// 测试不同数据量的性能
	fmt.Println("不同数据量的性能测试 (p=12):")
	fmt.Println(strings.Repeat("-", 80))
	fmt.Printf("%-15s %-15s %-15s %-15s\n", "数据量", "添加耗时", "吞吐量", "估算基数")
	fmt.Println(strings.Repeat("-", 80))

	dataSizes := []int{1000, 10000, 100000, 1000000}
	for _, size := range dataSizes {
		hll, _ := hyperloglog.New(12)
		data := generateTestData(size)

		start := time.Now()
		for _, d := range data {
			hll.Add(d)
		}
		duration := time.Since(start)

		throughput := float64(size) / duration.Seconds()
		estimate := hll.Estimate()

		fmt.Printf("%-15d %-15s %-15.0f/s %-15d\n",
			size,
			formatDuration(duration),
			throughput,
			estimate)
	}
	fmt.Println(strings.Repeat("-", 80))
	fmt.Println()

	// 测试合并性能
	fmt.Println("合并性能测试 (p=12):")
	fmt.Println(strings.Repeat("-", 80))

	hll1, _ := hyperloglog.New(12)
	hll2, _ := hyperloglog.New(12)

	// 准备数据
	data1 := generateTestData(500000)
	data2 := generateTestData(500000)

	for _, d := range data1 {
		hll1.Add(d)
	}
	for _, d := range data2 {
		hll2.Add(d)
	}

	start := time.Now()
	hll1.Merge(hll2)
	mergeDuration := time.Since(start)

	estimate := hll1.Estimate()
	fmt.Printf("合并 1000000 个元素耗时: %s\n", formatDuration(mergeDuration))
	fmt.Printf("合并后估算基数: %d\n", estimate)
	fmt.Println(strings.Repeat("-", 80))
	fmt.Println()

	// 内存使用比较
	fmt.Println("内存使用比较:")
	fmt.Println(strings.Repeat("-", 60))
	fmt.Printf("%-10s %-15s %-15s %-15s\n", "精度(p)", "寄存器数", "内存占用", "标准误差")
	fmt.Println(strings.Repeat("-", 60))

	for _, p := range []uint8{4, 8, 10, 12, 14, 16} {
		hll, _ := hyperloglog.New(p)
		fmt.Printf("%-10d %-15d %-15d bytes %-15.2f%%\n",
			p,
			hll.Registers(),
			hll.MemoryUsage(),
			hll.StandardError()*100)
	}
	fmt.Println(strings.Repeat("-", 60))
}

// generateTestData generates random test data of the specified size.
func generateTestData(size int) [][]byte {
	data := make([][]byte, size)
	for i := 0; i < size; i++ {
		data[i] = []byte(fmt.Sprintf("element-%d-%d", i, rand.Int63()))
	}
	return data
}

// formatDuration formats a duration in a human-readable way.
func formatDuration(d time.Duration) string {
	if d < time.Microsecond {
		return fmt.Sprintf("%.2fns", float64(d.Nanoseconds()))
	} else if d < time.Millisecond {
		return fmt.Sprintf("%.2fus", float64(d.Microseconds()))
	} else if d < time.Second {
		return fmt.Sprintf("%.2fms", float64(d.Milliseconds()))
	} else {
		return fmt.Sprintf("%.2fs", d.Seconds())
	}
}
