package main

import (
	"fmt"
	"math"
	"strings"

	hyperloglog "github.com/hyperloglog/internal"
)

func main() {
	fmt.Println("=== HyperLogLog 精度分析 ===")
	fmt.Println()

	// 测试不同基数下的精度
	cardinalities := []int{100, 1000, 10000, 100000, 1000000}
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

			// 添加元素
			for i := 0; i < cardinality; i++ {
				hll.Add([]byte(fmt.Sprintf("element-%d", i)))
			}

			// 估算
			estimate := hll.Estimate()
			errorRate := math.Abs(float64(estimate)-float64(cardinality)) / float64(cardinality)

			row += fmt.Sprintf("%-15.2f%%", errorRate*100)
		}

		fmt.Println(row)
	}
	fmt.Println(strings.Repeat("-", 80))
	fmt.Println()

	// 多次测试取平均
	fmt.Println("多次测试取平均 (p=12, 基数=10000):")
	fmt.Println(strings.Repeat("-", 60))

	numTrials := 10
	var totalError float64
	var minError, maxError float64 = 100, 0

	for trial := 0; trial < numTrials; trial++ {
		hll, _ := hyperloglog.New(12)

		for i := 0; i < 10000; i++ {
			hll.Add([]byte(fmt.Sprintf("trial-%d-element-%d", trial, i)))
		}

		estimate := hll.Estimate()
		errorRate := math.Abs(float64(estimate)-10000) / 10000

		totalError += errorRate
		if errorRate < minError {
			minError = errorRate
		}
		if errorRate > maxError {
			maxError = errorRate
		}

		fmt.Printf("试验 %2d: 估算=%5d, 误差=%.2f%%\n", trial+1, estimate, errorRate*100)
	}

	avgError := totalError / float64(numTrials)
	fmt.Println(strings.Repeat("-", 60))
	fmt.Printf("平均误差: %.2f%%\n", avgError*100)
	fmt.Printf("最小误差: %.2f%%\n", minError*100)
	fmt.Printf("最大误差: %.2f%%\n", maxError*100)
	fmt.Printf("理论标准误差: %.2f%%\n", 1.04/math.Sqrt(4096)*100)
	fmt.Println()

	// 寄存器分布分析
	fmt.Println("寄存器分布分析 (p=12, 基数=10000):")
	fmt.Println(strings.Repeat("-", 60))

	hll, _ := hyperloglog.New(12)
	for i := 0; i < 10000; i++ {
		hll.Add([]byte(fmt.Sprintf("dist-element-%d", i)))
	}

	stats := hll.GetRegisterStats()
	fmt.Printf("最小值: %d\n", stats.Min)
	fmt.Printf("最大值: %d\n", stats.Max)
	fmt.Printf("平均值: %.2f\n", stats.Average)
	fmt.Printf("空寄存器: %d (%.1f%%)\n", stats.Empty, float64(stats.Empty)/float64(hll.Registers())*100)
	fmt.Printf("非空寄存器: %d (%.1f%%)\n", stats.NonEmpty, float64(stats.NonEmpty)/float64(hll.Registers())*100)
	fmt.Printf("密度: %.2f%%\n", hll.Density()*100)
	fmt.Println()

	// 理论分析
	fmt.Println("理论分析:")
	fmt.Println(strings.Repeat("-", 60))
	fmt.Println("HyperLogLog 的精度由以下因素决定:")
	fmt.Println("1. 精度参数 p: 决定寄存器数量 m = 2^p")
	fmt.Println("2. 标准误差: SE = 1.04 / sqrt(m)")
	fmt.Println("3. 寄存器数量: m = 2^p")
	fmt.Println()
	fmt.Println("精度与资源的权衡:")
	fmt.Println("- p=8:  256 寄存器, 6.5% 误差, 256 字节")
	fmt.Println("- p=10: 1024 寄存器, 3.25% 误差, 1KB")
	fmt.Println("- p=12: 4096 寄存器, 1.6% 误差, 4KB")
	fmt.Println("- p=14: 16384 寄存器, 0.8% 误差, 16KB")
	fmt.Println("- p=16: 65536 寄存器, 0.4% 误差, 64KB")
	fmt.Println()
	fmt.Println("一般推荐 p=12 (1.6% 误差, 4KB 内存)")
}
