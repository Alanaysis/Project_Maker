package test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/yourusername/device-management/internal/device"
	"github.com/yourusername/device-management/internal/group"
	"github.com/yourusername/device-management/internal/handler"
)

func setupTestServer() (*httptest.Server, *handler.Handler) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)
	h := handler.NewHandler(dm, gm)
	mux := h.SetupRoutes()
	server := httptest.NewServer(mux)
	return server, h
}

func TestAPIRegisterDevice(t *testing.T) {
	server, _ := setupTestServer()
	defer server.Close()

	// 测试注册设备
	reqBody := handler.RegisterRequest{
		Name: "测试传感器",
		Type: "sensor",
		Metadata: map[string]string{
			"location": "office",
		},
	}

	body, _ := json.Marshal(reqBody)
	resp, err := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
	}

	var result handler.Response
	json.NewDecoder(resp.Body).Decode(&result)

	if result.Code != 0 {
		t.Errorf("响应代码错误: got %d, want %d", result.Code, 0)
	}
}

func TestAPIListDevices(t *testing.T) {
	server, _ := setupTestServer()
	defer server.Close()

	// 先注册一个设备
	reqBody := handler.RegisterRequest{
		Name: "测试设备",
		Type: "sensor",
	}
	body, _ := json.Marshal(reqBody)
	http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))

	// 测试列出设备
	resp, err := http.Get(server.URL + "/api/device/list")
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
	}

	var result handler.Response
	json.NewDecoder(resp.Body).Decode(&result)

	if result.Code != 0 {
		t.Errorf("响应代码错误: got %d, want %d", result.Code, 0)
	}
}

func TestAPISendCommand(t *testing.T) {
	server, _ := setupTestServer()
	defer server.Close()

	// 先注册一个设备
	reqBody := handler.RegisterRequest{
		Name: "可控设备",
		Type: "actuator",
	}
	body, _ := json.Marshal(reqBody)
	resp, _ := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(body))

	var regResult handler.Response
	json.NewDecoder(resp.Body).Decode(&regResult)
	resp.Body.Close()

	// 从响应中获取设备ID
	data, _ := json.Marshal(regResult.Data)
	var dev device.Device
	json.Unmarshal(data, &dev)

	// 测试发送命令
	cmdReq := handler.CommandRequest{
		DeviceID: dev.ID,
		Command:  "turn_on",
		Params:   map[string]string{"brightness": "100"},
	}
	cmdBody, _ := json.Marshal(cmdReq)
	resp, err := http.Post(server.URL+"/api/device/command", "application/json", bytes.NewBuffer(cmdBody))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
	}
}

func TestAPICreateGroup(t *testing.T) {
	server, _ := setupTestServer()
	defer server.Close()

	// 测试创建分组
	reqBody := handler.GroupRequest{
		Name:        "测试分组",
		Description: "测试描述",
	}
	body, _ := json.Marshal(reqBody)
	resp, err := http.Post(server.URL+"/api/group/create", "application/json", bytes.NewBuffer(body))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
	}

	var result handler.Response
	json.NewDecoder(resp.Body).Decode(&result)

	if result.Code != 0 {
		t.Errorf("响应代码错误: got %d, want %d", result.Code, 0)
	}
}

func TestAPIAddDeviceToGroup(t *testing.T) {
	server, _ := setupTestServer()
	defer server.Close()

	// 先注册设备
	regReq := handler.RegisterRequest{
		Name: "传感器",
		Type: "sensor",
	}
	regBody, _ := json.Marshal(regReq)
	resp, _ := http.Post(server.URL+"/api/device/register", "application/json", bytes.NewBuffer(regBody))
	var regResult handler.Response
	json.NewDecoder(resp.Body).Decode(&regResult)
	resp.Body.Close()
	data, _ := json.Marshal(regResult.Data)
	var dev device.Device
	json.Unmarshal(data, &dev)

	// 创建分组
	grpReq := handler.GroupRequest{
		Name:        "测试组",
		Description: "测试",
	}
	grpBody, _ := json.Marshal(grpReq)
	resp, _ = http.Post(server.URL+"/api/group/create", "application/json", bytes.NewBuffer(grpBody))
	var grpResult handler.Response
	json.NewDecoder(resp.Body).Decode(&grpResult)
	resp.Body.Close()
	grpData, _ := json.Marshal(grpResult.Data)
	var grp group.Group
	json.Unmarshal(grpData, &grp)

	// 添加设备到分组
	addReq := handler.GroupDeviceRequest{
		DeviceID: dev.ID,
	}
	addBody, _ := json.Marshal(addReq)
	resp, err := http.Post(server.URL+"/api/group/add-device?group_id="+grp.ID, "application/json", bytes.NewBuffer(addBody))
	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		t.Errorf("状态码错误: got %d, want %d", resp.StatusCode, http.StatusOK)
	}
}
