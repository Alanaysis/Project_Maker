package main

import (
	"fmt"
	"math/rand"

	stream "github.com/streaming-algorithm/internal"
)

func simulateSensorData() <-chan float64 {
	ch := make(chan float64)
	go func() {
		base := 25.0
		for i := 0; i < 1000; i++ {
			noise := rand.Float64()*4 - 2
			ch <- base + noise
			if i%200 == 199 {
				base += 10
			}
		}
		close(ch)
	}()
	return ch
}

func main() {
	fmt.Println("=== 传感器流式数据分析 ===")

	window := stream.NewSlidingWindow(50)
	sampler := stream.NewReservoirSampler(20)
	anomalyCounter := stream.NewTopK(5)

	dataCh := simulateSensorData()
	var prevAvg float64

	for v := range dataCh {
		window.Add(v)
		sampler.Sample(int(v * 100))

		avg, ok := window.Average()
		if ok && prevAvg != 0 {
			diff := avg - prevAvg
			if diff > 5 || diff < -5 {
				label := fmt.Sprintf("突变_%.0f", diff)
				anomalyCounter.Add(label)
			}
		}
		prevAvg = avg
	}

	fmt.Printf("最后窗口均值: %.2f\n", prevAvg)
	fmt.Printf("数据采样 (n=%d): %v\n", len(sampler.GetSample()), sampler.GetSample())
	fmt.Println("异常模式:")
	for _, item := range anomalyCounter.Top() {
		fmt.Printf("  %s: %d次\n", item.Item, item.Count)
	}
}
