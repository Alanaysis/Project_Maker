package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/simple-rpc/examples"
	"github.com/simple-rpc/internal/codec"
	"github.com/simple-rpc/internal/registry"
	"github.com/simple-rpc/internal/server"
)

func main() {
	// 命令行参数
	addr := flag.String("addr", "localhost:8080", "server address")
	serviceName := flag.String("service", "Calculator", "service name (Calculator or UserService)")
	flag.Parse()

	// 创建注册中心
	reg := registry.NewMemoryRegistry()

	// 创建编解码器
	c := codec.NewJSONCodec()

	// 创建服务器
	srv := server.NewServer(*addr, c, reg)

	// 注册服务
	switch *serviceName {
	case "Calculator":
		if err := srv.Register(&examples.Calculator{}); err != nil {
			log.Fatalf("Failed to register Calculator service: %v", err)
		}
		log.Println("Registered Calculator service")
	case "UserService":
		if err := srv.Register(&examples.UserService{}); err != nil {
			log.Fatalf("Failed to register UserService: %v", err)
		}
		log.Println("Registered UserService")
	default:
		log.Fatalf("Unknown service: %s", *serviceName)
	}

	// 优雅关闭
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigCh
		fmt.Println("\nShutting down server...")
		if err := srv.Stop(); err != nil {
			log.Printf("Failed to stop server: %v", err)
		}
		os.Exit(0)
	}()

	// 启动服务器
	log.Printf("Starting server on %s", *addr)
	if err := srv.Start(*addr); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
