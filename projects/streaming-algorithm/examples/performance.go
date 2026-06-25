package main

import (
	"fmt"
	"math/rand"
	"time"

	stream "github.com/streaming-algorithm/internal"
)

func main() {
	n := 1_000_000

	fmt.Printf("性能测试: %d 条数据\n\n", n)

	start := time.Now()
	sw := stream.NewSlidingWindow(1000)
	for i := 0; i < n; i++ {
		sw.Add(float64(rand.Float64() * 1000))
	}
	avg, _ := sw.Average()
	fmt.Printf("滑动窗口: %v, 平均: %.2f\n", time.Since(start), avg)

	start = time.Now()
	rs := stream.NewReservoirSampler(100)
	for i := 0; i < n; i++ {
		rs.Sample(rand.Intn(10000))
	}
	fmt.Printf("蓄水池采样: %v, 样本: %v\n", time.Since(start), rs.GetSample())

	start = time.Now()
	hll := stream.NewHyperLogLog(0.01)
	for i := 0; i < n; i++ {
		hll.Add(fmt.Sprintf("item_%d", rand.Intn(500000)))
	}
	est := hll.Count()
	fmt.Printf("HyperLogLog: %v, 估计基数: %.0f\n", time.Since(start), est)

	start = time.Now()
	tk := stream.NewTopK(10)
	for i := 0; i < n; i++ {
		tk.Add(fmt.Sprintf("word_%d", rand.Intn(10000)))
	}
	fmt.Printf("Top-K: %v\n", time.Since(start))
	for _, item := range tk.Top() {
		fmt.Printf("  %s\n", item.Item)
	}
}
