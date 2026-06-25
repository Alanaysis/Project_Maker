# 03_DESIGN.md - 技术设计文档

## 1. 架构设计

### 1.1 整体架构

```
logistic-regression/
├── src/                        # 源代码
│   ├── logistic_regression.py  # 基础逻辑回归
│   ├── multiclass.py           # 多分类实现
│   ├── regularization.py       # 正则化实现
│   ├── metrics.py              # 评估指标
│   ├── feature_engineering.py  # 特征工程
│   ├── optimizers.py           # 优化算法
│   └── __init__.py             # 包初始化
├── examples/                   # 示例代码
├── tests/                      # 测试代码
├── docs/                       # 文档
├── main.py                     # 主入口
└── requirements.txt            # 依赖
```

### 1.2 模块依赖关系

```
                    +-----------------+
                    |   __init__.py   |
                    +-----------------+
                            |
        +-------------------+-------------------+
        |                   |                   |
+-------v-------+   +-------v-------+   +-------v-------+
| logistic_     |   | multiclass.py |   | regularization|
| regression.py |   |               |   |     .py       |
+---------------+   +---------------+   +---------------+
        |                   |                   |
        +-------------------+-------------------+
                            |
                    +-------v-------+
                    |   metrics.py  |
                    +---------------+
                            |
                    +-------v-------+
                    |   feature_    |
                    | engineering.py|
                    +---------------+
                            |
                    +-------v-------+
                    |  optimizers.py|
                    +---------------+
```

## 2. 类设计

### 2.1 LogisticRegression类

```python
class LogisticRegression:
    """基础逻辑回归分类器"""

    # 参数
    learning_rate: float       # 学习率
    n_iterations: int          # 迭代次数
    regularization: float      # L2正则化强度
    threshold: float           # 分类阈值
    verbose: bool              # 是否打印训练过程

    # 属性
    weights: np.ndarray        # 模型权重
    bias: float                # 偏置项
    losses: list               # 损失记录

    # 方法
    fit(X, y) -> self          # 训练模型
    predict_proba(X) -> ndarray # 预测概率
    predict(X) -> ndarray      # 预测类别
    score(X, y) -> float       # 计算准确率
```

### 2.2 多分类类

```python
class OneVsRestClassifier:
    """One-vs-Rest多分类策略"""

    # 参数
    learning_rate: float
    n_iterations: int
    regularization: float

    # 属性
    classifiers: List[LogisticRegression]
    classes: np.ndarray

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray


class OneVsOneClassifier:
    """One-vs-One多分类策略"""

    # 参数
    learning_rate: float
    n_iterations: int
    regularization: float

    # 属性
    classifiers: Dict[Tuple, LogisticRegression]
    classes: np.ndarray

    # 方法
    fit(X, y) -> self
    predict(X) -> ndarray


class SoftmaxRegression:
    """Softmax回归"""

    # 参数
    learning_rate: float
    n_iterations: int
    regularization: float

    # 属性
    weights: np.ndarray        # 权重矩阵 (n_classes, n_features)
    bias: np.ndarray           # 偏置向量 (n_classes,)
    classes: np.ndarray

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray
    score(X, y) -> float
```

### 2.3 正则化类

```python
class LogisticRegressionL1:
    """L1正则化逻辑回归"""

    # 参数
    learning_rate: float
    n_iterations: int
    lambda_param: float        # L1正则化强度
    threshold: float

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray
    score(X, y) -> float


class LogisticRegressionL2:
    """L2正则化逻辑回归"""

    # 参数
    learning_rate: float
    n_iterations: int
    lambda_param: float        # L2正则化强度
    threshold: float

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray
    score(X, y) -> float


class ElasticNet:
    """Elastic Net正则化逻辑回归"""

    # 参数
    learning_rate: float
    n_iterations: int
    l1_ratio: float            # L1比例
    lambda_param: float        # 正则化强度
    threshold: float

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray
    score(X, y) -> float
```

### 2.4 优化器类

```python
class BaseOptimizer:
    """优化器基类"""

    # 参数
    learning_rate: float
    n_iterations: int
    threshold: float

    # 属性
    weights: np.ndarray
    bias: float
    losses: list

    # 方法
    fit(X, y) -> self
    predict_proba(X) -> ndarray
    predict(X) -> ndarray
    score(X, y) -> float


class BatchGradientDescent(BaseOptimizer):
    """批量梯度下降"""


class StochasticGradientDescent(BaseOptimizer):
    """随机梯度下降"""

    # 额外参数
    learning_rate_schedule: str  # 学习率调度策略


class MiniBatchGradientDescent(BaseOptimizer):
    """小批量梯度下降"""

    # 额外参数
    batch_size: int


class MomentumOptimizer(BaseOptimizer):
    """动量优化器"""

    # 额外参数
    momentum: float

    # 额外属性
    velocity_w: np.ndarray
    velocity_b: float


class AdamOptimizer(BaseOptimizer):
    """Adam优化器"""

    # 额外参数
    beta1: float
    beta2: float
    epsilon: float

    # 额外属性
    m_w, v_w: np.ndarray
    m_b, v_b: float


class LearningRateScheduler:
    """学习率调度器"""

    # 参数
    initial_lr: float
    schedule: str
    step_size: int
    gamma: float

    # 方法
    get_lr(epoch) -> float
```

### 2.5 特征工程类

```python
class StandardScaler:
    """标准化缩放器"""

    # 属性
    mean: np.ndarray
    std: np.ndarray

    # 方法
    fit(X) -> self
    transform(X) -> ndarray
    fit_transform(X) -> ndarray
    inverse_transform(X) -> ndarray


class MinMaxScaler:
    """归一化缩放器"""

    # 参数
    feature_range: tuple

    # 属性
    min: np.ndarray
    max: np.ndarray

    # 方法
    fit(X) -> self
    transform(X) -> ndarray
    fit_transform(X) -> ndarray
    inverse_transform(X) -> ndarray


class VarianceThreshold:
    """方差阈值特征选择"""

    # 参数
    threshold: float

    # 属性
    variances: np.ndarray
    support: np.ndarray

    # 方法
    fit(X) -> self
    transform(X) -> ndarray
    fit_transform(X) -> ndarray
    get_support() -> ndarray


class CorrelationThreshold:
    """相关性阈值特征选择"""

    # 参数
    threshold: float

    # 属性
    correlation_matrix: np.ndarray
    support: np.ndarray

    # 方法
    fit(X) -> self
    transform(X) -> ndarray
    fit_transform(X) -> ndarray
    get_support() -> ndarray
```

## 3. 接口设计

### 3.1 统一接口

所有模型类遵循统一的接口设计：

```python
# 训练
model.fit(X: np.ndarray, y: np.ndarray) -> self

# 预测概率
model.predict_proba(X: np.ndarray) -> np.ndarray

# 预测类别
model.predict(X: np.ndarray) -> np.ndarray

# 评估
model.score(X: np.ndarray, y: np.ndarray) -> float
```

### 3.2 评估指标接口

```python
# 单个指标
accuracy_score(y_true, y_pred) -> float
precision_score(y_true, y_pred) -> float
recall_score(y_true, y_pred) -> float
f1_score(y_true, y_pred) -> float

# 混淆矩阵
confusion_matrix(y_true, y_pred) -> Tuple[int, int, int, int]

# 分类报告
classification_report(y_true, y_pred) -> str

# ROC曲线
roc_curve(y_true, y_scores) -> Tuple[np.ndarray, np.ndarray, np.ndarray]

# AUC
auc_score(fpr, tpr) -> float
```

### 3.3 特征工程接口

```python
# 缩放器
scaler.fit(X) -> self
scaler.transform(X) -> np.ndarray
scaler.fit_transform(X) -> np.ndarray
scaler.inverse_transform(X) -> np.ndarray

# 特征选择
selector.fit(X) -> self
selector.transform(X) -> np.ndarray
selector.fit_transform(X) -> np.ndarray
selector.get_support() -> np.ndarray

# 交叉验证
cross_validate(model, X, y, cv, scoring) -> np.ndarray
train_test_split(X, y, test_size, random_state) -> Tuple
```

## 4. 数据流设计

### 4.1 训练流程

```
输入数据 (X, y)
    ↓
特征缩放 (StandardScaler/MinMaxScaler)
    ↓
划分数据集 (train_test_split)
    ↓
模型训练 (model.fit)
    ↓
保存模型参数 (weights, bias)
```

### 4.2 预测流程

```
输入数据 (X)
    ↓
特征缩放 (scaler.transform)
    ↓
计算线性输出 (z = X @ weights + bias)
    ↓
应用激活函数 (sigmoid/softmax)
    ↓
输出概率 (predict_proba)
    ↓
应用阈值 (predict)
```

### 4.3 评估流程

```
真实标签 (y_true)
预测结果 (y_pred/y_scores)
    ↓
计算混淆矩阵 (TP, TN, FP, FN)
    ↓
计算评估指标 (accuracy, precision, recall, f1)
    ↓
生成分类报告 (classification_report)
    ↓
绘制ROC曲线 (roc_curve)
    ↓
计算AUC (auc_score)
```

## 5. 算法设计

### 5.1 Sigmoid函数

```python
def sigmoid(z):
    """σ(z) = 1 / (1 + e^(-z))"""
    z = np.clip(z, -500, 500)  # 数值稳定性
    return 1 / (1 + np.exp(-z))
```

### 5.2 交叉熵损失

```python
def cross_entropy_loss(y_true, y_pred):
    """L = -1/m * Σ[y*log(p) + (1-y)*log(1-p)]"""
    epsilon = 1e-15
    y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
```

### 5.3 梯度计算

```python
def compute_gradients(X, y_true, y_pred):
    """∂L/∂w = 1/m * X^T * (p - y)"""
    m = len(y_true)
    error = y_pred - y_true
    dw = (1 / m) * np.dot(X.T, error)
    db = (1 / m) * np.sum(error)
    return dw, db
```

### 5.4 正则化梯度

```python
# L1正则化
dw += lambda_param * np.sign(weights)

# L2正则化
dw += lambda_param * weights

# Elastic Net
dw += lambda_param * (l1_ratio * np.sign(weights) + (1 - l1_ratio) * weights)
```

### 5.5 Softmax函数

```python
def softmax(z):
    """softmax(z_i) = e^(z_i) / Σ e^(z_j)"""
    z_max = np.max(z, axis=1, keepdims=True)
    exp_z = np.exp(z - z_max)
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)
```

## 6. 示例设计

### 6.1 垃圾邮件分类

```
输入特征:
- word_freq_free: "free"出现频率
- word_freq_money: "money"出现频率
- word_freq_win: "win"出现频率
- word_freq_click: "click"出现频率
- word_freq_offer: "offer"出现频率
- capital_run_length_avg: 连续大写字母平均长度
- capital_run_length_max: 连续大写字母最大长度

输出: 0 (正常邮件) 或 1 (垃圾邮件)
```

### 6.2 疾病诊断

```
输入特征:
- age: 年龄
- blood_pressure: 血压
- cholesterol: 胆固醇
- blood_sugar: 血糖
- heart_rate: 心率
- bmi: 体重指数
- smoking: 吸烟史

输出: 0 (健康) 或 1 (患病)
```

### 6.3 信用评分

```
输入特征:
- income: 年收入
- debt_ratio: 负债收入比
- credit_history_length: 信用历史长度
- num_credit_lines: 信用账户数量
- late_payments: 近期逾期次数
- employment_years: 工作年限
- home_ownership: 是否有房产

输出: 0 (拒绝) 或 1 (批准)
```

## 7. 测试设计

### 7.1 单元测试

```python
# 测试Sigmoid函数
def test_sigmoid():
    assert sigmoid(0) == 0.5
    assert sigmoid(100) ≈ 1.0
    assert sigmoid(-100) ≈ 0.0

# 测试损失函数
def test_cross_entropy_loss():
    # 完美预测
    assert cross_entropy_loss([1, 0], [1, 0]) ≈ 0.0
    # 完全错误
    assert cross_entropy_loss([1, 0], [0, 1]) > 1.0

# 测试梯度计算
def test_compute_gradients():
    # 验证梯度方向正确
    ...
```

### 7.2 集成测试

```python
# 测试完整训练流程
def test_training_pipeline():
    model = LogisticRegression()
    model.fit(X_train, y_train)
    assert model.score(X_test, y_test) > 0.5

# 测试评估流程
def test_evaluation_pipeline():
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred)
    assert "准确率" in report
```

### 7.3 性能测试

```python
# 测试训练时间
def test_training_time():
    import time
    start = time.time()
    model.fit(X, y)
    duration = time.time() - start
    assert duration < 1.0  # 应在1秒内完成

# 测试内存使用
def test_memory_usage():
    import tracemalloc
    tracemalloc.start()
    model.fit(X, y)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert peak < 100 * 1024 * 1024  # 应小于100MB
```

## 8. 错误处理设计

### 8.1 输入验证

```python
def validate_input(X, y):
    """验证输入数据"""
    X = np.array(X)
    y = np.array(y)

    # 检查维度
    if X.ndim != 2:
        raise ValueError("X must be 2D array")
    if y.ndim != 1:
        raise ValueError("y must be 1D array")

    # 检查样本数量匹配
    if len(X) != len(y):
        raise ValueError("X and y must have same number of samples")

    # 检查标签值
    if not np.all(np.isin(y, [0, 1])):
        raise ValueError("y must contain only 0 and 1")

    return X, y
```

### 8.2 数值稳定性

```python
# Sigmoid函数数值稳定性
z = np.clip(z, -500, 500)

# 对数函数数值稳定性
epsilon = 1e-15
y_pred = np.clip(y_pred, epsilon, 1 - epsilon)

# Softmax数值稳定性
z_max = np.max(z, axis=1, keepdims=True)
exp_z = np.exp(z - z_max)
```

### 8.3 除零保护

```python
# 标准化
self.std[self.std == 0] = 1.0

# 评估指标
if tp + fp == 0:
    return 0.0
if tp + fn == 0:
    return 0.0
```

## 9. 扩展性设计

### 9.1 添加新优化器

```python
class NewOptimizer(BaseOptimizer):
    """新优化器"""

    def fit(self, X, y):
        # 实现新的优化算法
        ...
        return self
```

### 9.2 添加新正则化

```python
class NewRegularization:
    """新正则化"""

    def __init__(self, lambda_param):
        self.lambda_param = lambda_param

    def penalty(self, weights):
        # 计算正则化惩罚
        ...

    def gradient(self, weights):
        # 计算正则化梯度
        ...
```

### 9.3 添加新评估指标

```python
def new_metric(y_true, y_pred):
    """新评估指标"""
    # 实现新指标
    ...
    return score
```

## 10. 部署设计

### 10.1 依赖管理

```
# requirements.txt
numpy>=1.19.0
pytest>=6.0.0
```

### 10.2 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 10.3 运行方式

```bash
# 运行主程序
python main.py

# 运行示例
python examples/spam_classification.py

# 运行测试
pytest tests/ -v
```
