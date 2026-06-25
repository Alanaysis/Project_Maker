package stream

import (
	"math"
	"math/bits"
)

type HyperLogLog struct {
	registers []uint8
	m         uint64
	b         uint64
	alpha     float64
}

func NewHyperLogLog(stdErr float64) *HyperLogLog {
	b := uint64(math.Ceil(math.Log2((1.04 / stdErr) * (1.04 / stdErr))))
	if b < 4 {
		b = 4
	}
	if b > 16 {
		b = 16
	}
	m := uint64(1) << b
	var alpha float64
	switch m {
	case 16:
		alpha = 0.673
	case 32:
		alpha = 0.697
	case 64:
		alpha = 0.709
	default:
		alpha = 0.7213 / (1 + 1.079/float64(m))
	}
	return &HyperLogLog{
		registers: make([]uint8, m),
		m:         m,
		b:         b,
		alpha:     alpha,
	}
}

func hash64(data []byte) uint64 {
	var h uint64 = 14695981039346656037
	for _, b := range data {
		h ^= uint64(b)
		h *= 1099511628211
	}
	h ^= h >> 33
	h *= 0xff51afd7ed558ccd
	h ^= h >> 33
	h *= 0xc4ceb9fe1a85ec53
	h ^= h >> 33
	return h
}

func (hll *HyperLogLog) Add(item string) {
	hash := hash64([]byte(item))
	idx := hash & (hll.m - 1)
	w := hash >> hll.b
	if w == 0 {
		return
	}
	rank := uint8(uint64(bits.LeadingZeros64(w)) - hll.b + 1)
	if rank > hll.registers[idx] {
		hll.registers[idx] = rank
	}
}

func (hll *HyperLogLog) Count() float64 {
	sum := 0.0
	zeros := 0
	for _, r := range hll.registers {
		if r == 0 {
			zeros++
		}
		sum += 1.0 / float64(uint64(1)<<r)
	}
	estimate := hll.alpha * float64(hll.m*hll.m) / sum
	if estimate <= 2.5*float64(hll.m) {
		if zeros > 0 {
			estimate = float64(hll.m) * math.Log(float64(hll.m)/float64(zeros))
		}
	}
	return estimate
}

func (hll *HyperLogLog) Merge(other *HyperLogLog) {
	if hll.m != other.m {
		return
	}
	for i := range hll.registers {
		if other.registers[i] > hll.registers[i] {
			hll.registers[i] = other.registers[i]
		}
	}
}
