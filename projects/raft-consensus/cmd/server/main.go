package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/raft-consensus/internal/raft"
)

func main() {
	// 解析命令行参数
	id := flag.Int64("id", 1, "Node ID")
	port := flag.Int("port", 50051, "Server port")
	peersStr := flag.String("peers", "", "Comma-separated list of peer addresses (host:port)")
	flag.Parse()

	// 构建对等节点映射
	peers := make(map[int64]string)
	if *peersStr != "" {
		peerList := strings.Split(*peersStr, ",")
		for i, addr := range peerList {
			addr = strings.TrimSpace(addr)
			if addr != "" {
				// 对等节点 ID 从 1 开始
				peerID := int64(i + 1)
				if peerID == *id {
					peerID = int64(len(peerList) + 1)
				}
				peers[peerID] = addr
			}
		}
	}

	// 添加自己到对等节点列表
	address := fmt.Sprintf("localhost:%d", *port)
	peers[*id] = address

	// 创建配置
	config := raft.Config{
		ID:                 *id,
		Address:            address,
		Peers:              peers,
		ElectionTimeoutMin: 150 * time.Millisecond,
		ElectionTimeoutMax: 300 * time.Millisecond,
		HeartbeatInterval:  50 * time.Millisecond,
	}

	// 创建并启动 Raft 节点
	node := raft.NewRaftNode(config)
	if err := node.Start(); err != nil {
		log.Fatalf("Failed to start node: %v", err)
	}

	log.Printf("Raft node %d started on %s", *id, address)
	log.Printf("Peers: %v", peers)

	// 等待中断信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	// 优雅关闭
	log.Printf("Shutting down node %d...", *id)
	node.Stop()
}