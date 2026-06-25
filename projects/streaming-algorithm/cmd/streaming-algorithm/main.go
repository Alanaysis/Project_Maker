package main

import (
	"fmt"
	"math/rand"

	stream "github.com/streaming-algorithm/internal"
)

func main() {
	fmt.Println("=== 流式算法演示 ===")

	// 滑动窗口平均
	fmt.Println("\n--- 滑动窗口平均 ---")
	sw := stream.NewSlidingWindow(5)
	data := []float64{10, 20, 30, 40, 50, 60, 70, 80, 90, 100}
	for _, v := range data {
		sw.Add(v)
		avg, ok := sw.Average()
		if ok {
			fmt.Printf("添加 %.0f, 窗口平均值: %.1f\n", v, avg)
		}
	}

	// 蓄水池采样
	fmt.Println("\n--- 蓄水池采样 (k=3) ---")
	rs := stream.NewReservoirSampler(3)
	for i := 0; i < 100; i++ {
		rs.Sample(i)
	}
	fmt.Printf("采样结果: %v\n", rs.GetSample())

	// 计数器
	fmt.Println("\n--- 计数器 ---")
	hc := stream.NewHyperLogLog(0.01)
	for i := 0; i < 10000; i++ {
		hc.Add(fmt.Sprintf("user_%d", rand.Intn(5000)))
	}
	estimated := hc.Count()
	fmt.Printf("实际基数: ~5000, 估计基数: %.0f\n", estimated)

	// Top-K
	fmt.Println("\n--- Top-K 频繁项 ---")
	tk := stream.NewTopK(3)
	items := []string{"a", "b", "a", "c", "a", "b", "d", "a", "c", "b", "c", "c", "b", "a", "d"}
	for _, item := range items {
		tk.Add(item)
	}
	fmt.Printf("Top-%d: %v\n", 3, tk.Top())
}
