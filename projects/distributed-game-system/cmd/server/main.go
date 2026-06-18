package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/distributed-game-system/internal/game"
	"github.com/distributed-game-system/internal/network"
	"github.com/distributed-game-system/internal/sync"
	"github.com/distributed-game-system/pkg/config"
	"github.com/distributed-game-system/pkg/logger"
)

func main() {
	// 解析命令行参数
	port := flag.Int("port", 8080, "UDP port")
	configFile := flag.String("config", "", "Config file path")
	flag.Parse()

	// 加载配置
	var cfg *config.ServerConfig
	if *configFile != "" {
		var err error
		cfg, err = config.LoadConfig(*configFile)
		if err != nil {
			logger.Fatalf("Failed to load config: %v", err)
		}
	} else {
		cfg = config.DefaultConfig()
		cfg.Server.UDPPort = *port
	}

	// 创建游戏世界
	world := game.NewWorld(cfg.Game.WorldWidth, cfg.Game.WorldHeight)

	// 创建快照管理器
	snapshotMgr := sync.NewSnapshotManager(100)

	// 创建 UDP 服务器
	addr := fmt.Sprintf("%s:%d", cfg.Server.Host, cfg.Server.UDPPort)
	udpServer := network.NewUDPServer(network.UDPServerConfig{
		Addr:        addr,
		MaxSessions: cfg.Server.MaxPlayers,
	})

	// 设置回调
	udpServer.SetOnConnect(func(session *network.Session) {
		handleConnect(session, world, udpServer)
	})

	udpServer.SetOnDisconnect(func(session *network.Session) {
		handleDisconnect(session, world)
	})

	// 启动服务器
	if err := udpServer.Start(); err != nil {
		logger.Fatalf("Failed to start server: %v", err)
	}
	defer udpServer.Stop()

	logger.Infof("Game server started on %s", addr)
	logger.Infof("Max players: %d", cfg.Server.MaxPlayers)
	logger.Infof("World size: %.0fx%.0f", cfg.Game.WorldWidth, cfg.Game.WorldHeight)

	// 启动游戏循环
	go gameLoop(world, snapshotMgr, udpServer, cfg)

	// 启动状态同步
	go syncLoop(world, snapshotMgr, udpServer, cfg)

	// 等待退出信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	logger.Info("Shutting down...")
}

// handleConnect 处理玩家连接
func handleConnect(session *network.Session, world *game.World, server *network.UDPServer) {
	// 分配玩家 ID
	playerID := uint32(world.GetPlayerCount() + 1)

	// 获取出生位置
	spawnPos := game.GetSpawnPosition(world.GetPlayerCount())

	// 创建玩家
	player := game.NewPlayer(playerID, fmt.Sprintf("Player%d", playerID), spawnPos)

	// 添加到世界
	if err := world.AddPlayer(player); err != nil {
		logger.Errorf("Failed to add player: %v", err)
		return
	}

	// 设置会话
	session.SetConnected(playerID)

	logger.Infof("Player %d connected from %s", playerID, session.Addr.String())
}

// handleDisconnect 处理玩家断开
func handleDisconnect(session *network.Session, world *game.World) {
	if session.PlayerID > 0 {
		world.RemovePlayer(session.PlayerID)
		logger.Infof("Player %d disconnected", session.PlayerID)
	}
}

// gameLoop 游戏主循环
func gameLoop(world *game.World, snapshotMgr *sync.SnapshotManager, server *network.UDPServer, cfg *config.ServerConfig) {
	ticker := time.NewTicker(time.Second / time.Duration(cfg.Game.TickRate))
	defer ticker.Stop()

	for range ticker.C {
		deltaTime := 1.0 / float64(cfg.Game.TickRate)
		world.Update(deltaTime)
	}
}

// syncLoop 状态同步循环
func syncLoop(world *game.World, snapshotMgr *sync.SnapshotManager, server *network.UDPServer, cfg *config.ServerConfig) {
	ticker := time.NewTicker(time.Second / time.Duration(cfg.Game.SnapshotRate))
	defer ticker.Stop()

	for range ticker.C {
		// 获取世界快照
		players := world.GetSnapshot()

		// 保存快照
		snapshot := snapshotMgr.TakeSnapshot(players)

		// 广播快照
		broadcastSnapshot(server, snapshot)
	}
}

// broadcastSnapshot 广播快照
func broadcastSnapshot(server *network.UDPServer, snapshot sync.WorldSnapshot) {
	// 简化实现：直接发送快照
	// 实际应该使用 Protobuf 序列化
	logger.Debugf("Broadcasting snapshot tick=%d players=%d",
		snapshot.Tick, len(snapshot.Players))
}
