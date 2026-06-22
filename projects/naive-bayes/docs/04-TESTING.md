# 测试策略

## 测试目标

验证朴素贝叶斯分类器的正确性、健壮性和性能。

## 测试分类

### 1. 单元测试

**测试对象**: 各个类的方法

**测试内容**:
- `fit()`: 训练功能
- `predict()`: 预测功能
- `predict_proba()`: 概率预测
- `score()`: 准确率计算
- `_calculate_likelihood()`: 似然计算

### 2. 集成测试

**测试对象**: 完整的分类流程

**测试内容**:
- 从训练到预测的完整流程
- 不同数据类型的处理
- 多类别分类

### 3. 边界测试

**测试对象**: 异常情况

**测试内容**:
- 空数据
- 不匹配的数据长度
- 训练前预测
- 负特征值 (多项式)

## 测试用例

### 高斯朴素贝叶斯

| 测试用例 | 验证点 |
|---------|-------|
| 基本训练 | 模型状态、类别、先验概率 |
| 先验概率 | 平衡/不平衡数据 |
| 均值计算 | 按类别分组计算 |
| 基本预测 | 正确分类 |
| 概率预测 | 概率和为1、概率排序 |
| 准确率 | 正确率计算 |
| 单特征 | 简单数据 |
| 多类别 | 三分类 |
| 方差平滑 | 防止除零 |

### 多项式朴素贝叶斯

| 测试用例 | 验证点 |
|---------|-------|
| 文本分类 | 词频特征 |
| 负特征检查 | 输入验证 |
| Laplace平滑 | 零概率处理 |

### 伯努利朴素贝叶斯

| 测试用例 | 验证点 |
|---------|-------|
| 二值特征 | 0/1特征 |
| 邮件检测 | 实际应用场景 |
| 概率计算 | 对数概率 |

## 运行测试

```bash
# 运行所有测试
cd projects/naive-bayes
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_gaussian_naive_bayes.py -v

# 运行并显示覆盖率
python -m pytest tests/ -v --tb=short
```

## 测试结果示例

```
tests/test_gaussian_naive_bayes.py::TestGaussianNaiveBayes::test_fit_basic PASSED
tests/test_gaussian_naive_bayes.py::TestGaussianNaiveBayes::test_predict_basic PASSED
tests/test_gaussian_naive_bayes.py::TestGaussianNaiveBayes::test_predict_proba PASSED
...
```

## 测试覆盖率

目标: 核心功能 100% 覆盖

- fit(): 100%
- predict(): 100%
- predict_proba(): 100%
- score(): 100%
- 错误处理: 100%
