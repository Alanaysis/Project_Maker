package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/yourusername/device-management/internal/device"
	"github.com/yourusername/device-management/internal/group"
	"github.com/yourusername/device-management/internal/handler"
)

func main() {
	// 初始化设备管理器
	dm := device.NewDeviceManager()

	// 初始化分组管理器
	gm := group.NewGroupManager(dm)

	// 初始化处理器
	h := handler.NewHandler(dm, gm)

	// 设置路由
	mux := h.SetupRoutes()

	// 启动事件监听
	go func() {
		eventChan := dm.GetEventChannel()
		for event := range eventChan {
			log.Printf("设备事件: %s - %s - %v", event.Type, event.DeviceID, event.Data)
		}
	}()

	// 启动HTTP服务器
	addr := ":8080"
	fmt.Printf("设备管理服务启动在 %s\n", addr)
	fmt.Println("API 端点:")
	fmt.Println("  POST   /api/device/register  - 注册设备")
	fmt.Println("  GET    /api/device/get        - 获取设备信息")
	fmt.Println("  GET    /api/device/list       - 列出所有设备")
	fmt.Println("  POST   /api/device/status     - 更新设备状态")
	fmt.Println("  POST   /api/device/command    - 发送控制命令")
	fmt.Println("  DELETE /api/device/delete     - 删除设备")
	fmt.Println("  POST   /api/group/create      - 创建分组")
	fmt.Println("  GET    /api/group/list        - 列出所有分组")
	fmt.Println("  POST   /api/group/add-device  - 添加设备到分组")
	fmt.Println("  DELETE /api/group/remove-device - 从分组移除设备")
	fmt.Println("  GET    /api/group/devices     - 获取分组设备")

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}
