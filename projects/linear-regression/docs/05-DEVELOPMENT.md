# 05 - 开发文档

## 开发环境

### 环境要求
- Python >= 3.8
- NumPy >= 1.20
- Matplotlib >= 3.3
- pytest >= 6.0

### 安装依赖
```bash
pip install -r requirements.txt
```

## 项目结构

```
linear-regression/
├── src/
│   ├── __init__.py              # 模块导出
│   ├── model.py                 # 回归模型（4个类）
│   ├── losses.py                # 损失函数（3个类）
│   ├── optimizers.py            # 优化算法（4个类）
│   ├── evaluation.py            # 评估指标（4个函数）
│   ├── feature_engineering.py   # 特征工程（4个类+1个函数）
│   └── utils.py                 # 工具函数
├── tests/
│   ├── test_model.py            # 模型测试
│   ├── test_losses.py           # 损失函数测试
│   ├── test_utils.py            # 工具函数测试
│   ├── test_evaluation.py       # 评估指标测试
│   └── test_feature_engineering.py  # 特征工程测试
├── examples/
│   ├── basic_example.py         # 基础示例
│   ├── regularization_example.py    # 正则化示例
│   ├── optimization_example.py      # 优化算法示例
│   ├── feature_engineering_example.py  # 特征工程示例
│   ├── house_price_prediction.py    # 房价预测
│   ├── stock_prediction.py          # 股票预测
│   └── sales_prediction.py          # 销量预测
├── docs/                        # 文档
├── requirements.txt             # 依赖
└── README.md                    # 说明文档
```

## 运行方式

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行单个测试文件
```bash
pytest tests/test_model.py -v
```

### 运行示例
```bash
python examples/basic_example.py
python examples/regularization_example.py
python examples/optimization_example.py
python examples/feature_engineering_example.py
python examples/house_price_prediction.py
python examples/stock_prediction.py
python examples/sales_prediction.py
```

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型提示
- 编写文档字符串

### 命名规范
- 类名：PascalCase (如 LinearRegression)
- 函数名：snake_case (如 compute_gradients)
- 变量名：snake_case (如 learning_rate)
- 常量名：UPPER_CASE

### 注释规范
- 每个类和方法都要有文档字符串
- 复杂逻辑添加行内注释
- 数学公式使用 LaTeX 风格

## 测试策略

### 单元测试
- 每个类独立测试
- 测试初始化、核心方法、边界条件

### 集成测试
- 测试模型训练和预测的完整流程
- 测试不同模块的协作

### 测试覆盖
目标：> 80%

```bash
pytest tests/ -v --cov=src
```

## 调试技巧

### 1. 查看训练过程
```python
model = LinearRegression(verbose=True)
model.fit(X, y)
```

### 2. 检查损失曲线
```python
import matplotlib.pyplot as plt
plt.plot(model.losses)
plt.xlabel('Iteration')
plt.ylabel('Loss')
plt.show()
```

### 3. 检查参数更新
```python
print(f"Weight history: {model.weight_history[:5]}")
print(f"Bias history: {model.bias_history[:5]}")
```

### 4. 数值梯度检查
```python
def numerical_gradient(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)
```

## 常见问题

### Q1: 学习率如何选择？
A: 从 0.01 开始，观察损失曲线。如果损失震荡，减小学习率；如果收敛太慢，增大学习率。

### Q2: 如何判断模型收敛？
A: 观察损失曲线，当损失不再明显下降时，可以认为模型收敛。

### Q3: 何时使用正则化？
A: 当训练误差低但测试误差高（过拟合）时，使用正则化。

### Q4: L1 和 L2 如何选择？
A: L1 适合特征选择（稀疏解），L2 适合防止过拟合。不确定时用 Elastic Net。

### Q5: 何时使用正规方程？
A: 特征数较少（< 10000）时，正规方程更快。特征数多时用梯度下降。

## 性能优化

1. **向量化运算**：使用 NumPy 矩阵运算代替循环
2. **批量计算**：一次计算所有样本的梯度
3. **内存优化**：避免不必要的数据复制
4. **特征缩放**：加速梯度下降收敛
