# 实现细节

## 模块详解

### 1. data.py - 数据生成模块

#### generate_stock_data()
使用几何布朗运动生成模拟股票数据:

```python
# 收益率生成
ret[i, t] = mu[i] + beta[i] * market[t] + momentum_component + noise

# 价格生成
price[t] = price[t-1] * (1 + ret[t])
```

关键设计:
- 每只股票有不同的 mu 和 sigma (横截面差异)
- 加入市场共同因子 (beta 不同)
- 加入动量效应 (可被因子捕捉)
- 成交量与波动率正相关

#### split_train_test()
按时间分割, 避免未来信息泄露:
```python
train = data[:split_idx]
test  = data[split_idx:]
```

### 2. factors.py - 因子计算模块

#### 动量因子
```python
MOM_t = Price_t / Price_{t-window} - 1
```
- 窗口越长, 因子越平滑
- 短期反转是动量的负值

#### 波动率因子
```python
VOL = Std(returns, window)
```
- 下行波动率: 仅计算负收益的标准差
- ATR: 真实波幅的均值

#### 流动性因子
```python
AMIHUD = Mean(|ret| / volume, window)
```
- Amihud (2002) 非流动性指标
- 值越大, 流动性越差

#### 组合因子
截面标准化后加权:
```python
z_i = (f_i - mean) / std
composite = sum(w_i * z_i)
```

### 3. evaluation.py - 因子评估模块

#### IC 计算
使用 SciPy 的 spearmanr:
```python
from scipy.stats import spearmanr
corr, pvalue = spearmanr(factor_values, return_values)
```

#### 分组收益
使用 pd.qcut 进行分位数分组:
```python
groups = pd.qcut(factor_values, n_groups, labels=False)
```

#### 因子衰减
对不同持有期计算 IC 和多空收益:
```python
for lag in range(1, max_lag+1):
    future_ret = returns.shift(-lag)
    ic[lag] = compute_ic(factor, future_ret)
```

### 4. backtest.py - 回测框架模块

#### 权重分配
```python
# 多空策略
weights[top_group] = +1/n_top
weights[bottom_group] = -1/n_bottom

# 纯多头
weights[top_group] = 1/n_top
```

#### 交易成本
```python
turnover = sum(|new_weight - old_weight|) / 2
cost = turnover * 2 * commission_rate
```

#### NAV 计算
```python
nav[t] = nav[t-1] * (1 + portfolio_return[t] - cost)
```

## 性能优化

### 向量化操作
- 使用 Pandas 的 rolling() 而非循环
- 使用 NumPy 的向量化运算
- 避免逐行 iterrows()

### 内存管理
- 生成数据时使用 float64
- 评估时及时释放中间变量

## 数值稳定性

### NaN 处理
- 因子计算中使用 fillna() 处理窗口期
- 评估中使用 dropna() 对齐截面

### 除零保护
```python
# 使用 epsilon 避免除零
result = numerator / (denominator + 1e-10)
```

### 异常值处理
- 因子值理论上无界, 但极端值可能影响评估
- 可选: 截面 winsorize (本框架未实现, 保持简洁)
