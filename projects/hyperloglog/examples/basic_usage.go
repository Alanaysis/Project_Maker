package main

import (
	"fmt"
	"math"
	"strings"

	hyperloglog "github.com/hyperloglog/internal"
)

func main() {
	fmt.Println("=== HyperLogLog 基本使用示例 ===")
	fmt.Println()

	// 1. 创建 HyperLogLog 实例
	hll, err := hyperloglog.New(12) // p=12, 4096 registers
	if err != nil {
		fmt.Printf("创建 HyperLogLog 失败: %v\n", err)
		return
	}

	fmt.Printf("精度参数 p = %d\n", hll.Precision())
	fmt.Printf("寄存器数量 m = %d\n", hll.Registers())
	fmt.Printf("内存占用 = %d 字节\n", hll.MemoryUsage())
	fmt.Printf("理论标准误差 = %.2f%%\n", hll.StandardError()*100)
	fmt.Println()

	// 2. 添加元素
	fmt.Println("添加 10000 个不同元素...")
	for i := 0; i < 10000; i++ {
		hll.Add([]byte(fmt.Sprintf("user-%d", i)))
	}

	// 3. 估算基数
	estimate := hll.Estimate()
	errorRate := math.Abs(float64(estimate)-10000) / 10000

	fmt.Printf("实际基数: 10000\n")
	fmt.Printf("估算基数: %d\n", estimate)
	fmt.Printf("误差率: %.2f%%\n", errorRate*100)
	fmt.Println()

	// 4. 查看寄存器统计
	stats := hll.GetRegisterStats()
	fmt.Println("寄存器统计:")
	fmt.Printf("  最小值: %d\n", stats.Min)
	fmt.Printf("  最大值: %d\n", stats.Max)
	fmt.Printf("  平均值: %.2f\n", stats.Average)
	fmt.Printf("  空寄存器: %d (%.1f%%)\n", stats.Empty, float64(stats.Empty)/float64(hll.Registers())*100)
	fmt.Printf("  非空寄存器: %d (%.1f%%)\n", stats.NonEmpty, float64(stats.NonEmpty)/float64(hll.Registers())*100)
	fmt.Println()

	// 5. 测试重复元素
	fmt.Println("测试重复元素...")
	hll.Reset()
	for i := 0; i < 1000; i++ {
		hll.Add([]byte("duplicate-element"))
	}

	estimate = hll.Estimate()
	fmt.Printf("添加 1000 次相同元素后估算: %d\n", estimate)
	fmt.Println()

	// 6. 测试合并
	fmt.Println("测试合并两个 HyperLogLog...")
	hll1, _ := hyperloglog.New(12)
	hll2, _ := hyperloglog.New(12)

	// 添加不同的元素到两个集合
	for i := 0; i < 5000; i++ {
		hll1.Add([]byte(fmt.Sprintf("set1-%d", i)))
	}
	for i := 0; i < 5000; i++ {
		hll2.Add([]byte(fmt.Sprintf("set2-%d", i)))
	}

	// 合并
	err = hll1.Merge(hll2)
	if err != nil {
		fmt.Printf("合并失败: %v\n", err)
		return
	}

	estimate = hll1.Estimate()
	errorRate = math.Abs(float64(estimate)-10000) / 10000

	fmt.Printf("合并后估算基数: %d (期望 ~10000)\n", estimate)
	fmt.Printf("误差率: %.2f%%\n", errorRate*100)
	fmt.Println()

	// 7. 不同精度的比较
	fmt.Println("不同精度的比较 (实际基数 = 10000):")
	fmt.Println(strings.Repeat("-", 50))
	fmt.Printf("%-10s %-15s %-15s %-10s\n", "精度(p)", "寄存器数", "估算基数", "误差率")
	fmt.Println(strings.Repeat("-", 50))

	for _, p := range []uint8{4, 8, 10, 12, 14, 16} {
		hll, _ := hyperloglog.New(p)
		for i := 0; i < 10000; i++ {
			hll.Add([]byte(fmt.Sprintf("element-%d", i)))
		}
		est := hll.Estimate()
		err := math.Abs(float64(est)-10000) / 10000
		fmt.Printf("%-10d %-15d %-15d %-10.2f%%\n", p, hll.Registers(), est, err*100)
	}
	fmt.Println(strings.Repeat("-", 50))
}
