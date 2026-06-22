# 05 - 开发文档

## 开发环境

### 环境要求
- Python >= 3.8
- NumPy >= 1.20
- Matplotlib >= 3.3

### 安装依赖
```bash
pip install -r requirements.txt
```

## 项目结构

```
linear-regression/
├── src/
│   ├── __init__.py
│   ├── model.py          # 线性回归模型
│   ├── losses.py         # 损失函数
│   └── utils.py          # 工具函数
├── tests/
│   ├── test_model.py     # 模型测试
│   └── test_losses.py    # 损失函数测试
├── examples/
│   └── basic_example.py  # 基础示例
├── docs/                 # 文档
├── requirements.txt      # 依赖
└── README.md             # 说明文档
```

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型提示
- 编写文档字符串

### 命名规范
- 类名：PascalCase
- 函数名：snake_case
- 变量名：snake_case
- 常量名：UPPER_CASE

### 注释规范
- 每个类和方法都要有文档字符串
- 复杂逻辑添加行内注释
- 使用中英文混合注释

## 测试策略

### 单元测试
```python
# test_model.py
def test_model_initialization():
    model = LinearRegression(learning_rate=0.01, n_iterations=100)
    assert model.learning_rate == 0.01
    assert model.n_iterations == 100

def test_model_fit():
    model = LinearRegression(learning_rate=0.01, n_iterations=100)
    X = np.array([[1], [2], [3]])
    y = np.array([2, 4, 6])
    model.fit(X, y)
    assert model.weights is not None
    assert model.bias is not None

def test_model_predict():
    model = LinearRegression(learning_rate=0.01, n_iterations=100)
    X_train = np.array([[1], [2], [3]])
    y_train = np.array([2, 4, 6])
    model.fit(X_train, y_train)

    X_test = np.array([[4]])
    y_pred = model.predict(X_test)
    assert abs(y_pred[0] - 8) < 0.1
```

### 测试覆盖率
目标：> 80%

运行测试：
```bash
pytest tests/ -v --cov=src
```

## 发布流程

1. **代码审查**
   - 检查代码风格
   - 验证测试通过
   - 确认文档完整

2. **版本发布**
   - 更新版本号
   - 创建 Git 标签
   - 发布到 PyPI（可选）

## 调试技巧

### 1. 查看训练过程
```python
# 打印每 100 次迭代的损失
for i in range(n_iterations):
    if i % 100 == 0:
        print(f"Iteration {i}, Loss: {loss}")
```

### 2. 可视化调试
```python
# 绘制损失曲线
import matplotlib.pyplot as plt
plt.plot(losses)
plt.xlabel('Iteration')
plt.ylabel('Loss')
plt.show()
```

### 3. 检查梯度
```python
# 数值梯度检查
def numerical_gradient(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)
```

## 常见问题

### Q1: 学习率如何选择？
A: 从 0.01 开始，观察损失曲线。如果损失震荡，减小学习率；如果收敛太慢，增大学习率。

### Q2: 如何判断模型收敛？
A: 观察损失曲线，当损失不再明显下降时，可以认为模型收敛。

### Q3: 如何处理多特征？
A: 使用矩阵运算，X 的形状为 (n_samples, n_features)。

## 性能优化

1. **向量化运算**：使用 NumPy 矩阵运算代替循环
2. **批量计算**：一次计算所有样本的梯度
3. **内存优化**：避免不必要的数据复制

## 扩展计划

### 短期（1-2周）
- [ ] 添加批量梯度下降
- [ ] 支持多特征
- [ ] 添加更多可视化

### 中期（1-2月）
- [ ] 添加正则化
- [ ] 支持在线学习
- [ ] 添加交叉验证

### 长期（3-6月）
- [ ] 支持非线性回归
- [ ] 集成其他优化器
- [ ] 构建完整 ML 库
