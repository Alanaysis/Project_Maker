# CDN Service - 内容分发网络服务

## 📖 项目简介

实现一个轻量级的内容分发网络（CDN）服务，支持缓存、智能调度和回源机制。通过这个项目，深入理解CDN的核心架构和工作原理。

## 🎯 学习目标

- ⭐ **CDN架构理解**：掌握CDN的分层架构和工作流程
- ⭐ **缓存策略**：实现LRU等缓存淘汰算法
- ⭐ **智能调度**：理解DNS调度和负载均衡原理
- ⭐ **回源机制**：实现缓存未命中时的回源逻辑
- 💡 **性能优化**：学习高并发场景下的优化技巧

## 🛠️ 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Go | 主语言 | ⭐⭐ |
| net/http | HTTP服务 | ⭐⭐ |
| sync.Map | 并发缓存 | ⭐⭐⭐ |
| container/list | LRU实现 | ⭐⭐ |

## 🏗️ 系统架构

```
用户请求 → 智能调度 → 边缘节点 → 缓存命中 → [未命中] → 回源 → 缓存 → 返回
```

### 核心组件

1. **HTTP Server**：接收和处理HTTP请求
2. **Cache Manager**：管理缓存存储和淘汰
3. **Dispatcher**：智能调度和负载均衡
4. **Origin Fetcher**：回源获取内容
5. **Health Checker**：节点健康检查

## 📁 项目结构

```
cdn-service/
├── cmd/
│   └── cdn-server/      # 主程序入口
├── pkg/
│   ├── cache/           # 缓存模块
│   │   ├── lru.go       # LRU缓存实现
│   │   └── manager.go   # 缓存管理器
│   ├── dispatcher/      # 调度模块
│   │   └── scheduler.go # 智能调度
│   ├── origin/          # 回源模块
│   │   └── fetcher.go   # 回源获取
│   └── server/          # HTTP服务器
│       └── handler.go   # 请求处理
├── docs/                # 文档
├── examples/            # 使用示例
└── tests/               # 单元测试
```

## 🚀 快速开始

### 环境要求

- Go 1.21+
- Git

### 安装和运行

```bash
# 克隆项目
cd projects/cdn-service

# 初始化Go模块
go mod init cdn-service

# 编译
go build -o bin/cdn-server cmd/cdn-server/main.go

# 运行
./bin/cdn-server -port 8080 -origin http://origin.example.com
```

### 测试缓存

```bash
# 第一次请求（回源）
curl -v http://localhost:8080/test.html

# 第二次请求（缓存命中）
curl -v http://localhost:8080/test.html
```

## ⭐ 重点难点

### 1. LRU缓存实现
- 使用双向链表+哈希表实现O(1)的访问和删除
- 并发安全的缓存访问
- 缓存过期和淘汰策略

### 2. 智能调度算法
- 基于地理位置的调度
- 基于负载的调度
- 基于网络质量的调度

### 3. 回源优化
- 并发回源控制
- 回源合并（防止缓存击穿）
- 部分内容回源（Range请求）

## 💡 值得思考

1. **缓存一致性**：如何保证多个边缘节点的缓存一致性？
2. **缓存击穿**：热点key过期时如何防止大量请求穿透到源站？
3. **缓存雪崩**：大量缓存同时过期时如何应对？
4. **负载均衡**：如何根据节点状态动态调整权重？
5. **健康检查**：如何快速检测节点故障并切换？

## 📚 相关资源

- [Nginx官方文档](https://nginx.org/en/docs/)
- [Varnish Cache文档](https://varnish-cache.org/docs/)
- [OpenResty文档](https://openresty.org/en/)
- [CDN技术详解](https://www.cdnplanet.com/)
- [HTTP缓存规范](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Caching)

## 📊 性能指标

- 缓存命中率：> 90%
- 响应时间：< 50ms（缓存命中）
- 并发支持：> 1000 QPS
- 回源延迟：< 200ms

## 🔧 配置说明

```yaml
server:
  port: 8080
  read_timeout: 30s
  write_timeout: 30s

cache:
  max_size: 1GB
  default_ttl: 3600s
  cleanup_interval: 300s

origin:
  url: http://origin.example.com
  timeout: 10s
  retry_count: 3

dispatcher:
  algorithm: round-robin  # round-robin, least-connections, ip-hash
  health_check_interval: 30s
```

## 📝 开发日志

- [ ] 实现基础HTTP服务器
- [ ] 实现LRU缓存
- [ ] 实现缓存管理器
- [ ] 实现回源机制
- [ ] 实现智能调度
- [ ] 编写单元测试
- [ ] 性能测试和优化

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License