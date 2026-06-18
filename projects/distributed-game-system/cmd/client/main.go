package main

import (
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/distributed-game-system/internal/game"
	"github.com/distributed-game-system/internal/network"
	"github.com/distributed-game-system/internal/prediction"
	"github.com/distributed-game-system/internal/sync"
	"github.com/distributed-game-system/pkg/logger"
)

func main() {
	// 解析命令行参数
	serverAddr := flag.String("server", "localhost:8080", "Server address")
	playerName := flag.String("name", "Player", "Player name")
	flag.Parse()

	logger.Infof("Connecting to %s as %s", *serverAddr, *playerName)

	// 创建本地游戏状态
	localPlayer := game.NewPlayer(0, *playerName, game.Vector2{X: 500, Y: 500})

	// 创建预测器
	predictor := prediction.NewPredictor(60)

	// 创建校正器
	reconciler := prediction.NewReconciler(0.1)

	// 创建插值器（用于显示其他玩家）
	interpolator := sync.NewInterpolator(100, 10)

	// 连接到服务器
	conn, err := connectToServer(*serverAddr)
	if err != nil {
		logger.Fatalf("Failed to connect: %v", err)
	}
	defer conn.Close()

	logger.Info("Connected to server")

	// 启动接收循环
	go receiveLoop(conn, localPlayer, predictor, reconciler, interpolator)

	// 启动输入循环
	go inputLoop(conn, localPlayer, predictor)

	// 启动渲染循环
	go renderLoop(localPlayer, interpolator)

	// 等待退出信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	<-sigCh

	logger.Info("Disconnecting...")
}

// connectToServer 连接到服务器
func connectToServer(addr string) (*net.UDPConn, error) {
	udpAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		return nil, fmt.Errorf("resolve addr: %w", err)
	}

	conn, err := net.DialUDP("udp", nil, udpAddr)
	if err != nil {
		return nil, fmt.Errorf("dial: %w", err)
	}

	// 发送连接请求
	connectPacket, _ := network.EncodePacket(network.MsgConnect, 0, nil)
	_, err = conn.Write(connectPacket)
	if err != nil {
		conn.Close()
		return nil, fmt.Errorf("send connect: %w", err)
	}

	return conn, nil
}

// receiveLoop 接收服务器数据
func receiveLoop(conn *net.UDPConn, player *game.Player, predictor *prediction.Predictor, reconciler *prediction.Reconciler, interpolator *sync.Interpolator) {
	buf := make([]byte, 1500)

	for {
		n, err := conn.Read(buf)
		if err != nil {
			logger.Errorf("Read error: %v", err)
			continue
		}

		packet, err := network.DecodePacket(buf[:n])
		if err != nil {
			logger.Errorf("Decode error: %v", err)
			continue
		}

		switch packet.Header.Type {
		case network.MsgConnectAck:
			logger.Info("Connection acknowledged")
		case network.MsgStateSnapshot:
			handleStateSnapshot(packet, player, predictor, reconciler, interpolator)
		case network.MsgHeartbeat:
			// 计算 RTT
			logger.Debug("Heartbeat received")
		}
	}
}

// handleStateSnapshot 处理状态快照
func handleStateSnapshot(packet *network.Packet, player *game.Player, predictor *prediction.Predictor, reconciler *prediction.Reconciler, interpolator *sync.Interpolator) {
	// 简化实现：实际应该解析 Protobuf
	logger.Debug("State snapshot received")
}

// inputLoop 输入处理循环
func inputLoop(conn *net.UDPConn, player *game.Player, predictor *prediction.Predictor) {
	ticker := time.NewTicker(time.Second / 60) // 60Hz 输入
	defer ticker.Stop()

	var sequence uint32

	for range ticker.C {
		sequence++

		// 获取输入（简化：实际应该从键盘/鼠标获取）
		input := game.PlayerInput{
			Sequence:  sequence,
			Timestamp: time.Now().UnixMilli(),
			MoveX:     0,
			MoveY:     0,
			Attack:    false,
		}

		// 客户端预测
		currentState := player.GetState()
		predicted := predictor.Predict(input, currentState)

		// 更新本地显示
		player.Position = predicted.Position
		player.Velocity = predicted.Velocity
		player.Direction = predicted.Direction

		// 发送到服务器
		sendInput(conn, input)
	}
}

// sendInput 发送输入到服务器
func sendInput(conn *net.UDPConn, input game.PlayerInput) {
	// 简化实现：实际应该使用 Protobuf
	packet, _ := network.EncodePacket(network.MsgPlayerInput, uint16(input.Sequence), nil)
	conn.Write(packet)
}

// renderLoop 渲染循环
func renderLoop(player *game.Player, interpolator *sync.Interpolator) {
	ticker := time.NewTicker(time.Second / 60) // 60fps
	defer ticker.Stop()

	for range ticker.C {
		// 简化实现：实际应该渲染到屏幕
		state := player.GetState()
		logger.Debugf("Player at (%.1f, %.1f) HP: %d",
			state.Position.X, state.Position.Y, state.Health)
	}
}
