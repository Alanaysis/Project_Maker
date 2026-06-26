package hyperloglog

import (
	"fmt"
	"math"
)

// PrintInfo prints a detailed summary of the HyperLogLog sketch state.
// Useful for debugging and educational visualization.
func (h *HyperLogLog) PrintInfo(estimate float64) {
	fmt.Printf("=== HyperLogLog Sketch Info ===\n")
	fmt.Printf("Precision (p):      %d\n", h.p)
	fmt.Printf("Buckets (m=2^p):    %d\n", h.m)
	fmt.Printf("Memory usage:       %d bytes\n", h.MemoryBytes())
	fmt.Printf("Estimate:           %.2f\n", estimate)
	fmt.Printf("Max register:       %d\n", h.MaxRegister())
	fmt.Printf("Avg register:       %.4f\n", h.AverageRegister())
	fmt.Printf("Zero buckets:       %d / %d\n", h.ZeroBucketCount(), h.m)
	fmt.Printf("Standard error:     %.4f%%\n", h.StandardError()*100)

	// Theoretical max register value
	maxPossible := int(64 - h.p) + 1
	fmt.Printf("Max possible rho:   %d\n", maxPossible)

	// Expected rho for the estimated cardinality
	if estimate > 0 {
		expectedRho := math.Log2(estimate) + 0.332
		fmt.Printf("Expected rho:       ~%.2f\n", expectedRho)
	}
	fmt.Println("===============================")
}

// PrintRegisterDistribution prints a histogram of register values.
// This helps visualize the distribution of rho values across buckets.
func (h *HyperLogLog) PrintRegisterDistribution() {
	// Count frequency of each register value
	maxReg := h.MaxRegister()
	freq := make([]int, maxReg+1)
	for _, reg := range h.registers {
		freq[reg]++
	}

	fmt.Println("\nRegister Value Distribution:")
	fmt.Println("rho | Count | Percentage | Bar")
	fmt.Println("----|-------|------------|-----")

	for rho := 0; rho <= int(maxReg); rho++ {
		percentage := float64(freq[rho]) / float64(h.m) * 100
		barLen := int(percentage / 2) // Scale to reasonable bar length
		if barLen == 0 && freq[rho] > 0 {
			barLen = 1
		}
		bar := ""
		for i := 0; i < barLen; i++ {
			bar += "█"
		}
		fmt.Printf("  %2d | %5d | %8.2f%% | %s\n", rho, freq[rho], percentage, bar)
	}
}

// PrintConfidenceInterval prints a formatted confidence interval for the estimate.
func (h *HyperLogLog) PrintConfidenceInterval(estimate float64, confidenceLevel float64) {
	lower, upper := h.ConfidenceInterval(estimate, confidenceLevel)
	levelStr := ""
	switch {
	case confidenceLevel >= 0.999:
		levelStr = "99.9%"
	case confidenceLevel >= 0.99:
		levelStr = "99%"
	case confidenceLevel >= 0.95:
		levelStr = "95%"
	case confidenceLevel >= 0.90:
		levelStr = "90%"
	default:
		levelStr = fmt.Sprintf("%.0f%%", confidenceLevel*100)
	}

	fmt.Printf("\n%s confidence interval: [%.2f, %.2f]\n", levelStr, lower, upper)
	fmt.Printf("Margin of error: ±%.2f (%.2f%%)\n", upper-estimate, (upper-estimate)/estimate*100)
}
