package tests

import (
	"testing"

	"github.com/distributed-game-system/internal/game"
	"github.com/distributed-game-system/internal/hashing"
	"github.com/distributed-game-system/internal/prediction"
	"github.com/distributed-game-system/internal/sync"
)

// 集成测试：测试各模块协作

func TestIntegrationWorldAndSync(t *testing.T) {
	// 创建游戏世界
	world := game.NewWorld(2000, 2000)

	// 创建玩家
	player1 := game.NewPlayer(1, "Alice", game.Vector2{X: 100, Y: 100})
	player2 := game.NewPlayer(2, "Bob", game.Vector2{X: 200, Y: 200})

	world.AddPlayer(player1)
	world.AddPlayer(player2)

	// 创建快照管理器
	snapshotMgr := sync.NewSnapshotManager(100)

	// 模拟游戏循环
	for i := 0; i < 5; i++ {
		// 更新世界
		world.Update(0.05)

		// 获取快照
		players := world.GetSnapshot()
		snapshot := snapshotMgr.TakeSnapshot(players)
	}

	// 验证快照数量
	if snapshotMgr.GetCurrentTick() != 5 {
		t.Errorf("Snapshot tick = %d, want 5", snapshotMgr.GetCurrentTick())
	}
}

func TestIntegrationPredictionAndReconciliation(t *testing.T) {
	// 创建预测器和校正器
	predictor := prediction.NewPredictor(60)
	reconciler := prediction.NewReconciler(0.1)

	// 初始状态
	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 模拟输入序列
	for i := uint32(1); i <= 5; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    1.0,
		}
		currentState = predictor.Predict(input, currentState)
	}

	// 服务器状态（假设服务器确认了前 3 个输入）
	serverState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 350, Y: 100}, // 服务器计算的位置
	}

	// 确认前 3 个输入
	predictor.AcknowledgeInputs(3)

	// 获取待处理输入
	pendingInputs := predictor.GetPendingInputs()

	// 校正
	reconciled := reconciler.Reconcile(serverState, pendingInputs, currentState)

	// 校正后应该在服务器状态附近
	if reconciled.Position.X < 300 || reconciled.Position.X > 400 {
		t.Errorf("Reconciled position X = %.1f, want between 300 and 400", reconciled.Position.X)
	}
}

func TestIntegrationHashingAndWorld(t *testing.T) {
	// 创建哈希环
	ring := hashing.NewHashRing(100)
	ring.AddNode("server-1")
	ring.AddNode("server-2")
	ring.AddNode("server-3")

	// 模拟玩家分配
	worlds := map[string]*game.World{
		"server-1": game.NewWorld(2000, 2000),
		"server-2": game.NewWorld(2000, 2000),
		"server-3": game.NewWorld(2000, 2000),
	}

	// 分配 10 个玩家
	for i := 1; i <= 10; i++ {
		playerID := uint32(i)
		playerName := "Player" + string(rune('0'+i))

		// 使用一致性哈希分配服务器
		serverID, _ := ring.GetNode(playerName)
		world := worlds[serverID]

		// 创建玩家并添加到世界
		player := game.NewPlayer(playerID, playerName, game.GetSpawnPosition(i))
		world.AddPlayer(player)
	}

	// 验证玩家总数
	totalPlayers := 0
	for _, world := range worlds {
		totalPlayers += world.GetPlayerCount()
	}

	if totalPlayers != 10 {
		t.Errorf("Total players = %d, want 10", totalPlayers)
	}

	// 验证分布（应该相对均匀）
	for serverID, world := range worlds {
		count := world.GetPlayerCount()
		t.Logf("%s: %d players", serverID, count)
	}
}

func TestIntegrationFullCycle(t *testing.T) {
	// 完整的游戏循环测试

	// 1. 创建世界
	world := game.NewWorld(2000, 2000)

	// 2. 创建玩家
	player := game.NewPlayer(1, "TestPlayer", game.Vector2{X: 100, Y: 100})
	world.AddPlayer(player)

	// 3. 创建预测器
	predictor := prediction.NewPredictor(60)

	// 4. 创建校正器
	reconciler := prediction.NewReconciler(0.1)

	// 5. 创建快照管理器
	snapshotMgr := sync.NewSnapshotManager(100)

	// 6. 模拟游戏循环
	for tick := 0; tick < 10; tick++ {
		// 客户端预测
		input := game.PlayerInput{
			Sequence: uint32(tick + 1),
			MoveX:    1.0,
		}
		currentState := player.GetState()
		predicted := predictor.Predict(input, currentState)

		// 更新玩家状态
		player.Position = predicted.Position
		player.Velocity = predicted.Velocity

		// 更新世界
		world.Update(0.05)

		// 创建快照
		players := world.GetSnapshot()
		snapshotMgr.TakeSnapshot(players)
	}

	// 验证
	if snapshotMgr.GetCurrentTick() != 10 {
		t.Errorf("Snapshot tick = %d, want 10", snapshotMgr.GetCurrentTick())
	}

	if predictor.GetPendingCount() != 10 {
		t.Errorf("Pending inputs = %d, want 10", predictor.GetPendingCount())
	}
}
