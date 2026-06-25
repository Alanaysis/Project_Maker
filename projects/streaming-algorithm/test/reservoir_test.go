package test

import (
	"testing"

	stream "github.com/streaming-algorithm/internal"
)

func TestReservoirSamplerLessThanK(t *testing.T) {
	rs := stream.NewReservoirSampler(5)
	for i := 0; i < 3; i++ {
		rs.Sample(i)
	}
	sample := rs.GetSample()
	if len(sample) != 3 {
		t.Fatalf("expected 3 samples, got %d", len(sample))
	}
}

func TestReservoirSamplerExactK(t *testing.T) {
	rs := stream.NewReservoirSampler(3)
	for i := 0; i < 3; i++ {
		rs.Sample(i)
	}
	sample := rs.GetSample()
	if len(sample) != 3 {
		t.Fatalf("expected 3 samples, got %d", len(sample))
	}
}

func TestReservoirSamplerMoreThanK(t *testing.T) {
	rs := stream.NewReservoirSampler(3)
	for i := 0; i < 100; i++ {
		rs.Sample(i)
	}
	sample := rs.GetSample()
	if len(sample) != 3 {
		t.Fatalf("expected 3 samples, got %d", len(sample))
	}
}

func TestReservoirSamplerSize(t *testing.T) {
	rs := stream.NewReservoirSampler(3)
	for i := 0; i < 1000; i++ {
		rs.Sample(i)
	}
	if len(rs.GetSample()) != 3 {
		t.Error("sample size should always equal k")
	}
}
