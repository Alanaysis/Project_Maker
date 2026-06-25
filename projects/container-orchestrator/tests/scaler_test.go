package tests

import (
	"testing"
	"time"

	"github.com/container-orchestrator/pkg/scaler"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewScaler(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)
	assert.NotNil(t, s)
}

func TestRegisterUnregisterService(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas: 1,
		MaxReplicas: 10,
	})

	// Get service state
	state, err := s.GetServiceState("service-1")
	assert.NoError(t, err)
	assert.Equal(t, 3, state.CurrentReplicas)

	// Unregister service
	s.UnregisterService("service-1")

	// Get service state should fail
	_, err = s.GetServiceState("service-1")
	assert.ErrorIs(t, err, scaler.ErrServiceNotFound)
}

func TestGetAllServiceStates(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register services
	s.RegisterService("service-1", 3, nil)
	s.RegisterService("service-2", 5, nil)

	// Get all states
	states := s.GetAllServiceStates()
	assert.Len(t, states, 2)
}

func TestManualScale(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas: 1,
		MaxReplicas: 10,
	})

	// Scale up
	err := s.ManualScale("service-1", 5)
	assert.NoError(t, err)

	// Check state
	state, err := s.GetServiceState("service-1")
	assert.NoError(t, err)
	assert.Equal(t, 5, state.CurrentReplicas)

	// Scale down
	err = s.ManualScale("service-1", 2)
	assert.NoError(t, err)

	// Check state
	state, err = s.GetServiceState("service-1")
	assert.NoError(t, err)
	assert.Equal(t, 2, state.CurrentReplicas)
}

func TestManualScaleLimits(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service with limits
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas: 2,
		MaxReplicas: 5,
	})

	// Try to scale below min
	err := s.ManualScale("service-1", 1)
	assert.NoError(t, err)

	state, err := s.GetServiceState("service-1")
	assert.NoError(t, err)
	assert.Equal(t, 2, state.CurrentReplicas) // Should be clamped to min

	// Try to scale above max
	err = s.ManualScale("service-1", 10)
	assert.NoError(t, err)

	state, err = s.GetServiceState("service-1")
	assert.NoError(t, err)
	assert.Equal(t, 5, state.CurrentReplicas) // Should be clamped to max
}

func TestEvaluate(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        0, // No cooldown for test
	})

	// Update metrics to trigger scale up
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.9,
		MemoryUsage: 0.5,
		Timestamp:   time.Now(),
	})

	// Evaluate
	decisions := s.Evaluate()
	assert.Len(t, decisions, 1)
	assert.Equal(t, scaler.ScaleUp, decisions[0].Direction)
	assert.Equal(t, 4, decisions[0].DesiredReplicas)
}

func TestEvaluateScaleDown(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        0,
	})

	// Update metrics to trigger scale down
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.1,
		MemoryUsage: 0.1,
		Timestamp:   time.Now(),
	})

	// Evaluate
	decisions := s.Evaluate()
	assert.Len(t, decisions, 1)
	assert.Equal(t, scaler.ScaleDown, decisions[0].Direction)
	assert.Equal(t, 2, decisions[0].DesiredReplicas)
}

func TestCooldown(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service with cooldown
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        1 * time.Hour,
	})

	// Update metrics to trigger scale up
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.9,
		MemoryUsage: 0.5,
		Timestamp:   time.Now(),
	})

	// First evaluation should trigger scale
	decisions := s.Evaluate()
	assert.Len(t, decisions, 1)

	// Perform scaling
	err := s.Scale("service-1", decisions[0].DesiredReplicas)
	require.NoError(t, err)

	// Second evaluation should not trigger scale due to cooldown
	decisions = s.Evaluate()
	assert.Len(t, decisions, 0)
}

func TestMetricsCollector(t *testing.T) {
	mc := scaler.NewMetricsCollector()

	// Update metrics
	mc.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.5,
		MemoryUsage: 0.6,
		Timestamp:   time.Now(),
	})

	// Get metrics
	metrics, ok := mc.GetMetrics("service-1")
	assert.True(t, ok)
	assert.Equal(t, 0.5, metrics.CPUUsage)
	assert.Equal(t, 0.6, metrics.MemoryUsage)

	// Get non-existent metrics
	_, ok = mc.GetMetrics("service-2")
	assert.False(t, ok)
}

func TestCustomMetrics(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service with custom metric rules
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        0,
		CustomMetricRules: []scaler.CustomMetricRule{
			{
				MetricName:       "requests_per_second",
				ScaleUpThreshold: 1000,
				ScaleDownThreshold: 100,
			},
		},
	})

	// Update metrics with custom metric above threshold
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.3,
		MemoryUsage: 0.3,
		CustomMetrics: map[string]float64{
			"requests_per_second": 1500,
		},
		Timestamp: time.Now(),
	})

	// Evaluate - should trigger scale up due to custom metric
	decisions := s.Evaluate()
	assert.Len(t, decisions, 1)
	assert.Equal(t, scaler.ScaleUp, decisions[0].Direction)
	assert.Contains(t, decisions[0].Reason, "requests_per_second")
}

func TestCustomMetricsScaleDown(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service with custom metric rules
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        0,
		CustomMetricRules: []scaler.CustomMetricRule{
			{
				MetricName:       "requests_per_second",
				ScaleUpThreshold: 1000,
				ScaleDownThreshold: 100,
			},
		},
	})

	// Update metrics with all metrics low
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.1,
		MemoryUsage: 0.1,
		CustomMetrics: map[string]float64{
			"requests_per_second": 50,
		},
		Timestamp: time.Now(),
	})

	// Evaluate - should trigger scale down
	decisions := s.Evaluate()
	assert.Len(t, decisions, 1)
	assert.Equal(t, scaler.ScaleDown, decisions[0].Direction)
}

func TestCustomMetricsNoScale(t *testing.T) {
	scaleFunc := func(serviceID string, desiredReplicas int) error {
		return nil
	}

	s := scaler.NewScaler(scaleFunc)

	// Register service with custom metric rules
	s.RegisterService("service-1", 3, &scaler.ScalingPolicy{
		MinReplicas:     1,
		MaxReplicas:     10,
		ScaleUpCPU:      0.8,
		ScaleDownCPU:    0.2,
		ScaleUpMemory:   0.8,
		ScaleDownMemory: 0.2,
		Cooldown:        0,
		CustomMetricRules: []scaler.CustomMetricRule{
			{
				MetricName:       "requests_per_second",
				ScaleUpThreshold: 1000,
				ScaleDownThreshold: 100,
			},
		},
	})

	// Update metrics - CPU low but custom metric above scale-down threshold
	s.UpdateMetrics("service-1", &scaler.ServiceMetrics{
		CPUUsage:    0.1,
		MemoryUsage: 0.1,
		CustomMetrics: map[string]float64{
			"requests_per_second": 500, // Above scale-down threshold
		},
		Timestamp: time.Now(),
	})

	// Evaluate - should not trigger scale down
	decisions := s.Evaluate()
	assert.Len(t, decisions, 0)
}
