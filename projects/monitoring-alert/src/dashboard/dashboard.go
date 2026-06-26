package dashboard

import (
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/src/aggregation"
)

// 避免未使用的 import
var _ = model.MetricTypeCounter

// DashboardPanel 仪表盘面板
type DashboardPanel struct {
	ID       string                 `json:"id"`
	Title    string                 `json:"title"`
	Type     PanelType              `json:"type"`
	Metric   string                 `json:"metric"`
	Labels   map[string]string      `json:"labels"`
	AggType  aggregation.AggregationType `json:"aggregation"`
	Range    time.Duration          `json:"range"`
	Interval time.Duration          `json:"interval"`
	Thresholds *ThresholdConfig    `json:"thresholds,omitempty"`
}

// PanelType 面板类型
type PanelType string

const (
	// PanelTimeSeries 时序图
	PanelTimeSeries PanelType = "timeseries"
	// PanelGauge 仪表盘
	PanelGauge PanelType = "gauge"
	// PanelStat 统计值
	PanelStat PanelType = "stat"
	// PanelBarChart 柱状图
	PanelBarChart PanelType = "barchart"
	// PanelHeatmap 热力图
	PanelHeatmap PanelType = "heatmap"
)

// ThresholdConfig 阈值配置
type ThresholdConfig struct {
	Warning  float64 `json:"warning"`
	Critical float64 `json:"critical"`
}

// Dashboard 仪表盘
type Dashboard struct {
	ID       string         `json:"id"`
	Title    string         `json:"title"`
	Desc     string         `json:"desc"`
	Panels   []*DashboardPanel `json:"panels"`
	Refresh  time.Duration  `json:"refresh"`
	TimeRange time.Duration `json:"time_range"`
}

// NewDashboard 创建仪表盘
func NewDashboard(id, title, desc string) *Dashboard {
	return &Dashboard{
		ID:       id,
		Title:    title,
		Desc:     desc,
		Panels:   make([]*DashboardPanel, 0),
		Refresh:  30 * time.Second,
		TimeRange: 1 * time.Hour,
	}
}

// AddPanel 添加面板
func (d *Dashboard) AddPanel(panel *DashboardPanel) *Dashboard {
	d.Panels = append(d.Panels, panel)
	return d
}

// DashboardDataProvider 仪表盘数据提供者
type DashboardDataProvider struct {
	db    TimeSeriesDB
	agg   *aggregation.AggregationFunc
}

// TimeSeriesDB 时序数据库接口
type TimeSeriesDB interface {
	Read(metric string, labels map[string]string, start, end time.Time) (*model.TimeSeries, error)
	Query(query string) ([]*model.TimeSeries, error)
	List() []string
	GetLatest(metric string, labels map[string]string) (float64, bool)
}

// NewDashboardDataProvider 创建数据提供者
func NewDashboardDataProvider(db TimeSeriesDB) *DashboardDataProvider {
	return &DashboardDataProvider{
		db:  db,
		agg: aggregation.NewAggregationFunc(db),
	}
}

// GetDashboardData 获取仪表盘数据
func (p *DashboardDataProvider) GetDashboardData(dashboard *Dashboard) (*DashboardData, error) {
	data := &DashboardData{
		DashboardID: dashboard.ID,
		Title:       dashboard.Title,
		TimeRange:   dashboard.TimeRange,
		UpdatedAt:   time.Now(),
		PanelData:   make(map[string]*PanelData),
	}

	for _, panel := range dashboard.Panels {
		panelData, err := p.getPanelData(panel)
		if err != nil {
			panelData = &PanelData{
				Error:   err.Error(),
				Updated: time.Now(),
			}
		}
		data.PanelData[panel.ID] = panelData
	}

	return data, nil
}

// getPanelData 获取面板数据
func (p *DashboardDataProvider) getPanelData(panel *DashboardPanel) (*PanelData, error) {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	switch panel.Type {
	case PanelTimeSeries:
		data = p.getTimeseriesData(panel)
	case PanelGauge:
		data = p.getGaugeData(panel)
	case PanelStat:
		data = p.getStatData(panel)
	case PanelBarChart:
		data = p.getBarChartData(panel)
	case PanelHeatmap:
		data = p.getHeatmapData(panel)
	}

	data.Updated = time.Now()
	return data, nil
}

// getTimeseriesData 获取时序数据
func (p *DashboardDataProvider) getTimeseriesData(panel *DashboardPanel) *PanelData {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	end := time.Now()
	start := end.Add(-panel.Range)

	ts, err := p.db.Read(panel.Metric, panel.Labels, start, end)
	if err != nil {
		data.Error = err.Error()
		return data
	}

	points := ts.GetPoints()
	data.Points = make([]DataPoint, len(points))
	for i, p := range points {
		data.Points[i] = DataPoint{
			Timestamp: p.Timestamp,
			Value:     p.Value,
		}
	}

	// 计算聚合值
	if panel.AggType != "" {
		aggResult, err := p.agg.Aggregate(panel.Metric, panel.Labels, start, end, panel.AggType)
		if err == nil {
			data.Aggregation = aggResult
			data.CurrentValue = aggResult.Value
		}
	}

	// 检查阈值
	if panel.Thresholds != nil {
		if data.CurrentValue > panel.Thresholds.Critical {
			data.Status = "critical"
		} else if data.CurrentValue > panel.Thresholds.Warning {
			data.Status = "warning"
		} else {
			data.Status = "ok"
		}
	}

	return data
}

// getGaugeData 获取仪表盘数据
func (p *DashboardDataProvider) getGaugeData(panel *DashboardPanel) *PanelData {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	value, ok := p.db.GetLatest(panel.Metric, panel.Labels)
	if !ok {
		data.Error = "no data"
		return data
	}

	data.CurrentValue = value

	// 检查阈值
	if panel.Thresholds != nil {
		if value > panel.Thresholds.Critical {
			data.Status = "critical"
		} else if value > panel.Thresholds.Warning {
			data.Status = "warning"
		} else {
			data.Status = "ok"
		}
	}

	return data
}

// getStatData 获取统计值数据
func (p *DashboardDataProvider) getStatData(panel *DashboardPanel) *PanelData {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	end := time.Now()
	start := end.Add(-panel.Range)

	aggResult, err := p.agg.Aggregate(panel.Metric, panel.Labels, start, end, panel.AggType)
	if err != nil {
		data.Error = err.Error()
		return data
	}

	data.Aggregation = aggResult
	data.CurrentValue = aggResult.Value

	// 检查阈值
	if panel.Thresholds != nil {
		if aggResult.Value > panel.Thresholds.Critical {
			data.Status = "critical"
		} else if aggResult.Value > panel.Thresholds.Warning {
			data.Status = "warning"
		} else {
			data.Status = "ok"
		}
	}

	return data
}

// getBarChartData 获取柱状图数据
func (p *DashboardDataProvider) getBarChartData(panel *DashboardPanel) *PanelData {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	// 按时间区间分桶
	end := time.Now()
	start := end.Add(-panel.Range)

	if panel.Interval == 0 {
		panel.Interval = 5 * time.Minute
	}

	numBuckets := int(panel.Range / panel.Interval)
	if numBuckets <= 0 {
		numBuckets = 1
	}

	bucketSize := panel.Range / time.Duration(numBuckets)
	buckets := make([]BucketData, numBuckets)

	for i := 0; i < numBuckets; i++ {
		bucketStart := start.Add(time.Duration(i) * bucketSize)
		bucketEnd := bucketStart.Add(bucketSize)

		ts, err := p.db.Read(panel.Metric, panel.Labels, bucketStart, bucketEnd)
		if err != nil {
			continue
		}

		points := ts.GetPoints()
		if len(points) == 0 {
			continue
		}

		sum := 0.0
		for _, p := range points {
			sum += p.Value
		}
		avg := sum / float64(len(points))

		buckets[i] = BucketData{
			Start:     bucketStart,
			End:       bucketEnd,
			Value:     avg,
			Count:     len(points),
			Min:       points[0].Value,
			Max:       points[0].Value,
		}

		for _, p := range points {
			if p.Value < buckets[i].Min {
				buckets[i].Min = p.Value
			}
			if p.Value > buckets[i].Max {
				buckets[i].Max = p.Value
			}
		}
	}

	data.Buckets = buckets
	return data
}

// getHeatmapData 获取热力图数据
func (p *DashboardDataProvider) getHeatmapData(panel *DashboardPanel) *PanelData {
	data := &PanelData{
		PanelID: panel.ID,
		Title:   panel.Title,
		Type:    panel.Type,
	}

	// 获取所有相关指标
	tsList, err := p.db.Query(panel.Metric)
	if err != nil || len(tsList) == 0 {
		data.Error = "no data found"
		return data
	}

	// 按标签分组统计
	groups := make(map[string]*GroupStats)
	for _, ts := range tsList {
		labels := ts.Labels
		key := labelsToString(labels)

		g, exists := groups[key]
		if !exists {
			g = &GroupStats{Labels: labels}
			groups[key] = g
		}

		points := ts.GetPoints()
		for _, p := range points {
			g.Count++
			g.Sum += p.Value
			if g.Count == 1 || p.Value < g.Min {
				g.Min = p.Value
			}
			if g.Count == 1 || p.Value > g.Max {
				g.Max = p.Value
			}
			g.Values = append(g.Values, p.Value)
		}
	}

	// 计算统计信息
	for _, g := range groups {
		if g.Count > 0 {
			g.Avg = g.Sum / float64(g.Count)
		}
	}

	data.Groups = groups
	return data
}

// GroupStats 分组统计
type GroupStats struct {
	Labels map[string]string `json:"labels"`
	Count  int               `json:"count"`
	Sum    float64           `json:"sum"`
	Avg    float64           `json:"avg"`
	Min    float64           `json:"min"`
	Max    float64           `json:"max"`
	Values []float64         `json:"-"`
}

// PanelData 面板数据
type PanelData struct {
	PanelID       string                        `json:"panel_id"`
	Title         string                        `json:"title"`
	Type          PanelType                     `json:"type"`
	CurrentValue  float64                       `json:"current_value,omitempty"`
	Points        []DataPoint                   `json:"points,omitempty"`
	Buckets       []BucketData                  `json:"buckets,omitempty"`
	Groups        map[string]*GroupStats        `json:"groups,omitempty"`
	Aggregation   *aggregation.AggregationResult `json:"aggregation,omitempty"`
	Status        string                        `json:"status,omitempty"`
	Error         string                        `json:"error,omitempty"`
	Updated       time.Time                     `json:"updated"`
}

// DataPoint 数据点
type DataPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

// BucketData 桶数据
type BucketData struct {
	Start time.Time `json:"start"`
	End   time.Time `json:"end"`
	Value float64   `json:"value"`
	Count int       `json:"count"`
	Min   float64   `json:"min"`
	Max   float64   `json:"max"`
}

// DashboardData 仪表盘数据
type DashboardData struct {
	DashboardID string                    `json:"dashboard_id"`
	Title       string                    `json:"title"`
	TimeRange   time.Duration             `json:"time_range"`
	UpdatedAt   time.Time                 `json:"updated_at"`
	PanelData   map[string]*PanelData     `json:"panel_data"`
}

// 辅助函数
func labelsToString(labels map[string]string) string {
	if len(labels) == 0 {
		return "{}"
	}
	parts := make([]string, 0, len(labels))
	for k, v := range labels {
		parts = append(parts, k+"="+v)
	}
	return "{" + joinStrings(parts, ",") + "}"
}

func joinStrings(parts []string, sep string) string {
	if len(parts) == 0 {
		return ""
	}
	result := parts[0]
	for _, p := range parts[1:] {
		result += sep + p
	}
	return result
}
