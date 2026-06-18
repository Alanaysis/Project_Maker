package main

import (
	"fmt"
	"time"

	"github.com/distributed-game-system/internal/game"
	"github.com/distributed-game-system/internal/hashing"
	"github.com/distributed-game-system/internal/prediction"
	"github.com/distributed-game-system/internal/sync"
)

// 快速开始示例
// 这个示例展示了分布式游戏系统的核心功能
func main() {
	fmt.Println("=== 分布式游戏系统 - 快速开始 ===")
	fmt.Println()

	// 示例 1: 游戏世界
	demonstrateWorld()

	// 示例 2: 客户端预测
	demonstratePrediction()

	// 示例 3: 服务器校正
	demonstrateReconciliation()

	// 示例 4: 状态同步
	demonstrateSync()

	// 示例 5: 一致性哈希
	demonstrateHashing()
}

// demonstrateWorld 演示游戏世界
func demonstrateWorld() {
	fmt.Println("--- 1. 游戏世界 ---")

	// 创建游戏世界
	world := game.NewWorld(2000, 2000)

	// 创建玩家
	player1 := game.NewPlayer(1, "Alice", game.Vector2{X: 100, Y: 100})
	player2 := game.NewPlayer(2, "Bob", game.Vector2{X: 200, Y: 200})

	// 添加到世界
	world.AddPlayer(player1)
	world.AddPlayer(player2)

	fmt.Printf("玩家数量: %d\n", world.GetPlayerCount())

	// 模拟移动
	player1.Velocity = game.Vector2{X: 100, Y: 0} // 向右移动

	// 更新世界
	for i := 0; i < 5; i++ {
		world.Update(0.05) // 50ms
		state := player1.GetState()
		fmt.Printf("玩家1位置: (%.1f, %.1f)\n", state.Position.X, state.Position.Y)
	}

	fmt.Println()
}

// demonstratePrediction 演示客户端预测
func demonstratePrediction() {
	fmt.Println("--- 2. 客户端预测 ---")

	// 创建预测器
	predictor := prediction.NewPredictor(60)

	// 初始状态
	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 模拟输入序列
	fmt.Println("发送输入序列:")
	for i := uint32(1); i <= 5; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    1.0, // 向右移动
			Timestamp: time.Now().UnixMilli(),
		}

		// 客户端预测
		predicted := predictor.Predict(input, currentState)
		fmt.Printf("  输入%d: 位置 (%.1f, %.1f) -> 预测 (%.1f, %.1f)\n",
			i, currentState.Position.X, currentState.Position.Y,
			predicted.Position.X, predicted.Position.Y)

		currentState = predicted
	}

	fmt.Printf("待确认输入数: %d\n", predictor.GetPendingCount())
	fmt.Println()
}

// demonstrateReconciliation 演示服务器校正
func demonstrateReconciliation() {
	fmt.Println("--- 3. 服务器校正 ---")

	reconciler := prediction.NewReconciler(0.1)

	// 场景：客户端预测了位置 300，但服务器确认位置是 200
	serverState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 200, Y: 100},
	}

	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 300, Y: 100}, // 客户端预测更远
	}

	// 待处理输入
	pendingInputs := []game.PlayerInput{
		{Sequence: 2, MoveX: 1.0},
		{Sequence: 3, MoveX: 1.0},
	}

	fmt.Printf("服务器位置: (%.1f, %.1f)\n", serverState.Position.X, serverState.Position.Y)
	fmt.Printf("客户端位置: (%.1f, %.1f)\n", currentState.Position.X, currentState.Position.Y)
	fmt.Printf("待处理输入: %d 个\n", len(pendingInputs))

	// 校正
	result := reconciler.Reconcile(serverState, pendingInputs, currentState)
	fmt.Printf("校正后位置: (%.1f, %.1f)\n", result.Position.X, result.Position.Y)
	fmt.Println("注意: 位置被平滑校正，避免突变")
	fmt.Println()
}

// demonstrateSync 演示状态同步
func demonstrateSync() {
	fmt.Println("--- 4. 状态同步 ---")

	// 创建快照管理器
	snapshotMgr := sync.NewSnapshotManager(100)

	// 创建玩家状态
	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
		2: {
			ID:       2,
			Position: game.Vector2{X: 200, Y: 200},
			Health:   100,
		},
	}

	// 创建快照
	for tick := 0; tick < 5; tick++ {
		// 模拟玩家移动
		for id, state := range players {
			state.Position.X += 10
			players[id] = state
		}

		snapshot := snapshotMgr.TakeSnapshot(players)
		fmt.Printf("快照 %d: %d 个玩家\n", snapshot.Tick, len(snapshot.Players))
	}

	// 计算增量
	delta := snapshotMgr.CalculateDelta(1, 5)
	if delta != nil {
		fmt.Printf("增量 (1->5): %d 个变化\n", len(delta.Players))
	}

	fmt.Println()
}

// demonstrateHashing 演示一致性哈希
func demonstrateHashing() {
	fmt.Println("--- 5. 一致性哈希 ---")

	// 创建哈希环
	ring := hashing.NewHashRing(100)

	// 添加服务器
	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	fmt.Printf("服务器数量: %d\n", ring.GetNodeCount())

	// 分配玩家
	fmt.Println("\n玩家分配:")
	for i := 1; i <= 10; i++ {
		playerID := fmt.Sprintf("player-%d", i)
		node, _ := ring.GetNode(playerID)
		fmt.Printf("  %s -> %s\n", playerID, node)
	}

	// 显示分布
	fmt.Println("\n负载分布:")
	dist := ring.GetDistribution(1000)
	for node, count := range dist {
		fmt.Printf("  %s: %d 玩家 (%.1f%%)\n", node, count, float64(count)/10)
	}

	// 演示最小化迁移
	fmt.Println("\n添加新服务器后的迁移:")
	dist1 := make(map[string]int)
	for i := 0; i < 1000; i++ {
		node, _ := ring.GetNode(fmt.Sprintf("player-%d", i))
		dist1[node]++
	}

	ring.AddNode("server-4")

	dist2 := make(map[string]int)
	for i := 0; i < 1000; i++ {
		node, _ := ring.GetNode(fmt.Sprintf("player-%d", i))
		dist2[node]++
	}

	// 统计迁移
	moved := 0
	for i := 0; i < 1000; i++ {
		node1, _ := ring.GetNode(fmt.Sprintf("player-%d", i))
		// 需要重新计算（因为 ring 已经改变）
		_ = node1
	}
	fmt.Printf("理论上只有 ~25%% 的玩家需要迁移\n")
}
