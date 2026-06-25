# 05_DEVELOPMENT.md - 开发手册

## 1. 环境配置

### 1.1 系统要求

- **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
- **Python版本**: Python 3.7+
- **内存**: 至少4GB RAM
- **磁盘空间**: 至少100MB

### 1.2 Python环境配置

#### 方法1：使用系统Python

```bash
# 检查Python版本
python --version

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 方法2：使用Anaconda

```bash
# 创建conda环境
conda create -n logistic-regression python=3.8

# 激活环境
conda activate logistic-regression

# 安装依赖
pip install -r requirements.txt
```

#### 方法3：使用pyenv

```bash
# 安装Python
pyenv install 3.8.10

# 设置本地Python版本
pyenv local 3.8.10

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 1.3 依赖说明

#### requirements.txt

```
numpy>=1.19.0
pytest>=6.0.0
```

#### 依赖说明

| 依赖 | 版本 | 用途 |
|------|------|------|
| numpy | >=1.19.0 | 数值计算 |
| pytest | >=6.0.0 | 单元测试 |

#### 可选依赖

```
matplotlib>=3.3.0  # 用于绘制图表
scikit-learn>=0.24.0  # 用于对比测试
```

### 1.4 IDE配置

#### VS Code

1. 安装Python扩展
2. 选择Python解释器
3. 配置代码格式化工具
4. 配置测试运行器

推荐扩展：
- Python
- Pylance
- Python Test Explorer
- Code Runner

#### PyCharm

1. 创建新项目
2. 配置Python解释器
3. 配置代码风格
4. 配置测试运行器

#### Jupyter Notebook

```bash
# 安装Jupyter
pip install jupyter

# 启动Jupyter
jupyter notebook
```

## 2. 项目结构

### 2.1 目录结构

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
│   ├── basic_usage.py          # 基本使用
│   ├── spam_classification.py  # 垃圾邮件分类
│   ├── disease_diagnosis.py    # 疾病诊断
│   ├── credit_scoring.py       # 信用评分
│   └── compare_sklearn.py      # 与sklearn对比
├── tests/                      # 测试代码
│   ├── test_logistic_regression.py
│   ├── test_metrics.py
│   └── __init__.py
├── docs/                       # 文档
│   ├── 01_RESEARCH.md          # 调研报告
│   ├── 02_REQUIREMENTS.md      # 需求分析
│   ├── 03_DESIGN.md            # 技术设计
│   ├── 04_PRODUCT.md           # 产品思考
│   └── 05_DEVELOPMENT.md       # 开发手册
├── main.py                     # 主入口
├── README.md                   # 项目说明
├── requirements.txt            # 依赖配置
└── LEARNING_NOTES.md           # 学习笔记
```

### 2.2 文件说明

| 文件 | 说明 |
|------|------|
| src/logistic_regression.py | 基础逻辑回归实现 |
| src/multiclass.py | 多分类策略实现 |
| src/regularization.py | 正则化实现 |
| src/metrics.py | 评估指标实现 |
| src/feature_engineering.py | 特征工程实现 |
| src/optimizers.py | 优化算法实现 |
| examples/*.py | 使用示例 |
| tests/*.py | 单元测试 |
| docs/*.md | 项目文档 |
| main.py | 主程序入口 |

## 3. 运行方式

### 3.1 运行主程序

```bash
# 进入项目目录
cd projects/logistic-regression

# 运行主程序
python main.py
```

### 3.2 运行示例

```bash
# 基本使用示例
python examples/basic_usage.py

# 垃圾邮件分类示例
python examples/spam_classification.py

# 疾病诊断示例
python examples/disease_diagnosis.py

# 信用评分示例
python examples/credit_scoring.py

# 与sklearn对比示例
python examples/compare_sklearn.py
```

### 3.3 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_logistic_regression.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=src

# 运行带详细输出的测试
pytest tests/ -v -s
```

### 3.4 运行单个模块

```bash
# 运行基础逻辑回归
python -c "from src import LogisticRegression; print('导入成功')"

# 运行多分类
python -c "from src import OneVsRestClassifier; print('导入成功')"

# 运行正则化
python -c "from src import LogisticRegressionL1; print('导入成功')"
```

## 4. 开发流程

### 4.1 代码规范

#### 命名规范

- **类名**: 使用PascalCase，如`LogisticRegression`
- **函数名**: 使用snake_case，如`compute_loss`
- **变量名**: 使用snake_case，如`learning_rate`
- **常量名**: 使用大写字母和下划线，如`MAX_ITERATIONS`

#### 注释规范

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    函数功能描述

    Parameters
    ----------
    param1 : type
        参数1的描述
    param2 : type
        参数2的描述

    Returns
    -------
    return_type
        返回值的描述

    Examples
    --------
    >>> result = function_name(1, 2)
    >>> print(result)
    3
    """
    # 实现代码
    pass
```

#### 代码风格

- 使用4个空格缩进
- 每行不超过79个字符
- 使用空行分隔函数和类
- 导入语句放在文件开头

### 4.2 版本控制

#### Git工作流

```bash
# 克隆仓库
git clone <repository-url>

# 创建功能分支
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/new-feature

# 创建Pull Request
# ...

# 合并到主分支
git checkout master
git merge feature/new-feature
```

#### 提交规范

- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建/工具相关

### 4.3 测试流程

#### 单元测试

```python
import pytest
from src import LogisticRegression

class TestLogisticRegression:
    """测试逻辑回归类"""

    def setup_method(self):
        """每个测试方法前运行"""
        self.model = LogisticRegression(learning_rate=0.1, n_iterations=100)

    def test_sigmoid(self):
        """测试Sigmoid函数"""
        import numpy as np
        z = np.array([0, 1, -1])
        result = self.model._sigmoid(z)
        assert result[0] == 0.5
        assert result[1] > 0.5
        assert result[2] < 0.5

    def test_fit(self):
        """测试模型训练"""
        import numpy as np
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 1])
        self.model.fit(X, y)
        assert self.model.weights is not None
        assert self.model.bias is not None

    def test_predict(self):
        """测试预测功能"""
        import numpy as np
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 1])
        self.model.fit(X, y)
        predictions = self.model.predict(X)
        assert len(predictions) == 3
        assert all(p in [0, 1] for p in predictions)

    def test_score(self):
        """测试准确率计算"""
        import numpy as np
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([0, 1, 1])
        self.model.fit(X, y)
        score = self.model.score(X, y)
        assert 0 <= score <= 1
```

#### 集成测试

```python
def test_full_pipeline():
    """测试完整的训练和预测流程"""
    import numpy as np
    from src import LogisticRegression, StandardScaler, train_test_split

    # 生成数据
    X = np.random.randn(100, 5)
    y = (X[:, 0] > 0).astype(int)

    # 特征缩放
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y)

    # 训练模型
    model = LogisticRegression(learning_rate=0.1, n_iterations=1000)
    model.fit(X_train, y_train)

    # 预测
    predictions = model.predict(X_test)
    score = model.score(X_test, y_test)

    # 验证结果
    assert len(predictions) == len(y_test)
    assert 0 <= score <= 1
```

### 4.4 调试技巧

#### 使用print调试

```python
def fit(self, X, y):
    """训练模型"""
    print(f"输入数据形状: X={X.shape}, y={y.shape}")
    print(f"输入数据类型: X={X.dtype}, y={y.dtype}")

    # 训练代码
    ...

    print(f"训练完成，最终权重: {self.weights}")
    print(f"最终偏置: {self.bias}")
    return self
```

#### 使用断言调试

```python
def _compute_loss(self, y_true, y_pred):
    """计算损失"""
    assert y_true.shape == y_pred.shape, "形状不匹配"
    assert np.all(y_pred >= 0) and np.all(y_pred <= 1), "概率超出范围"

    # 计算损失
    ...
```

#### 使用pdb调试

```python
import pdb

def fit(self, X, y):
    """训练模型"""
    pdb.set_trace()  # 设置断点

    # 训练代码
    ...
```

## 5. 常见问题

### 5.1 安装问题

#### Q1: pip安装失败

**问题描述**: pip install numpy失败

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 使用镜像源
pip install numpy -i https://pypi.tuna.tsinghua.edu.cn/simple

# 使用conda
conda install numpy
```

#### Q2: 虚拟环境激活失败

**问题描述**: source venv/bin/activate失败

**解决方案**:
```bash
# Linux/Mac
chmod +x venv/bin/activate
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

### 5.2 运行问题

#### Q3: 导入模块失败

**问题描述**: ModuleNotFoundError: No module named 'src'

**解决方案**:
```bash
# 确保在项目根目录运行
cd projects/logistic-regression

# 或者添加路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python main.py
```

#### Q4: 内存不足

**问题描述**: MemoryError

**解决方案**:
```python
# 减少数据量
X = X[:1000]
y = y[:1000]

# 使用小批量梯度下降
from src import MiniBatchGradientDescent
model = MiniBatchGradientDescent(batch_size=32)
```

### 5.3 测试问题

#### Q5: 测试失败

**问题描述**: pytest测试失败

**解决方案**:
```bash
# 查看详细错误信息
pytest tests/ -v -s

# 运行单个测试
pytest tests/test_logistic_regression.py::TestLogisticRegression::test_fit -v

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

### 5.4 性能问题

#### Q6: 训练速度慢

**问题描述**: 模型训练时间过长

**解决方案**:
```python
# 减少迭代次数
model = LogisticRegression(n_iterations=100)

# 使用更大学习率
model = LogisticRegression(learning_rate=0.1)

# 使用小批量梯度下降
from src import MiniBatchGradientDescent
model = MiniBatchGradientDescent(batch_size=64)

# 使用Adam优化器
from src import AdamOptimizer
model = AdamOptimizer(learning_rate=0.001)
```

## 6. 扩展开发

### 6.1 添加新算法

```python
# 在src目录下创建新文件
# src/new_algorithm.py

class NewAlgorithm:
    """新算法实现"""

    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2

    def fit(self, X, y):
        """训练模型"""
        ...
        return self

    def predict(self, X):
        """预测"""
        ...

    def score(self, X, y):
        """评估"""
        ...
```

### 6.2 添加新指标

```python
# 在src/metrics.py中添加新指标

def new_metric(y_true, y_pred):
    """
    新评估指标

    Parameters
    ----------
    y_true : ndarray
        真实标签
    y_pred : ndarray
        预测标签

    Returns
    -------
    float
        指标值
    """
    # 实现新指标
    ...
    return score
```

### 6.3 添加新示例

```python
# examples/new_example.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import LogisticRegression

def main():
    """主函数"""
    # 实现新示例
    ...

if __name__ == "__main__":
    main()
```

## 7. 部署发布

### 7.1 打包

```bash
# 创建setup.py
# ...

# 打包
python setup.py sdist bdist_wheel

# 安装
pip install dist/logistic_regression-0.1.0-py3-none-any.whl
```

### 7.2 发布到PyPI

```bash
# 安装twine
pip install twine

# 上传
twine upload dist/*
```

### 7.3 Docker部署

```dockerfile
# Dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```bash
# 构建镜像
docker build -t logistic-regression .

# 运行容器
docker run logistic-regression
```

## 8. 最佳实践

### 8.1 代码质量

- 遵循PEP 8代码规范
- 编写清晰的文档字符串
- 添加类型注解
- 编写单元测试

### 8.2 性能优化

- 使用向量化操作
- 避免不必要的循环
- 使用适当的数据结构
- 考虑内存使用

### 8.3 可维护性

- 模块化设计
- 清晰的接口定义
- 完整的文档
- 版本控制

### 8.4 协作开发

- 使用Git进行版本控制
- 编写清晰的提交信息
- 进行代码审查
- 持续集成/持续部署

## 9. 总结

本开发手册提供了逻辑回归项目的完整开发指南，包括：

1. **环境配置**: 详细的环境搭建步骤
2. **项目结构**: 清晰的目录和文件说明
3. **运行方式**: 多种运行和测试方法
4. **开发流程**: 规范的开发流程和最佳实践
5. **常见问题**: 常见问题的解决方案
6. **扩展开发**: 如何扩展项目功能
7. **部署发布**: 项目的打包和部署

通过遵循本手册，开发者可以快速上手项目开发，并保证代码质量和可维护性。
