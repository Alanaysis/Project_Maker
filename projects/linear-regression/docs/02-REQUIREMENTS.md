# 02 - 需求文档

## 功能需求

### 1. 核心模型

#### LinearRegression（线性回归）
- 支持梯度下降法和正规方程法
- 支持简单线性回归（单特征）和多元线性回归（多特征）
- 记录训练损失历史和参数更新历史

#### RidgeRegression（岭回归）
- L2 正则化
- 支持梯度下降法和正规方程法
- 可调节正则化强度 alpha

#### LassoRegression（Lasso 回归）
- L1 正则化
- 次梯度下降优化
- 自动特征选择（稀疏解）

#### ElasticNet（弹性网络）
- L1+L2 混合正则化
- 可调节 L1/L2 比例 (l1_ratio)

### 2. 损失函数

| 损失函数 | 公式 | 说明 |
|----------|------|------|
| MSE | (1/n) * sum((y-y')^2) | 均方误差 |
| RMSE | sqrt(MSE) | 均方根误差 |
| MAE | (1/n) * sum(|y-y'|) | 平均绝对误差 |

每个损失函数需要实现：
- `compute(y_true, y_pred)`: 计算损失值
- `gradient(y_true, y_pred)`: 计算梯度

### 3. 优化算法

#### 批量梯度下降 (Batch Gradient Descent)
- 使用全部数据计算梯度
- 收敛稳定，适合小数据集

#### 随机梯度下降 (Stochastic Gradient Descent)
- 使用单个样本计算梯度
- 更新频繁，收敛快但噪声大

#### 小批量梯度下降 (Mini-Batch Gradient Descent)
- 使用小批量数据计算梯度
- 平衡效率和稳定性

#### 学习率调度器
- constant: 恒定学习率
- step_decay: 阶梯衰减
- exponential_decay: 指数衰减
- cosine_annealing: 余弦退火

### 4. 特征工程

#### 特征缩放
- StandardScaler: 标准化 (Z-Score)
- MinMaxScaler: 归一化 [0, 1]

#### 多项式特征
- 支持任意阶数
- 自动计算交叉项

#### 特征选择
- 方差阈值选择
- 相关性选择
- 递归特征消除 (RFE)

#### 交叉验证
- K 折交叉验证
- 支持多种评估指标

### 5. 模型评估

| 指标 | 函数 | 范围 | 方向 |
|------|------|------|------|
| MSE | mean_squared_error | [0, +inf) | 越小越好 |
| RMSE | root_mean_squared_error | [0, +inf) | 越小越好 |
| MAE | mean_absolute_error | [0, +inf) | 越小越好 |
| R2 | r2_score | (-inf, 1] | 越大越好 |

### 6. 实际应用示例

#### 房价预测
- 多元特征（面积、卧室数、房龄、距离、楼层）
- 特征缩放
- 多模型对比
- 特征重要性分析

#### 股票预测
- 技术指标特征
- 时间序列处理
- 模拟交易策略

#### 销量预测
- 多元特征处理
- 正则化模型选择
- 交叉验证调参

## 算法清单

| 模块 | 算法/功能 | 文件 |
|------|-----------|------|
| 模型 | LinearRegression | model.py |
| 模型 | RidgeRegression | model.py |
| 模型 | LassoRegression | model.py |
| 模型 | ElasticNet | model.py |
| 损失 | MSELoss | losses.py |
| 损失 | RMSELoss | losses.py |
| 损失 | MAELoss | losses.py |
| 优化 | BatchGradientDescent | optimizers.py |
| 优化 | StochasticGradientDescent | optimizers.py |
| 优化 | MiniBatchGradientDescent | optimizers.py |
| 优化 | LearningRateScheduler | optimizers.py |
| 特征 | StandardScaler | feature_engineering.py |
| 特征 | MinMaxScaler | feature_engineering.py |
| 特征 | PolynomialFeatures | feature_engineering.py |
| 特征 | FeatureSelector | feature_engineering.py |
| 特征 | cross_validation | feature_engineering.py |
| 评估 | MSE/RMSE/MAE/R2 | evaluation.py |

## 非功能需求

### 1. 代码质量
- 清晰的代码结构
- 详细的中英文注释
- 完整的类型提示
- 遵循 PEP 8 规范

### 2. 测试覆盖
- 单元测试覆盖所有模块
- 边界条件测试
- 集成测试
- 测试覆盖率 > 80%

### 3. 文档
- 详细的 README
- API 文档
- 学习笔记
- 6 个文档文件

## 技术约束

1. **Python 版本**：>= 3.8
2. **依赖**：仅使用 NumPy 和 Matplotlib
3. **无外部 ML 框架**：从零实现
