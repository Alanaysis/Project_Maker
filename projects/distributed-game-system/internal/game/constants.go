package game

// 游戏常量定义

const (
	// 移动相关
	MoveSpeed = 200.0 // 像素/秒

	// 战斗相关
	BaseAttackDamage  = 10
	BaseAttackRange   = 50.0
	AttackCooldownSec = 1.0
	BaseHealth        = 100

	// 世界边界
	DefaultWorldWidth  = 2000.0
	DefaultWorldHeight = 2000.0

	// 碰撞检测
	PlayerRadius = 20.0

	// 同步相关
	DefaultTickRate     = 20  // 服务器帧率
	DefaultSnapshotRate = 10  // 快照发送频率
)

// GetSpawnPosition 根据玩家索引获取出生位置
func GetSpawnPosition(index int) Vector2 {
	// 在世界中心区域随机分布
	positions := []Vector2{
		{X: 500, Y: 500},
		{X: 1500, Y: 500},
		{X: 500, Y: 1500},
		{X: 1500, Y: 1500},
		{X: 1000, Y: 1000},
	}

	return positions[index%len(positions)]
}
