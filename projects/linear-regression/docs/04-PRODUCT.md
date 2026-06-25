# 04 - 产品文档

## 产品概述

线性回归教学项目是一个从零实现的机器学习学习工具，涵盖线性回归的全部核心技术，帮助学习者建立扎实的机器学习基础。

## 目标用户

1. **机器学习初学者**：想了解基础算法原理
2. **学生**：学习机器学习课程
3. **开发者**：想深入理解算法实现细节
4. **数据分析师**：需要掌握回归分析基础

## 学习目标

通过本项目，学习者将掌握：

### 知识层面
1. 线性回归的数学原理
2. 梯度下降的优化过程
3. 正则化的作用和原理
4. 特征工程的重要性
5. 模型评估的方法

### 技能层面
1. 从零实现机器学习算法
2. 使用 NumPy 进行矩阵运算
3. 实现不同的优化算法
4. 进行特征工程和模型选择
5. 评估和调优模型

### 实践层面
1. 完整的机器学习工作流程
2. 实际应用场景的处理
3. 代码组织和测试

## 关键要点

### 1. 数学基础
- 线性模型：y = X @ w + b
- 损失函数：MSE = (1/n) * sum((y-y')^2)
- 梯度下降：w = w - lr * grad(Loss)

### 2. 正则化
- L2 (Ridge)：权重收缩，防止过拟合
- L1 (Lasso)：稀疏解，特征选择
- Elastic Net：结合两者优点

### 3. 优化算法
- BGD：稳定但慢
- SGD：快但噪声大
- Mini-Batch：平衡两者
- 学习率调度：动态调整

### 4. 特征工程
- 缩放：标准化/归一化
- 多项式：处理非线性
- 选择：减少冗余特征
- 交叉验证：评估泛化能力

### 5. 模型评估
- MSE/RMSE：误差度量
- MAE：鲁棒误差度量
- R2：解释方差比例

## 使用场景

### 场景 1：学习线性回归原理
```python
from src.model import LinearRegression
model = LinearRegression(learning_rate=0.01, n_iterations=100)
model.fit(X_train, y_train)
```

### 场景 2：学习正则化
```python
from src.model import RidgeRegression, LassoRegression
ridge = RidgeRegression(alpha=1.0)
lasso = LassoRegression(alpha=0.1)
```

### 场景 3：学习特征工程
```python
from src.feature_engineering import StandardScaler, PolynomialFeatures
scaler = StandardScaler()
poly = PolynomialFeatures(degree=2)
```

### 场景 4：实际应用
```python
# 参考 examples/ 目录下的示例
python examples/house_price_prediction.py
```

## 功能清单

### 核心功能
- [x] 简单线性回归
- [x] 多元线性回归
- [x] 梯度下降法
- [x] 正规方程法
- [x] Ridge 回归 (L2)
- [x] Lasso 回归 (L1)
- [x] Elastic Net

### 优化功能
- [x] 批量梯度下降
- [x] 随机梯度下降
- [x] 小批量梯度下降
- [x] 学习率调度

### 特征工程
- [x] 标准化缩放
- [x] 归一化缩放
- [x] 多项式特征
- [x] 方差阈值选择
- [x] 相关性选择
- [x] RFE 特征选择
- [x] K 折交叉验证

### 评估指标
- [x] MSE
- [x] RMSE
- [x] MAE
- [x] R2

### 应用示例
- [x] 房价预测
- [x] 股票预测
- [x] 销量预测

## 质量标准

1. 所有代码可运行
2. 所有测试通过
3. 文档完整
4. 注释详细
5. 类型提示完整
