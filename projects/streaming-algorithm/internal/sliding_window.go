package stream

type SlidingWindow struct {
	buffer []float64
	size   int
	pos    int
	count  int
}

func NewSlidingWindow(size int) *SlidingWindow {
	return &SlidingWindow{
		buffer: make([]float64, size),
		size:   size,
	}
}

func (sw *SlidingWindow) Add(value float64) {
	sw.buffer[sw.pos] = value
	sw.pos = (sw.pos + 1) % sw.size
	if sw.count < sw.size {
		sw.count++
	}
}

func (sw *SlidingWindow) Average() (float64, bool) {
	if sw.count == 0 {
		return 0, false
	}
	sum := 0.0
	for i := 0; i < sw.count; i++ {
		sum += sw.buffer[i]
	}
	return sum / float64(sw.count), true
}

func (sw *SlidingWindow) Values() []float64 {
	result := make([]float64, sw.count)
	for i := 0; i < sw.count; i++ {
		result[i] = sw.buffer[i]
	}
	return result
}
