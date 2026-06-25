package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

// Server HTTP API 服务器
type Server struct {
	mu            sync.RWMutex
	addr          string
	db            storage.TimeSeriesDB
	queryEngine   *storage.QueryEngine
	collectorMgr  *collector.CollectorManager
	evaluator     *alert.RuleEvaluator
	trendEval     *alert.TrendEvaluator
	compositeEval *alert.CompositeEvaluator
	alertMgr      *alert.AlertManager
	server        *http.Server
}

// NewServer 创建 HTTP API 服务器
func NewServer(addr string, db storage.TimeSeriesDB, collectorMgr *collector.CollectorManager, evaluator *alert.RuleEvaluator, trendEval *alert.TrendEvaluator, compositeEval *alert.CompositeEvaluator, alertMgr *alert.AlertManager) *Server {
	s := &Server{
		addr:          addr,
		db:            db,
		queryEngine:   storage.NewQueryEngine(db),
		collectorMgr:  collectorMgr,
		evaluator:     evaluator,
		trendEval:     trendEval,
		compositeEval: compositeEval,
		alertMgr:      alertMgr,
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/api/v1/metrics", s.handleMetrics)
	mux.HandleFunc("/api/v1/metrics/query", s.handleMetricsQuery)
	mux.HandleFunc("/api/v1/metrics/aggregate", s.handleMetricsAggregate)
	mux.HandleFunc("/api/v1/alerts", s.handleAlerts)
	mux.HandleFunc("/api/v1/alerts/rules", s.handleAlertRules)
	mux.HandleFunc("/api/v1/alerts/trend-rules", s.handleTrendRules)
	mux.HandleFunc("/api/v1/alerts/composite-rules", s.handleCompositeRules)
	mux.HandleFunc("/api/v1/collectors", s.handleCollectors)
	mux.HandleFunc("/api/v1/health", s.handleHealth)

	s.server = &http.Server{
		Addr:    addr,
		Handler: mux,
	}

	return s
}

// Start 启动服务器
func (s *Server) Start() error {
	go func() {
		if err := s.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("HTTP server error: %v\n", err)
		}
	}()
	return nil
}

// Stop 停止服务器
func (s *Server) Stop() error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	return s.server.Shutdown(ctx)
}

// APIResponse API 响应
type APIResponse struct {
	Success bool        `json:"success"`
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
}

// writeJSON 写入 JSON 响应
func writeJSON(w http.ResponseWriter, status int, resp APIResponse) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(resp)
}

// handleMetrics 处理指标列表请求
func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	metrics := s.db.List()
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: metrics})
}

// handleMetricsQuery 处理指标查询请求
func (s *Server) handleMetricsQuery(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	metric := r.URL.Query().Get("metric")
	if metric == "" {
		writeJSON(w, http.StatusBadRequest, APIResponse{Error: "metric parameter is required"})
		return
	}

	durationStr := r.URL.Query().Get("duration")
	duration := 5 * time.Minute
	if durationStr != "" {
		var err error
		duration, err = time.ParseDuration(durationStr)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, APIResponse{Error: "invalid duration format"})
			return
		}
	}

	results, err := s.queryEngine.SimpleQuery(metric, duration)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, APIResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: results})
}

// handleMetricsAggregate 处理指标聚合请求
func (s *Server) handleMetricsAggregate(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	metric := r.URL.Query().Get("metric")
	if metric == "" {
		writeJSON(w, http.StatusBadRequest, APIResponse{Error: "metric parameter is required"})
		return
	}

	durationStr := r.URL.Query().Get("duration")
	duration := 5 * time.Minute
	if durationStr != "" {
		var err error
		duration, err = time.ParseDuration(durationStr)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, APIResponse{Error: "invalid duration format"})
			return
		}
	}

	aggregation := r.URL.Query().Get("aggregation")
	if aggregation == "" {
		aggregation = "avg"
	}

	result, err := s.queryEngine.AggregateQuery(metric, duration, aggregation)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, APIResponse{Error: err.Error()})
		return
	}

	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: map[string]interface{}{
		"metric":      metric,
		"duration":    duration.String(),
		"aggregation": aggregation,
		"value":       result,
	}})
}

// handleAlerts 处理告警列表请求
func (s *Server) handleAlerts(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	activeAlerts := s.alertMgr.GetActiveAlerts()
	history := s.alertMgr.GetHistory()

	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Data: map[string]interface{}{
			"active":  activeAlerts,
			"history": history,
		},
	})
}

// handleAlertRules 处理告警规则请求
func (s *Server) handleAlertRules(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		rules := s.evaluator.ListRules()
		writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: rules})
	case http.MethodPost:
		var rule model.AlertRule
		if err := json.NewDecoder(r.Body).Decode(&rule); err != nil {
			writeJSON(w, http.StatusBadRequest, APIResponse{Error: "invalid request body"})
			return
		}
		if err := s.evaluator.AddRule(&rule); err != nil {
			writeJSON(w, http.StatusInternalServerError, APIResponse{Error: err.Error()})
			return
		}
		writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: rule})
	default:
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
	}
}

// handleTrendRules 处理趋势规则请求
func (s *Server) handleTrendRules(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		rules := s.trendEval.ListRules()
		writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: rules})
	case http.MethodPost:
		var rule alert.TrendRule
		if err := json.NewDecoder(r.Body).Decode(&rule); err != nil {
			writeJSON(w, http.StatusBadRequest, APIResponse{Error: "invalid request body"})
			return
		}
		s.trendEval.AddRule(&rule)
		writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: rule})
	default:
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
	}
}

// handleCompositeRules 处理组合规则请求
func (s *Server) handleCompositeRules(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		rules := s.compositeEval.ListRules()
		writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: rules})
	case http.MethodPost:
		var rule alert.CompositeRule
		if err := json.NewDecoder(r.Body).Decode(&rule); err != nil {
			writeJSON(w, http.StatusBadRequest, APIResponse{Error: "invalid request body"})
			return
		}
		if err := s.compositeEval.AddRule(&rule); err != nil {
			writeJSON(w, http.StatusInternalServerError, APIResponse{Error: err.Error()})
			return
		}
		writeJSON(w, http.StatusCreated, APIResponse{Success: true, Data: rule})
	default:
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
	}
}

// handleCollectors 处理采集器列表请求
func (s *Server) handleCollectors(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	collectors := s.collectorMgr.ListCollectors()
	writeJSON(w, http.StatusOK, APIResponse{Success: true, Data: collectors})
}

// handleHealth 处理健康检查请求
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, APIResponse{Error: "method not allowed"})
		return
	}

	writeJSON(w, http.StatusOK, APIResponse{
		Success: true,
		Data: map[string]interface{}{
			"status":    "healthy",
			"timestamp": time.Now().Format(time.RFC3339),
			"metrics":   s.db.GetPointCount(),
			"series":    s.db.GetSeriesCount(),
		},
	})
}
