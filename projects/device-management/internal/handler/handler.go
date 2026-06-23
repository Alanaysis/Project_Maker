package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/yourusername/device-management/internal/device"
	"github.com/yourusername/device-management/internal/group"
)

// Handler 请求处理器
type Handler struct {
	dm *device.DeviceManager
	gm *group.GroupManager
}

// NewHandler 创建处理器
func NewHandler(dm *device.DeviceManager, gm *group.GroupManager) *Handler {
	return &Handler{
		dm: dm,
		gm: gm,
	}
}

// RegisterRequest 设备注册请求
type RegisterRequest struct {
	Name     string            `json:"name"`
	Type     string            `json:"type"`
	Metadata map[string]string `json:"metadata,omitempty"`
}

// StatusUpdateRequest 状态更新请求
type StatusUpdateRequest struct {
	Battery  int    `json:"battery"`
	Signal   int    `json:"signal"`
	Firmware string `json:"firmware"`
	IP       string `json:"ip_address"`
}

// CommandRequest 控制命令请求
type CommandRequest struct {
	DeviceID string            `json:"device_id"`
	Command  string            `json:"command"`
	Params   map[string]string `json:"params,omitempty"`
}

// GroupRequest 创建分组请求
type GroupRequest struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}

// GroupDeviceRequest 分组设备操作请求
type GroupDeviceRequest struct {
	DeviceID string `json:"device_id"`
}

// Response 通用响应
type Response struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data,omitempty"`
}

// RegisterDevice 注册设备
func (h *Handler) RegisterDevice(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if req.Name == "" || req.Type == "" {
		h.writeError(w, http.StatusBadRequest, "Name and type are required")
		return
	}

	device, err := h.dm.RegisterDevice(req.Name, req.Type, req.Metadata)
	if err != nil {
		h.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	h.writeSuccess(w, "设备注册成功", device)
}

// GetDevice 获取设备信息
func (h *Handler) GetDevice(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	deviceID := r.URL.Query().Get("id")
	if deviceID == "" {
		h.writeError(w, http.StatusBadRequest, "Device ID is required")
		return
	}

	device, err := h.dm.GetDevice(deviceID)
	if err != nil {
		h.writeError(w, http.StatusNotFound, err.Error())
		return
	}

	h.writeSuccess(w, "Success", device)
}

// ListDevices 列出所有设备
func (h *Handler) ListDevices(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	devices := h.dm.ListDevices()
	h.writeSuccess(w, "Success", devices)
}

// UpdateStatus 更新设备状态
func (h *Handler) UpdateStatus(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	deviceID := r.URL.Query().Get("id")
	if deviceID == "" {
		h.writeError(w, http.StatusBadRequest, "Device ID is required")
		return
	}

	var req StatusUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	err := h.dm.UpdateDeviceStatus(deviceID, req.Battery, req.Signal, req.Firmware, req.IP)
	if err != nil {
		h.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	h.writeSuccess(w, "状态更新成功", nil)
}

// SendCommand 发送控制命令
func (h *Handler) SendCommand(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req CommandRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if req.DeviceID == "" || req.Command == "" {
		h.writeError(w, http.StatusBadRequest, "Device ID and command are required")
		return
	}

	// 获取设备信息
	dev, err := h.dm.GetDevice(req.DeviceID)
	if err != nil {
		h.writeError(w, http.StatusNotFound, err.Error())
		return
	}

	// 检查设备是否在线
	if dev.Status != device.StatusOnline {
		h.writeError(w, http.StatusBadRequest, "设备离线，无法发送命令")
		return
	}

	// 模拟命令执行
	result := map[string]interface{}{
		"device_id": req.DeviceID,
		"command":   req.Command,
		"params":    req.Params,
		"status":    "executed",
		"time":      time.Now().Format(time.RFC3339),
	}

	h.writeSuccess(w, "命令发送成功", result)
}

// DeleteDevice 删除设备
func (h *Handler) DeleteDevice(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	deviceID := r.URL.Query().Get("id")
	if deviceID == "" {
		h.writeError(w, http.StatusBadRequest, "Device ID is required")
		return
	}

	err := h.dm.DeleteDevice(deviceID)
	if err != nil {
		h.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	h.writeSuccess(w, "设备删除成功", nil)
}

// CreateGroup 创建分组
func (h *Handler) CreateGroup(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	var req GroupRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	if req.Name == "" {
		h.writeError(w, http.StatusBadRequest, "Name is required")
		return
	}

	group, err := h.gm.CreateGroup(req.Name, req.Description)
	if err != nil {
		h.writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	h.writeSuccess(w, "分组创建成功", group)
}

// ListGroups 列出所有分组
func (h *Handler) ListGroups(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	groups := h.gm.ListGroups()
	h.writeSuccess(w, "Success", groups)
}

// AddDeviceToGroup 添加设备到分组
func (h *Handler) AddDeviceToGroup(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	groupID := r.URL.Query().Get("group_id")
	if groupID == "" {
		h.writeError(w, http.StatusBadRequest, "Group ID is required")
		return
	}

	var req GroupDeviceRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.writeError(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	err := h.gm.AddDeviceToGroup(groupID, req.DeviceID)
	if err != nil {
		h.writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	h.writeSuccess(w, "设备添加到分组成功", nil)
}

// RemoveDeviceFromGroup 从分组移除设备
func (h *Handler) RemoveDeviceFromGroup(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	groupID := r.URL.Query().Get("group_id")
	deviceID := r.URL.Query().Get("device_id")
	if groupID == "" || deviceID == "" {
		h.writeError(w, http.StatusBadRequest, "Group ID and Device ID are required")
		return
	}

	err := h.gm.RemoveDeviceFromGroup(groupID, deviceID)
	if err != nil {
		h.writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	h.writeSuccess(w, "设备从分组移除成功", nil)
}

// GetGroupDevices 获取分组内的设备
func (h *Handler) GetGroupDevices(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		h.writeError(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	groupID := r.URL.Query().Get("group_id")
	if groupID == "" {
		h.writeError(w, http.StatusBadRequest, "Group ID is required")
		return
	}

	devices, err := h.gm.GetGroupDevices(groupID)
	if err != nil {
		h.writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	h.writeSuccess(w, "Success", devices)
}

// writeSuccess 写入成功响应
func (h *Handler) writeSuccess(w http.ResponseWriter, message string, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(Response{
		Code:    0,
		Message: message,
		Data:    data,
	})
}

// writeError 写入错误响应
func (h *Handler) writeError(w http.ResponseWriter, statusCode int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	json.NewEncoder(w).Encode(Response{
		Code:    -1,
		Message: message,
	})
}

// SetupRoutes 设置路由
func (h *Handler) SetupRoutes() *http.ServeMux {
	mux := http.NewServeMux()

	// 设备管理接口
	mux.HandleFunc("/api/device/register", h.RegisterDevice)
	mux.HandleFunc("/api/device/get", h.GetDevice)
	mux.HandleFunc("/api/device/list", h.ListDevices)
	mux.HandleFunc("/api/device/status", h.UpdateStatus)
	mux.HandleFunc("/api/device/command", h.SendCommand)
	mux.HandleFunc("/api/device/delete", h.DeleteDevice)

	// 分组管理接口
	mux.HandleFunc("/api/group/create", h.CreateGroup)
	mux.HandleFunc("/api/group/list", h.ListGroups)
	mux.HandleFunc("/api/group/add-device", h.AddDeviceToGroup)
	mux.HandleFunc("/api/group/remove-device", h.RemoveDeviceFromGroup)
	mux.HandleFunc("/api/group/devices", h.GetGroupDevices)

	return mux
}
