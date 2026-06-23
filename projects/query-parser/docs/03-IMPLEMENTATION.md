# 03 - 实现阶段：查询解析器

## 实现概览

### 项目结构

```
query-parser/
├── cmd/
│   └── parser/
│       └── main.go           # 命令行入口
├── internal/
│   ├── lexer/
│   │   ├── token.go          # Token 定义
│   │   ├── lexer.go          # 词法分析器实现
│   │   └── lexer_test.go     # 词法分析器测试
│   ├── parser/
│   │   ├── parser.go         # 语法分析器实现
│   │   └── parser_test.go    # 语法分析器测试
│   ├── ast/
│   │   └── node.go           # AST 节点定义
│   ├── executor/
│   │   ├── executor.go       # 查询执行器
│   │   └── executor_test.go  # 执行器测试
│   ├── index/
│   │   ├── index.go          # 倒排索引
│   │   └── index_test.go     # 索引测试
│   └── query_test.go         # 集成测试
├── examples/
│   └── queries.txt           # 查询示例
├── docs/                     # 文档
├── go.mod                    # Go 模块定义
└── README.md                 # 项目说明
```

## 核心实现

### 1. 词法分析器 (Lexer)

#### Token 类型定义

```go
const (
    TokenTerm     TokenType = iota // 普通术语
    TokenPhrase                     // 短语 "..."
    TokenAnd                        // AND 关键字
    TokenOr                         // OR 关键字
    TokenNot                        // NOT 关键字
    TokenLParen                     // 左括号 (
    TokenRParen                     // 右括号 )
    TokenEOF                        // 输入结束
)
```

#### 核心逻辑

1. **跳过空白**：处理空格、制表符
2. **读取短语**：双引号包围的内容
3. **读取单词**：非空白字符序列
4. **识别关键字**：AND、OR、NOT（大小写不敏感）

### 2. 语法分析器 (Parser)

#### 递归下降解析

使用递归下降方法实现，处理运算符优先级：

1. `parseOr()` - 最低优先级
2. `parseAnd()` - 中等优先级
3. `parseNot()` - 高优先级
4. `parsePrimary()` - 最高优先级（术语、短语、括号）

#### 隐式 AND

当两个术语相邻时，自动转换为 AND 操作：
- `quick fox` → `quick AND fox`

### 3. AST 节点

#### 节点类型

```go
const (
    NodeTerm   NodeType = iota // 术语节点
    NodePhrase                  // 短语节点
    NodeAnd                     // AND 操作
    NodeOr                      // OR 操作
    NodeNot                     // NOT 操作
)
```

#### 节点方法

- `String()` - 字符串表示
- `CollectTerms()` - 收集所有术语

### 4. 执行器 (Executor)

#### 查询执行

1. **术语查询**：从索引搜索包含该术语的文档
2. **短语查询**：搜索包含所有术语的文档，然后验证短语连续性
3. **AND 操作**：两个结果集的交集
4. **OR 操作**：两个结果集的并集
5. **NOT 操作**：从所有文档中排除匹配文档

#### 相关性排序

使用简化版 TF-IDF 算法：

```go
score = Σ (tf × idf)
tf = 术语在文档中出现的次数
idf = 1 + 总文档数 / 包含该术语的文档数
```

### 5. 倒排索引 (Index)

#### 数据结构

```go
type Index struct {
    documents map[string]*Document     // 文档存储
    index     map[string]map[string]bool // 术语 → 文档ID集合
}
```

#### 核心操作

1. **AddDocument** - 添加文档并建立索引
2. **Search** - 搜索包含术语的文档
3. **GetDocument** - 获取文档内容
4. **AllDocuments** - 获取所有文档ID

#### 分词器

简单的空白和标点分词：

```go
func tokenize(text string) []string {
    // 转换为小写
    // 按空白和标点分割
    // 返回术语列表
}
```

## 测试覆盖

### 单元测试

1. **Lexer 测试**
   - 基本术语解析
   - 短语解析
   - 布尔运算符
   - 括号处理
   - 复杂查询

2. **Parser 测试**
   - 术语解析
   - 短语解析
   - AND 操作
   - OR 操作
   - NOT 操作
   - 运算符优先级
   - 括号优先级
   - 错误处理

3. **Executor 测试**
   - 术语查询
   - 短语查询
   - AND 操作
   - OR 操作
   - NOT 操作
   - 复杂查询
   - 相关性排序

4. **Index 测试**
   - 文档添加
   - 术语搜索
   - 大小写不敏感
   - 多文档搜索

### 集成测试

测试完整的查询流程：
1. 简单术语查询
2. 布尔 AND 查询
3. 布尔 OR 查询
4. NOT 查询
5. 短语查询
6. 复杂组合查询
7. 隐式 AND 查询
8. 相关性排序

## 性能考虑

### 时间复杂度

- **词法分析**：O(n)，n 为查询长度
- **语法分析**：O(m)，m 为 token 数量
- **查询执行**：O(k)，k 为匹配文档数
- **排序**：O(k log k)

### 空间复杂度

- **AST**：O(m)，m 为节点数
- **索引**：O(n × d)，n 为术语数，d 为文档数

## 已知限制

1. 不支持通配符查询（`*`、`?`）
2. 不支持模糊查询
3. 不支持范围查询
4. 简化的相关性算法
5. 内存索引，不支持持久化
