# 决策树 (Decision Tree)

从零实现决策树，理解信息增益。

## 项目简介

本项目是一个从零开始实现的决策树分类器，旨在帮助学习者理解决策树算法的原理和实现细节。通过本项目，您将学习到：

- 决策树的基本原理和算法
- 信息增益的计算方法
- 树的递归构建过程
- 预测功能的实现

## 功能特性

- ✅ 决策树分类器实现
- ✅ 信息增益计算
- ✅ 树的递归构建
- ✅ 预测功能
- ✅ 支持多种分裂标准（entropy/gini）
- ✅ 支持预剪枝策略
- ✅ 模型评估工具

## 项目结构

```
decision-tree/
├── README.md                    # 项目说明文档
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-ARCHITECTURE.md      # 架构设计
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/                         # 源代码目录
│   ├── __init__.py             # 包初始化
│   ├── decision_tree.py        # 决策树实现
│   ├── utils.py                # 工具函数
│   └── metrics.py              # 评估指标
├── tests/                       # 测试目录
│   ├── __init__.py             # 测试包初始化
│   ├── test_decision_tree.py   # 决策树测试
│   └── test_utils.py           # 工具函数测试
├── examples/                    # 示例目录
│   └── example_usage.py        # 使用示例
└── LEARNING_NOTES.md            # 学习笔记
```

## 快速开始

### 安装依赖

```bash
# 确保已安装Python 3.6+
pip install numpy
```

### 使用示例

```python
import numpy as np
from src.decision_tree import DecisionTreeClassifier

# 创建数据集
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([0, 0, 1, 1])

# 创建并训练决策树
dt = DecisionTreeClassifier(max_depth=3)
dt.fit(X, y)

# 预测
predictions = dt.predict(X)
print(f"预测结果: {predictions}")

# 评估
accuracy = dt.score(X, y)
print(f"准确率: {accuracy}")
```

### 运行示例

```bash
# 运行示例脚本
python examples/example_usage.py
```

## API文档

### DecisionTreeClassifier

决策树分类器类。

#### 参数

- `max_depth` (int, optional): 最大深度，默认None
- `min_samples_split` (int): 最小分裂样本数，默认2
- `min_samples_leaf` (int): 最小叶节点样本数，默认1
- `criterion` (str): 分裂标准，'entropy'或'gini'，默认'entropy'

#### 方法

- `fit(X, y)`: 训练模型
- `predict(X)`: 预测新数据
- `score(X, y)`: 计算准确率
- `get_params()`: 获取模型参数
- `print_tree()`: 打印决策树结构

### 工具函数

- `train_test_split(X, y, test_size=0.2, random_state=None)`: 划分数据集
- `accuracy_score(y_true, y_pred)`: 计算准确率
- `normalize(X)`: 数据标准化
- `check_input(X, y)`: 检查输入数据

### 评估指标

- `confusion_matrix(y_true, y_pred)`: 混淆矩阵
- `precision_score(y_true, y_pred, average='macro')`: 精确率
- `recall_score(y_true, y_pred, average='macro')`: 召回率
- `f1_score(y_true, y_pred, average='macro')`: F1分数

## 测试

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行带详细输出的测试
python -m pytest tests/ -v

# 运行带覆盖率的测试
python -m pytest tests/ --cov=src
```

### 测试覆盖率

- 语句覆盖率：>90%
- 分支覆盖率：>80%
- 函数覆盖率：100%

## 学习资源

### 文档

1. [调研文档](docs/01-RESEARCH.md) - 决策树的基本概念和原理
2. [架构设计](docs/02-ARCHITECTURE.md) - 项目的整体架构设计
3. [实现细节](docs/03-IMPLEMENTATION.md) - 核心算法的实现细节
4. [测试文档](docs/04-TESTING.md) - 测试策略和测试用例
5. [开发文档](docs/05-DEVELOPMENT.md) - 开发流程和最佳实践

### 学习笔记

- [学习笔记](LEARNING_NOTES.md) - 决策树学习过程中的心得体会

## 扩展阅读

### 相关算法

- 随机森林 (Random Forest)
- 梯度提升树 (Gradient Boosting Tree)
- XGBoost
- LightGBM

### 参考资料

- [scikit-learn决策树文档](https://scikit-learn.org/stable/modules/tree.html)
- [机器学习实战](https://book.douban.com/subject/26708119/)
- [统计学习方法](https://book.douban.com/subject/33437381/)

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

### 如何贡献

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

### 代码规范

- 遵循 PEP 8 代码规范
- 添加适当的文档字符串
- 编写测试用例

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- 感谢 scikit-learn 项目的启发
- 感谢所有贡献者的努力
- 感谢开源社区的支持

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至 [your-email@example.com]

---

**注意**：本项目仅用于学习目的，不建议在生产环境中使用。