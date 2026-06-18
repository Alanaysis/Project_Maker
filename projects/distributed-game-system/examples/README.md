# 使用示例

## 快速开始

### 1. 编译项目

```bash
# 编译服务器和客户端
make build
```

### 2. 启动服务器

```bash
# 使用默认配置启动
./bin/server

# 指定端口
./bin/server -port 8080

# 使用配置文件
./bin/server -config configs/server.yaml
```

### 3. 启动客户端

```bash
# 连接到本地服务器
./bin/client -server localhost:8080 -name Player1
```

### 4. 运行快速开始示例

```bash
# 运行示例代码
go run examples/quickstart.go
```

## 示例说明

### quickstart.go

这个示例展示了分布式游戏系统的核心功能：

1. **游戏世界** - 创建世界、添加玩家、更新状态
2. **客户端预测** - 预测玩家移动
3. **服务器校正** - 校正预测错误
4. **状态同步** - 快照管理和增量同步
5. **一致性哈希** - 玩家分配和负载均衡

## 测试

```bash
# 运行所有测试
make test

# 运行测试并显示覆盖率
make test-cover
```

## 配置

配置文件位于 `configs/server.yaml`：

```yaml
server:
  id: "server-1"
  host: "0.0.0.0"
  udp_port: 8080
  max_players: 100

game:
  tick_rate: 20
  snapshot_rate: 10
  world_width: 2000
  world_height: 2000
```
