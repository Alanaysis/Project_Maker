package tsdb

import (
	"fmt"
	"time"
)

// SeriesManager manages time series lifecycle operations.
type SeriesManager struct {
	storage *Storage
}

// NewSeriesManager creates a new series manager.
func NewSeriesManager(s *Storage) *SeriesManager {
	return &SeriesManager{storage: s}
}

// RegisterSeries creates a new time series with the given name and tags.
func (m *SeriesManager) RegisterSeries(id, name string) {
	m.storage.CreateSeries(id, name)
}

// GetSeries returns a series by ID.
func (m *SeriesManager) GetSeries(id string) (*Series, error) {
	ser, ok := m.storage.series[id]
	if !ok {
		return nil, fmt.Errorf("series %q not found", id)
	}
	return ser, nil
}

// ListSeries returns all series IDs.
func (m *SeriesManager) ListSeries() []string {
	m.storage.mu.RLock()
	defer m.storage.mu.RUnlock()
	ids := make([]string, 0, len(m.storage.series))
	for id := range m.storage.series {
		ids = append(ids, id)
	}
	return ids
}

// WriteBatch writes data points to multiple series atomically.
func (m *SeriesManager) WriteBatch(writes map[string][]Point) error {
	for id, points := range writes {
		if err := m.storage.WritePoints(id, points); err != nil {
			return fmt.Errorf("write to series %q failed: %w", id, err)
		}
	}
	return nil
}

// QueryAcrossSeries performs a time range query across multiple series.
func (m *SeriesManager) QueryAcrossSeries(ids []string, start, end time.Time) (map[string][]Point, error) {
	result := make(map[string][]Point)
	for _, id := range ids {
		points, err := m.storage.QueryRange(id, start, end)
		if err != nil {
			return nil, err
		}
		if len(points) > 0 {
			result[id] = points
		}
	}
	return result, nil
}
