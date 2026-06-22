# 05 - 开发：环境配置与开发流程

## 环境要求

- Go 1.21+
- 无第三方依赖

## 项目初始化

```bash
# 创建项目目录
mkdir -p projects/inverted-index
cd projects/inverted-index

# 初始化 Go 模块
go mod init github.com/copyninja/inverted-index
```

## 目录结构

```
inverted-index/
├── cmd/                    # 应用入口
│   └── main.go
├── internal/               # 内部包（不可被外部导入）
│   ├── index/              # 索引核心
│   │   ├── types.go        # 数据结构定义
│   │   ├── index.go        # 索引构建与查询
│   │   └── search.go       # 搜索结果
│   ├── tokenizer/          # 分词器
│   │   └── tokenizer.go
│   └── query/              # 查询解析
│       └── parser.go
├── tests/                  # 测试文件
│   ├── tokenizer_test.go
│   ├── index_test.go
│   └── query_test.go
├── docs/                   # 文档
├── go.mod
└── README.md
```

## 开发流程

### 1. 实现分词器

```bash
# 创建分词器
vim internal/tokenizer/tokenizer.go

# 编写测试
vim tests/tokenizer_test.go

# 运行测试
go test ./tests/ -v -run TestTokenize
```

### 2. 实现索引核心

```bash
# 定义数据结构
vim internal/index/types.go

# 实现索引操作
vim internal/index/index.go

# 编写测试
vim tests/index_test.go

# 运行测试
go test ./tests/ -v -run TestIndex
```

### 3. 实现查询解析器

```bash
# 创建解析器
vim internal/query/parser.go

# 编写测试
vim tests/query_test.go

# 运行测试
go test ./tests/ -v -run TestQuery
```

### 4. 实现 CLI

```bash
# 创建主程序
vim cmd/main.go

# 运行程序
go run cmd/main.go
```

## 常用命令

```bash
# 运行所有测试
go test ./tests/ -v

# 运行测试并显示覆盖率
go test ./tests/ -cover

# 运行特定测试
go test ./tests/ -v -run TestSearchAND

# 构建可执行文件
go build -o bin/search cmd/main.go

# 运行可执行文件
./bin/search

# 格式化代码
gofmt -w .

# 检查代码
go vet ./...
```

## 调试技巧

### 打印索引状态

```go
stats := idx.GetStats()
fmt.Printf("Documents: %d, Terms: %d, Tokens: %d\n",
    stats.NumDocuments, stats.NumTerms, stats.TotalTokens)
```

### 查看查询解析结果

```go
q := query.ParseQuery("hello OR world")
fmt.Printf("Operator: %v, Terms: %v\n", q.Operator, q.Terms)
```

### 测试 BM25 评分

```go
results := idx.Search("go")
for _, r := range results {
    fmt.Printf("%s: %.4f\n", r.DocID, r.Score)
}
```

## 常见问题

### Q: 为什么查询没有结果？

1. 检查词项是否被停用词过滤
2. 检查大小写是否匹配（已自动转小写）
3. 检查文档是否正确添加到索引

### Q: 如何添加中文支持？

1. 替换分词器（使用 jieba 等中文分词库）
2. 修改停用词表
3. 考虑中文特有的分词挑战

### Q: 如何提高查询性能？

1. 使用跳表（Skip List）优化倒排表交集
2. 按文档频率排序查询词（先处理稀有词）
3. 使用索引压缩减少内存占用

## 下一步扩展

1. **持久化存储**：将索引保存到文件/数据库
2. **短语查询**：支持 "exact phrase" 查询
3. **模糊查询**：支持拼写纠正
4. **分布式索引**：支持多节点索引
5. **实时索引**：支持增量更新
