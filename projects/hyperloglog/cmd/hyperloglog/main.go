package main

import (
	"fmt"
	"math"
	"os"
	"strings"
	"time"

	hyperloglog "github.com/hyperloglog/internal"
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		return
	}

	switch os.Args[1] {
	case "demo":
		runDemo()
	case "benchmark":
		runBenchmark()
	case "accuracy":
		runAccuracyTest()
	case "help":
		printUsage()
	default:
		fmt.Printf("未知命令: %s\n", os.Args[1])
		printUsage()
	}
}

func printUsage() {
	fmt.Println("HyperLogLog 基数估计工具")
	fmt.Println()
	fmt.Println("用法:")
	fmt.Println("  hyperloglog <command>")
	fmt.Println()
	fmt.Println("命令:")
	fmt.Println("  demo        运行基本演示")
	fmt.Println("  benchmark   运行性能测试")
	fmt.Println("  accuracy    运行精度测试")
	fmt.Println("  help        显示帮助信息")
}

func runDemo() {
	fmt.Println("=== HyperLogLog 演示 ===")
	fmt.Println()

	// 创建 HyperLogLog
	hll, err := hyperloglog.New(12)
	if err != nil {
		fmt.Printf("创建失败: %v\n", err)
		return
	}

	fmt.Printf("创建 HyperLogLog (p=%d)\n", hll.Precision())
	fmt.Printf("寄存器数量: %d\n", hll.Registers())
	fmt.Printf("内存占用: %d 字节\n", hll.MemoryUsage())
	fmt.Printf("理论标准误差: %.2f%%\n", hll.StandardError()*100)
	fmt.Println()

	// 添加元素
	fmt.Println("添加 10000 个不同元素...")
	start := time.Now()
	for i := 0; i < 10000; i++ {
		hll.Add([]byte(fmt.Sprintf("user-%d", i)))
	}
	duration := time.Since(start)

	// 估算基数
	estimate := hll.Estimate()
	errorRate := math.Abs(float64(estimate)-10000) / 10000

	fmt.Printf("添加耗时: %s\n", duration)
	fmt.Printf("实际基数: 10000\n")
	fmt.Printf("估算基数: %d\n", estimate)
	fmt.Printf("误差率: %.2f%%\n", errorRate*100)
	fmt.Println()

	// 寄存器统计
	stats := hll.GetRegisterStats()
	fmt.Println("寄存器统计:")
	fmt.Printf("  最小值: %d\n", stats.Min)
	fmt.Printf("  最大值: %d\n", stats.Max)
	fmt.Printf("  平均值: %.2f\n", stats.Average)
	fmt.Printf("  空寄存器: %d (%.1f%%)\n", stats.Empty, float64(stats.Empty)/float64(hll.Registers())*100)
	fmt.Printf("  非空寄存器: %d (%.1f%%)\n", stats.NonEmpty, float64(stats.NonEmpty)/float64(hll.Registers())*100)
}

func runBenchmark() {
	fmt.Println("=== HyperLogLog 性能测试 ===")
	fmt.Println()

	precisions := []uint8{8, 10, 12, 14}
	dataSize := 1000000

	fmt.Printf("测试数据量: %d\n", dataSize)
	fmt.Println()
	fmt.Println(strings.Repeat("-", 80))
	fmt.Printf("%-10s %-15s %-15s %-15s %-15s\n", "精度(p)", "添加耗时", "估算耗时", "吞吐量", "估算基数")
	fmt.Println(strings.Repeat("-", 80))

	for _, p := range precisions {
		hll, _ := hyperloglog.New(p)

		// 生成数据
		data := make([][]byte, dataSize)
		for i := 0; i < dataSize; i++ {
			data[i] = []byte(fmt.Sprintf("element-%d", i))
		}

		// 测试添加性能
		start := time.Now()
		for _, d := range data {
			hll.Add(d)
		}
		addDuration := time.Since(start)

		// 测试估算性能
		start = time.Now()
		estimate := hll.Estimate()
		estimateDuration := time.Since(start)

		throughput := float64(dataSize) / addDuration.Seconds()

		fmt.Printf("%-10d %-15s %-15s %-15.0f/s %-15d\n",
			p,
			formatDuration(addDuration),
			formatDuration(estimateDuration),
			throughput,
			estimate)
	}
	fmt.Println(strings.Repeat("-", 80))
}

func runAccuracyTest() {
	fmt.Println("=== HyperLogLog 精度测试 ===")
	fmt.Println()

	cardinalities := []int{100, 1000, 10000, 100000}
	precisions := []uint8{8, 10, 12, 14}

	fmt.Println("不同基数和精度下的误差率:")
	fmt.Println(strings.Repeat("-", 80))

	// 打印表头
	header := fmt.Sprintf("%-15s", "基数")
	for _, p := range precisions {
		header += fmt.Sprintf("%-15s", fmt.Sprintf("p=%d", p))
	}
	fmt.Println(header)
	fmt.Println(strings.Repeat("-", 80))

	for _, cardinality := range cardinalities {
		row := fmt.Sprintf("%-15d", cardinality)

		for _, p := range precisions {
			hll, _ := hyperloglog.New(p)

			for i := 0; i < cardinality; i++ {
				hll.Add([]byte(fmt.Sprintf("element-%d", i)))
			}

			estimate := hll.Estimate()
			errorRate := math.Abs(float64(estimate)-float64(cardinality)) / float64(cardinality)

			row += fmt.Sprintf("%-15.2f%%", errorRate*100)
		}

		fmt.Println(row)
	}
	fmt.Println(strings.Repeat("-", 80))
}

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
