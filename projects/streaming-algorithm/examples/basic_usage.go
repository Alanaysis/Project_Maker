package main

import (
	"fmt"
	"math/rand"

	stream "github.com/streaming-algorithm/internal"
)

func main() {
	fmt.Println("=== 滑动窗口 ===")
	sw := stream.NewSlidingWindow(5)
	for i := 1; i <= 10; i++ {
		sw.Add(float64(i * 10))
		avg, _ := sw.Average()
		fmt.Printf("添加 %d, 窗口: %v, 平均: %.0f\n", i*10, sw.Values(), avg)
	}

	fmt.Println("\n=== 蓄水池采样 (从1000个元素中采样5个) ===")
	rs := stream.NewReservoirSampler(5)
	for i := 0; i < 1000; i++ {
		rs.Sample(i)
	}
	fmt.Printf("采样结果: %v\n", rs.GetSample())

	fmt.Println("\n=== HyperLogLog 基数估计 ===")
	hll := stream.NewHyperLogLog(0.02)
	for i := 0; i < 10000; i++ {
		hll.Add(fmt.Sprintf("user_%d", rand.Intn(2000)))
	}
	fmt.Printf("估计基数: %.0f (实际基数: 2000)\n", hll.Count())

	fmt.Println("\n=== Top-K 频繁项 ===")
	tk := stream.NewTopK(3)
	words := []string{"go", "rust", "go", "python", "go", "rust", "java", "go", "python", "rust"}
	for _, w := range words {
		tk.Add(w)
	}
	for _, item := range tk.Top() {
		fmt.Printf("  %s: %d次\n", item.Item, item.Count)
	}
}
