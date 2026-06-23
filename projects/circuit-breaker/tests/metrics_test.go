package tests

import (
    "testing"

    "circuit-breaker/src"
)

func TestMetrics_RecordSuccess(t *testing.T) {
    m := src.NewMetrics()

    m.RecordSuccess()

    if m.GetTotalRequests() != 1 {
        t.Errorf("Expected total requests to be 1, got %d", m.GetTotalRequests())
    }
    if m.GetSuccessCount() != 1 {
        t.Errorf("Expected success count to be 1, got %d", m.GetSuccessCount())
    }
    if m.GetFailureCount() != 0 {
        t.Errorf("Expected failure count to be 0, got %d", m.GetFailureCount())
    }
    if m.GetConsecutiveSuccess() != 1 {
        t.Errorf("Expected consecutive success to be 1, got %d", m.GetConsecutiveSuccess())
    }
    if m.GetConsecutiveFailure() != 0 {
        t.Errorf("Expected consecutive failure to be 0, got %d", m.GetConsecutiveFailure())
    }
}

func TestMetrics_RecordFailure(t *testing.T) {
    m := src.NewMetrics()

    m.RecordFailure()

    if m.GetTotalRequests() != 1 {
        t.Errorf("Expected total requests to be 1, got %d", m.GetTotalRequests())
    }
    if m.GetSuccessCount() != 0 {
        t.Errorf("Expected success count to be 0, got %d", m.GetSuccessCount())
    }
    if m.GetFailureCount() != 1 {
        t.Errorf("Expected failure count to be 1, got %d", m.GetFailureCount())
    }
    if m.GetConsecutiveSuccess() != 0 {
        t.Errorf("Expected consecutive success to be 0, got %d", m.GetConsecutiveSuccess())
    }
    if m.GetConsecutiveFailure() != 1 {
        t.Errorf("Expected consecutive failure to be 1, got %d", m.GetConsecutiveFailure())
    }
}

func TestMetrics_GetFailureRate(t *testing.T) {
    m := src.NewMetrics()

    // 无请求时失败率为0
    if m.GetFailureRate() != 0 {
        t.Errorf("Expected failure rate to be 0, got %f", m.GetFailureRate())
    }

    // 记录4个成功，6个失败
    for i := 0; i < 4; i++ {
        m.RecordSuccess()
    }
    for i := 0; i < 6; i++ {
        m.RecordFailure()
    }

    expectedRate := 0.6
    if m.GetFailureRate() != expectedRate {
        t.Errorf("Expected failure rate to be %f, got %f", expectedRate, m.GetFailureRate())
    }
}

func TestMetrics_ConsecutiveCounters(t *testing.T) {
    m := src.NewMetrics()

    // 连续成功3次
    for i := 0; i < 3; i++ {
        m.RecordSuccess()
    }

    if m.GetConsecutiveSuccess() != 3 {
        t.Errorf("Expected consecutive success to be 3, got %d", m.GetConsecutiveSuccess())
    }
    if m.GetConsecutiveFailure() != 0 {
        t.Errorf("Expected consecutive failure to be 0, got %d", m.GetConsecutiveFailure())
    }

    // 失败一次，重置连续成功
    m.RecordFailure()

    if m.GetConsecutiveSuccess() != 0 {
        t.Errorf("Expected consecutive success to be 0, got %d", m.GetConsecutiveSuccess())
    }
    if m.GetConsecutiveFailure() != 1 {
        t.Errorf("Expected consecutive failure to be 1, got %d", m.GetConsecutiveFailure())
    }
}

func TestMetrics_Reset(t *testing.T) {
    m := src.NewMetrics()

    m.RecordSuccess()
    m.RecordFailure()
    m.RecordSuccess()

    m.Reset()

    if m.GetTotalRequests() != 0 {
        t.Errorf("Expected total requests to be 0, got %d", m.GetTotalRequests())
    }
    if m.GetSuccessCount() != 0 {
        t.Errorf("Expected success count to be 0, got %d", m.GetSuccessCount())
    }
    if m.GetFailureCount() != 0 {
        t.Errorf("Expected failure count to be 0, got %d", m.GetFailureCount())
    }
    if m.GetConsecutiveSuccess() != 0 {
        t.Errorf("Expected consecutive success to be 0, got %d", m.GetConsecutiveSuccess())
    }
    if m.GetConsecutiveFailure() != 0 {
        t.Errorf("Expected consecutive failure to be 0, got %d", m.GetConsecutiveFailure())
    }
}
