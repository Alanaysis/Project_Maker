# 逻辑回归调研报告

## 1. 算法概述

逻辑回归（Logistic Regression）是一种广义线性模型，虽然名字中有"回归"，但它实际上是一种**分类算法**，主要用于二分类问题。

### 核心思想
- 将线性回归的输出通过Sigmoid函数映射到(0,1)区间
- 输出值可解释为属于正类的概率
- 通过设定阈值（通常为0.5）进行分类决策

## 2. 数学原理

### 2.1 线性模型

首先计算线性组合：

$$z = w^T x + b = w_1x_1 + w_2x_2 + ... + w_nx_n + b$$

其中：
- $w$ 是权重向量
- $x$ 是特征向量
- $b$ 是偏置项

### 2.2 Sigmoid函数

Sigmoid函数将线性输出映射到概率空间：

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

**性质**：
- 输出范围：(0, 1)
- 单调递增
- 关于点(0, 0.5)中心对称
- 导数：$\sigma'(z) = \sigma(z)(1 - \sigma(z))$

### 2.3 决策边界

预测规则：
$$
\hat{y} = \begin{cases}
1 & \text{if } \sigma(z) \geq 0.5 \\
0 & \text{if } \sigma(z) < 0.5
\end{cases}
$$

## 3. 损失函数

### 3.1 交叉熵损失（Binary Cross-Entropy）

逻辑回归使用交叉熵损失衡量预测与真实标签的差异：

$$L = -\frac{1}{m}\sum_{i=1}^{m}[y^{(i)}\log(\hat{y}^{(i)}) + (1-y^{(i)})\log(1-\hat{y}^{(i)})]$$

**为什么选择交叉熵而非均方误差？**
- 交叉熵在概率估计错误时惩罚更重
- 梯度形式更简单，优化更高效
- 避免了Sigmoid函数的梯度消失问题

### 3.2 L2正则化

为防止过拟合，可添加L2正则化项：

$$L_{regularized} = L + \frac{\lambda}{2m}\sum_{j=1}^{n}w_j^2$$

## 4. 优化算法

### 4.1 梯度下降

参数更新规则：

$$w := w - \alpha \frac{\partial L}{\partial w}$$
$$b := b - \alpha \frac{\partial L}{\partial b}$$

梯度计算：
$$\frac{\partial L}{\partial w} = \frac{1}{m}X^T(\hat{y} - y)$$
$$\frac{\partial L}{\partial b} = \frac{1}{m}\sum_{i=1}^{m}(\hat{y}^{(i)} - y^{(i)})$$

### 4.2 其他优化算法
- 随机梯度下降（SGD）
- 小批量梯度下降
- Adam优化器
- 牛顿法

## 5. 评估指标

### 5.1 混淆矩阵

|  | 预测为0 | 预测为1 |
|--|---------|---------|
| 实际为0 | TN | FP |
| 实际为1 | FN | TP |

### 5.2 常用指标

- **准确率 (Accuracy)**: $(TP+TN)/(TP+TN+FP+FN)$
- **精确率 (Precision)**: $TP/(TP+FP)$ - 预测为正中真正为正的比例
- **召回率 (Recall)**: $TP/(TP+FN)$ - 实际为正中被正确识别的比例
- **F1分数**: $2 \times \frac{Precision \times Recall}{Precision + Recall}$

## 6. 与scikit-learn对比

### 6.1 sklearn.LogisticRegression特点

```python
from sklearn.linear_model import LogisticRegression

# 主要参数
model = LogisticRegression(
    C=1.0,           # 正则化强度的倒数
    penalty='l2',    # 正则化类型
    solver='lbfgs',  # 优化算法
    max_iter=100     # 最大迭代次数
)
```

### 6.2 我们实现的差异

| 特性 | 自定义实现 | scikit-learn |
|------|-----------|--------------|
| 正则化 | lambda参数 | C参数(倒数) |
| 优化器 | 基础梯度下降 | 多种可选 |
| 多分类 | 仅二分类 | 支持 |
| 收敛性 | 固定迭代次数 | 早停机制 |

## 7. 应用场景

- **医疗诊断**：疾病预测（阳性/阴性）
- **金融风控**：信用评估（违约/不违约）
- **垃圾邮件检测**：邮件分类（垃圾/正常）
- **广告点击预测**：CTR预估

## 8. 优缺点

### 优点
- 模型简单，易于理解和实现
- 输出具有概率意义
- 计算效率高
- 可解释性强

### 缺点
- 只能处理线性可分问题（可通过特征工程扩展）
- 对异常值敏感
- 容易欠拟合

## 9. 参考资源

1. [scikit-learn官方文档](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression)
2. [Andrew Ng机器学习课程](https://www.coursera.org/learn/machine-learning)
3. [周志华《机器学习》](https://book.douban.com/subject/26708119/)
