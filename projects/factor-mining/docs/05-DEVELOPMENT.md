# 开发指南

## 项目结构

```
factor-mining/
├── src/
│   ├── __init__.py          # 包初始化
│   ├── data.py              # 数据生成与加载
│   ├── factors.py           # 因子计算
│   ├── evaluation.py        # 因子评估
│   └── backtest.py          # 回测框架
├── tests/
│   ├── __init__.py
│   ├── test_factors.py      # 因子计算测试
│   ├── test_evaluation.py   # 评估模块测试
│   └── test_backtest.py     # 回测模块测试
├── examples/
│   ├── basic_factor_analysis.py  # 基础因子分析
│   └── backtest_example.py       # 回测示例
├── docs/
│   ├── 01-RESEARCH.md       # 研究背景
│   ├── 02-DESIGN.md         # 系统设计
│   ├── 03-IMPLEMENTATION.md # 实现细节
│   ├── 04-TESTING.md        # 测试文档
│   └── 05-DEVELOPMENT.md    # 开发指南
├── README.md
├── LEARNING_NOTES.md
└── requirements.txt
```

## 环境配置

### 依赖
```
numpy>=1.20
pandas>=1.3
scipy>=1.7
pytest>=6.0
```

### 安装
```bash
cd projects/factor-mining
pip install -r requirements.txt
```

## 开发流程

### 添加新因子

1. 在 `src/factors.py` 的 `FactorCalculator` 类中添加方法:

```python
def my_new_factor(self, param: int = 20) -> pd.DataFrame:
    """因子描述

    数学公式: ...
    """
    # 实现
    return result_df
```

2. 在 `tests/test_factors.py` 中添加测试:

```python
def test_my_new_factor(self, calculator):
    result = calculator.my_new_factor(param=20)
    assert result.shape == calculator.price.shape
    # 其他验证
```

3. 在示例中使用:

```python
factors['MY_FACTOR'] = calc.my_new_factor(param=20)
```

### 添加新评估指标

1. 在 `src/evaluation.py` 的 `FactorEvaluator` 类中添加方法:

```python
def my_metric(self) -> float:
    """指标描述"""
    # 实现
    return value
```

2. 添加对应测试

### 修改回测逻辑

回测引擎的核心流程:
```
AllocateWeights(date) -> CalculateReturn(date) -> ApplyCost -> UpdateNAV
```

可修改点:
- `_allocate_weights()`: 改变权重分配策略
- `run()`: 改变收益计算方式
- `BacktestConfig`: 添加新配置项

## 代码规范

### 命名
- 变量/函数: snake_case
- 类: PascalCase
- 常量: UPPER_SNAKE_CASE

### 文档
- 每个公共方法必须有 docstring
- 包含数学公式和参数说明
- 复杂逻辑添加行内注释

### 类型提示
- 使用 Python type hints
- DataFrame 用 pd.DataFrame
- Optional 用于可选参数

## 调试技巧

### 查看因子分布
```python
factor = calc.momentum(20)
print(factor.describe())          # 统计摘要
print(factor.iloc[-1].hist())     # 最新截面分布
```

### 检查 IC 时序
```python
evaluator = FactorEvaluator(factor, returns)
ic = evaluator.rank_ic()
print(ic.plot())                  # IC 时序图
print(ic.rolling(20).mean())      # IC 移动平均
```

### 验证回测
```python
result = engine.run()
df = result.to_dataframe()
print(df.head(20))               # 查看前20天
print(df['drawdown'].min())      # 最大回撤
```

## 常见问题

### Q: 因子 IC 很低怎么办?
- 检查因子是否有预测能力
- 尝试不同窗口参数
- 考虑因子组合
- 检查数据质量

### Q: 回测收益为负?
- 因子方向可能反了 (尝试取负)
- 交易成本可能过高
- 样本量不足
- 因子已失效

### Q: 内存不足?
- 减少股票数量或时间范围
- 使用 float32 替代 float64
- 分批计算因子
