package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/hpc-scheduler/internal/api"
	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/internal/resource"
	"github.com/hpc-scheduler/internal/scheduler"
	"github.com/hpc-scheduler/internal/task"
)

func main() {
	// 加载配置
	cfg := config.DefaultConfig()
	if envPort := os.Getenv("HPC_PORT"); envPort != "" {
		cfg.Server.Port = envPort
	}

	// 初始化资源管理器
	rm := resource.NewResourceManager(cfg.Resources)

	// 初始化任务管理器
	tm := task.NewTaskManager()

	// 初始化调度器
	sched := scheduler.NewScheduler(cfg.Scheduler, rm, tm)

	// 启动调度器
	sched.Start()
	log.Println("Scheduler started")

	// 初始化 HTTP API
	handler := api.NewHandler(sched, tm, rm)
	router := handler.SetupRoutes()

	// 启动 HTTP 服务器
	addr := fmt.Sprintf(":%s", cfg.Server.Port)
	log.Printf("Server starting on %s", addr)

	server := &http.Server{
		Addr:    addr,
		Handler: router,
	}

	// 优雅关闭
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		<-sigCh
		log.Println("Shutting down...")
		sched.Stop()
		server.Close()
	}()

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("Server error: %v", err)
	}
}
