package stream

import "math/rand"

type ReservoirSampler struct {
	sample []int
	size   int
	count  int
}

func NewReservoirSampler(k int) *ReservoirSampler {
	return &ReservoirSampler{
		sample: make([]int, 0, k),
		size:   k,
	}
}

func (rs *ReservoirSampler) Sample(value int) {
	rs.count++
	if len(rs.sample) < rs.size {
		rs.sample = append(rs.sample, value)
		return
	}
	j := rand.Intn(rs.count)
	if j < rs.size {
		rs.sample[j] = value
	}
}

func (rs *ReservoirSampler) GetSample() []int {
	result := make([]int, len(rs.sample))
	copy(result, rs.sample)
	return result
}
