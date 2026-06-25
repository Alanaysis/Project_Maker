# 测试文档

## 测试文件说明

| 文件 | 测试内容 | 测试用例数 |
|------|---------|-----------|
| `sliding_window_test.go` | 滑动窗口平均 | 5 |
| `reservoir_test.go` | 蓄水池采样 | 4 |
| `hyperloglog_test.go` | HyperLogLog 基数估计 | 5 |
| `topk_test.go` | Top-K 频繁项 | 5 |

## 运行测试

```bash
go test ./test/... -v
```
