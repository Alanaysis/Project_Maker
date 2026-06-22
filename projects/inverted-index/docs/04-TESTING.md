# 04 - 测试：测试策略与用例

## 测试策略

本项目采用分层测试：
1. **单元测试**：测试各个模块的核心功能
2. **集成测试**：测试模块间的协作
3. **边界测试**：测试异常情况和边界条件

## 测试用例

### Tokenizer 测试

| 测试用例 | 输入 | 预期输出 | 说明 |
|----------|------|----------|------|
| 简单分词 | "hello world" | ["hello", "world"] | 基本分词 |
| 停用词过滤 | "the quick brown fox" | ["quick", "brown", "fox"] | 过滤停用词 |
| 大小写 | "Hello World" | ["hello", "world"] | 统一转小写 |
| 标点符号 | "hello, world!" | ["hello", "world"] | 去除标点 |
| 空字符串 | "" | [] | 边界条件 |
| 全停用词 | "the a an" | [] | 全部过滤 |
| 数字 | "go 1.21" | ["go", "1", "21"] | 数字处理 |
| 位置追踪 | "the quick brown" | [quick:0, brown:1] | 位置信息正确 |

### Index 测试

| 测试用例 | 操作 | 预期结果 | 说明 |
|----------|------|----------|------|
| 添加文档 | AddDocument | 索引更新 | 基本功能 |
| 重复 ID | AddDocument | 返回错误 | 唯一性约束 |
| 空 ID | AddDocument | 返回错误 | 参数验证 |
| 删除文档 | RemoveDocument | 索引更新 | 基本功能 |
| 删除不存在 | RemoveDocument | 返回错误 | 错误处理 |
| 获取文档 | GetDocument | 返回文档 | 基本功能 |
| AND 查询 | "go python" | 交集结果 | 布尔查询 |
| OR 查询 | "go OR python" | 并集结果 | 布尔查询 |
| NOT 查询 | "NOT python" | 排除结果 | 布尔查询 |
| 无结果 | "nonexistent" | 空结果 | 边界条件 |
| 排序 | "go" | 按分数排序 | 相关性排序 |
| 分数正数 | "hello" | score > 0 | 评分正确 |
| 多文档 | 5个文档 | 正确索引 | 规模测试 |
| 删除后搜索 | Remove+Search | 结果更新 | 一致性 |

### Query 测试

| 测试用例 | 输入 | 预期结果 | 说明 |
|----------|------|----------|------|
| AND 查询 | "hello world" | OpAND, 2 terms | 默认 AND |
| OR 查询 | "hello OR world" | OpOR, 2 terms | OR 操作 |
| NOT 查询 | "NOT hello" | OpNOT, 1 term | NOT 操作 |
| 显式 AND | "hello AND world" | OpAND, 2 terms | 显式 AND |
| 空查询 | "" | OpAND, 0 terms | 边界条件 |
| 多 OR | "a OR b OR c" | OpOR, 3 terms | 多操作符 |
| 大小写 | "Hello OR World" | ["hello", "world"] | 不区分大小写 |

## 运行测试

```bash
# 运行所有测试
go test ./tests/ -v

# 运行特定测试
go test ./tests/ -v -run TestTokenize

# 运行测试并显示覆盖率
go test ./tests/ -cover
```

## 测试结果示例

```
=== RUN   TestTokenize
=== RUN   TestTokenize/simple_text
=== RUN   TestTokenize/with_stop_words
=== RUN   TestTokenize/mixed_case
--- PASS: TestTokenize (0.00s)

=== RUN   TestSearchAND
--- PASS: TestSearchAND (0.00s)

=== RUN   TestSearchRanking
--- PASS: TestSearchRanking (0.00s)
```

## 测试覆盖的重点

1. **核心功能**：索引构建、查询处理、评分排序
2. **边界条件**：空输入、重复数据、不存在的数据
3. **错误处理**：参数验证、资源不存在
4. **并发安全**：读写锁的正确使用
