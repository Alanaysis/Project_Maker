# 逻辑回归学习笔记

## 1. 核心概念

### 1.1 什么是逻辑回归？

逻辑回归是一种**分类算法**，虽然名字中有"回归"，但用于分类任务。

**核心思想**：
- 将线性回归的输出通过Sigmoid函数映射到(0,1)区间
- 输出可解释为概率
- 通过阈值进行分类决策

### 1.2 为什么叫"逻辑"？

"逻辑"来自Logistic函数（即Sigmoid函数），该函数最初用于人口增长模型。

## 2. Sigmoid函数

### 2.1 数学定义

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

### 2.2 关键性质

1. **输出范围**：(0, 1)，可解释为概率
2. **单调递增**：输入越大，输出越接近1
3. **中心对称**：关于点(0, 0.5)对称
4. **导数优美**：$\sigma'(z) = \sigma(z)(1 - \sigma(z))$

### 2.3 直观理解

```
输入z        输出σ(z)      含义
────────────────────────────────
z >> 0       ≈ 1          很可能是正类
z = 0        = 0.5        不确定
z << 0       ≈ 0          很可能是负类
```

### 2.4 代码实现

```python
def sigmoid(z):
    return 1 / (1 + np.exp(-z))
```

**数值稳定性处理**：
```python
def sigmoid(z):
    z = np.clip(z, -500, 500)  # 防止溢出
    return 1 / (1 + np.exp(-z))
```

## 3. 逻辑回归模型

### 3.1 模型定义

$$P(y=1|x) = \sigma(w^Tx + b)$$

**步骤**：
1. 线性变换：$z = w^Tx + b$
2. Sigmoid激活：$a = \sigma(z)$
3. 阈值判断：如果 $a \geq 0.5$，预测为1；否则预测为0

### 3.2 决策边界

决策边界是 $w^Tx + b = 0$ 定义的超平面。

- 决策边界一侧：预测为正类
- 决策边界另一侧：预测为负类

## 4. 损失函数

### 4.1 为什么不用均方误差？

对于分类问题，MSE存在问题：
1. 非凸优化，容易陷入局部最优
2. 梯度可能很小，收敛慢

### 4.2 交叉熵损失

$$L = -[y\log(a) + (1-y)\log(1-a)]$$

**直观理解**：
- 当y=1时：$L = -\log(a)$，a越接近1，损失越小
- 当y=0时：$L = -\log(1-a)$，a越接近0，损失越小

### 4.3 总损失

$$L = -\frac{1}{m}\sum_{i=1}^{m}[y^{(i)}\log(a^{(i)}) + (1-y^{(i)})\log(1-a^{(i)})]$$

## 5. 梯度下降

### 5.1 梯度推导

**目标**：最小化损失函数L

**步骤**：
1. 对z求导：$\frac{\partial L}{\partial z} = a - y$
2. 对w求导：$\frac{\partial L}{\partial w} = x(a - y)$
3. 对所有样本求平均

**最终公式**：
$$\frac{\partial L}{\partial w} = \frac{1}{m}X^T(a - y)$$
$$\frac{\partial L}{\partial b} = \frac{1}{m}\sum(a - y)$$

### 5.2 参数更新

$$w := w - \alpha \frac{\partial L}{\partial w}$$
$$b := b - \alpha \frac{\partial L}{\partial b}$$

其中α是学习率。

### 5.3 学习率选择

- **太大**：损失震荡，不收敛
- **太小**：收敛速度慢
- **建议**：从0.01开始，观察损失曲线调整

## 6. 正则化

### 6.1 为什么需要正则化？

防止过拟合，限制模型复杂度。

### 6.2 L2正则化

$$L_{regularized} = L + \frac{\lambda}{2m}\sum_{j=1}^{n}w_j^2$$

**效果**：
- 使权重趋向于较小的值
- λ越大，正则化越强

### 6.3 正则化梯度

$$\frac{\partial L_{regularized}}{\partial w} = \frac{\partial L}{\partial w} + \frac{\lambda}{m}w$$

## 7. 评估指标

### 7.1 混淆矩阵

```
              预测
           0    1
实际 0  [ TN | FP ]
     1  [ FN | TP ]
```

### 7.2 常用指标

**准确率 (Accuracy)**：
$$Accuracy = \frac{TP + TN}{TP + TN + FP + FN}$$

**精确率 (Precision)**：
$$Precision = \frac{TP}{TP + FP}$$

含义：预测为正的样本中，真正为正的比例

**召回率 (Recall)**：
$$Recall = \frac{TP}{TP + FN}$$

含义：实际为正的样本中，被正确识别的比例

**F1分数**：
$$F1 = 2 \times \frac{Precision \times Recall}{Precision + Recall}$$

含义：精确率和召回率的调和平均

### 7.3 指标选择

- **准确率**：类别平衡时使用
- **精确率**：关注减少误报（如垃圾邮件检测）
- **召回率**：关注减少漏报（如疾病诊断）
- **F1分数**：精确率和召回率都重要时使用

## 8. 与神经网络的关系

逻辑回归可以看作单层神经网络：

```
输入层  →  [线性变换 + Sigmoid]  →  输出
  x     →      w^T x + b         →   a
```

**区别**：
- 逻辑回归：单层，线性边界
- 神经网络：多层，非线性边界

## 9. 实践技巧

### 9.1 特征工程

虽然逻辑回归不要求特征标准化，但标准化后：
- 收敛更快
- 学习率选择更容易

```python
X_standardized = (X - X.mean(axis=0)) / X.std(axis=0)
```

### 9.2 多分类扩展

**One-vs-Rest (OvR)**：
- 训练K个二分类器
- 每个分类器区分"该类"vs"其他类"
- 预测时选择概率最大的类

### 9.3 常见问题

**问题1：损失不收敛**
- 降低学习率
- 添加特征标准化
- 检查数据质量

**问题2：过拟合**
- 添加正则化
- 减少特征数量
- 增加训练数据

**问题3：欠拟合**
- 增加特征（多项式特征）
- 减小正则化强度
- 增加模型复杂度

## 10. 代码模板

### 10.1 完整训练流程

```python
# 1. 准备数据
X_train, X_test, y_train, y_test = train_test_split(X, y)

# 2. 特征标准化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 3. 训练模型
model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
model.fit(X_train, y_train)

# 4. 评估模型
train_acc = model.score(X_train, y_train)
test_acc = model.score(X_test, y_test)

# 5. 预测新数据
predictions = model.predict(X_new)
```

## 11. 学习资源

### 书籍
- 周志华《机器学习》第3章
- 李航《统计学习方法》第6章

### 在线课程
- Andrew Ng机器学习课程
- 吴恩达深度学习课程

### 实践
- Kaggle二分类比赛
- scikit-learn官方文档

## 12. 总结

### 关键要点

1. 逻辑回归是分类算法，不是回归算法
2. Sigmoid函数将线性输出映射到概率空间
3. 交叉熵损失适合概率估计问题
4. 梯度下降是最常用的优化算法
5. 正则化防止过拟合

### 核心公式

```
模型：P(y=1|x) = σ(w^T x + b)
损失：L = -[y*log(a) + (1-y)*log(1-a)]
梯度：dw = X^T(a-y)/m
更新：w = w - α*dw
```

### 下一步学习

1. 多分类：Softmax回归
2. 非线性：核方法、神经网络
3. 高级优化：Adam、学习率调度
4. 实战项目：Kaggle比赛
