# 脚本目录

本目录包含项目的辅助脚本。

## 脚本列表

### test.sh

测试脚本，用于验证项目是否可以正常运行。

**使用方法**：

```bash
chmod +x scripts/test.sh
./scripts/test.sh
```

**功能**：
- 检查 Go 是否安装
- 安装依赖
- 运行单元测试
- 编译项目

### 手动运行步骤

如果脚本无法运行，请手动执行以下步骤：

```bash
# 1. 安装依赖
go mod tidy

# 2. 运行测试
go test -v ./...

# 3. 编译项目
go build -o bin/chat-server ./cmd/server

# 4. 启动服务器
./bin/chat-server
```

## 环境变量

可以通过环境变量配置服务器：

```bash
export CHAT_SERVER_PORT=8080          # 服务器端口
export CHAT_DB_PATH=./data/chat.db    # 数据库路径
export CHAT_JWT_SECRET=your-secret    # JWT 密钥
export CHAT_JWT_EXPIRY=24h            # Token 有效期
```

## 故障排查

### 依赖下载失败

**问题**：`go mod tidy` 失败

**解决**：
```bash
# 设置 Go 代理（中国大陆）
export GOPROXY=https://goproxy.cn,direct

# 重新下载
go mod tidy
```

### 编译失败

**问题**：`go build` 失败

**解决**：
```bash
# 检查 Go 版本
go version

# 确保版本 >= 1.21
# 如果版本过低，请升级 Go
```

### 测试失败

**问题**：`go test` 失败

**解决**：
```bash
# 查看详细错误信息
go test -v ./...

# 检查是否有语法错误
go vet ./...
```