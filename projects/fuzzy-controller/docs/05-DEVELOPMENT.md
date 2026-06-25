# 开发文档

## 1. 开发环境设置

### 1.1 系统要求

- Python 3.8+
- pip (Python 包管理器)
- Git (版本控制)

### 1.2 依赖安装

```bash
# 进入项目目录
cd projects/fuzzy-controller

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install numpy pytest pytest-cov

# 或使用 requirements.txt
pip install -r requirements.txt
```

### 1.3 IDE 配置

推荐使用 VS Code 或 PyCharm，配置以下插件：
- Python
- Pylance
- Python Test Explorer
- Coverage Gutters

## 2. 项目结构

```
fuzzy-controller/
├── README.md                    # 项目说明
├── LEARNING_NOTES.md            # 学习笔记
├── docs/                        # 文档目录
│   ├── 01-RESEARCH.md          # 调研文档
│   ├── 02-DESIGN.md            # 设计文档
│   ├── 03-IMPLEMENTATION.md    # 实现细节
│   ├── 04-TESTING.md           # 测试文档
│   └── 05-DEVELOPMENT.md       # 开发文档
├── src/                         # 源代码
│   ├── __init__.py
│   ├── fuzzy_set.py
│   ├── fuzzifier.py
│   ├── rule_engine.py
│   ├── defuzzifier.py
│   ├── controller.py
│   └── applications.py
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── test_fuzzy_set.py
│   ├── test_fuzzifier.py
│   ├── test_rule_engine.py
│   ├── test_defuzzifier.py
│   ├── test_controller.py
│   ├── test_sugeno.py
│   └── test_applications.py
└── examples/                    # 示例代码
    └── example_usage.py
```

## 3. 开发流程

### 3.1 功能开发流程

1. **需求分析**：明确功能需求和边界条件
2. **设计**：设计接口和数据结构
3. **实现**：编写代码
4. **测试**：编写和运行测试
5. **文档**：更新文档
6. **代码审查**：提交 PR 进行审查
7. **合并**：合并到主分支

### 3.2 测试驱动开发 (TDD)

1. 编写失败的测试
2. 编写最小实现使测试通过
3. 重构代码
4. 重复

### 3.3 代码规范

- 遵循 PEP 8 代码规范
- 使用类型注解
- 编写详细的文档字符串
- 保持函数简短（<50行）

## 4. 代码风格

### 4.1 命名规范

- **类名**：使用 PascalCase
  ```python
  class FuzzySet:
      pass
  ```

- **函数/方法名**：使用 snake_case
  ```python
  def calculate_membership(self, x):
      pass
  ```

- **常量**：使用 UPPER_SNAKE_CASE
  ```python
  MAX_ITERATIONS = 100
  ```

- **私有方法**：使用下划线前缀
  ```python
  def _internal_method(self):
      pass
  ```

### 4.2 文档字符串

```python
def fuzzify(self, crisp_inputs: Dict[str, float]) -> Dict[str, Dict[str, float]]:
    """
    模糊化精确输入

    参数:
        crisp_inputs: 精确输入值
            格式: {变量名: 精确值}

    返回:
        模糊化结果
            格式: {变量名: {模糊集合名: 隶属度}}

    异常:
        ValueError: 当输入变量未定义时
    """
    pass
```

### 4.3 类型注解

```python
from typing import Dict, List, Tuple, Union

def control(
    self,
    crisp_inputs: Dict[str, float],
    output_x_ranges: Dict[str, Tuple[float, float]],
    num_points: int = 100
) -> Dict[str, float]:
    pass
```

## 5. 调试技巧

### 5.1 使用 print 调试

```python
def control(self, crisp_inputs):
    print(f"输入: {crisp_inputs}")

    fuzzy_inputs = self.fuzzifier.fuzzify(crisp_inputs)
    print(f"模糊化: {fuzzy_inputs}")

    # ...
```

### 5.2 使用 pdb 调试

```python
import pdb

def control(self, crisp_inputs):
    pdb.set_trace()  # 断点
    # ...
```

### 5.3 使用 logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def control(self, crisp_inputs):
    logger.debug(f"输入: {crisp_inputs}")
    # ...
```

### 5.4 使用 control_step_by_step

```python
results = controller.control_step_by_step({'temperature': 25})

# 查看每一步的结果
for step, data in results.items():
    print(f"\n{step}:")
    print(data)
```

## 6. 性能优化

### 6.1 NumPy 向量化

```python
# 不推荐：使用循环
result = []
for x in inputs:
    result.append(membership_function(x))

# 推荐：使用向量化
result = membership_function(inputs)
```

### 6.2 避免重复计算

```python
# 不推荐
for rule in rules:
    activation = rule.evaluate(fuzzy_inputs)  # 重复计算

# 推荐
activations = [rule.evaluate(fuzzy_inputs) for rule in rules]
```

### 6.3 使用缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def membership_function(self, x):
    # 计算密集型操作
    pass
```

## 7. 扩展开发

### 7.1 添加新的隶属函数

```python
class CustomMF(MembershipFunction):
    """自定义隶属函数"""

    def __init__(self, name: str, param1: float, param2: float):
        super().__init__(name)
        self.param1 = param1
        self.param2 = param2

    def __call__(self, x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        x = np.asarray(x, dtype=float)
        # 实现自定义逻辑
        result = ...
        return result
```

### 7.2 添加新的去模糊化方法

```python
class Defuzzifier:
    def defuzzify(self, x, mf_values):
        if self.method == 'custom':
            return self._custom_method(x, mf_values)
        # ...

    def _custom_method(self, x, mf_values):
        # 实现自定义方法
        pass
```

### 7.3 添加新的推理方法

```python
class RuleEngine:
    def infer_sugeno(self, fuzzy_inputs, output_functions):
        """Sugeno 推理方法"""
        # 实现 Sugeno 推理
        pass
```

## 8. 版本管理

### 8.1 版本号规范

使用语义化版本：MAJOR.MINOR.PATCH

- **MAJOR**：不兼容的 API 更改
- **MINOR**：向后兼容的功能添加
- **PATCH**：向后兼容的错误修复

### 8.2 Git 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- **feat**：新功能
- **fix**：错误修复
- **docs**：文档更新
- **style**：代码风格更改
- **refactor**：重构
- **test**：测试相关
- **chore**：构建/工具相关

示例：
```
feat(fuzzy-set): 添加钟形隶属函数

- 实现 BellShapedMF 类
- 添加单元测试
- 更新文档

Closes #123
```

## 9. 发布流程

### 9.1 准备发布

1. 更新版本号
2. 更新 CHANGELOG
3. 运行所有测试
4. 生成文档

### 9.2 构建和发布

```bash
# 构建包
python setup.py sdist bdist_wheel

# 上传到 PyPI
twine upload dist/*
```

## 10. 常见问题

### 10.1 导入错误

确保在项目根目录运行：
```bash
cd projects/fuzzy-controller
python -m pytest tests/
```

### 10.2 NumPy 版本问题

使用兼容的 NumPy 版本：
```bash
pip install numpy>=1.20
```

### 10.3 测试失败

检查：
1. 是否在正确的目录
2. 依赖是否安装
3. Python 版本是否兼容
