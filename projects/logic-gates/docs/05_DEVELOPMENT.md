# 开发文档：逻辑门模拟器

## 1. 开发环境

### 1.1 环境要求

- **Python**: 3.8+
- **操作系统**: Windows, Linux, macOS
- **依赖**: 无外部依赖

### 1.2 开发工具

- **IDE**: VS Code, PyCharm, 或任何文本编辑器
- **版本控制**: Git
- **测试框架**: pytest
- **代码风格**: PEP 8

### 1.3 环境搭建

```bash
# 克隆仓库
git clone https://github.com/yourusername/logic-gates-simulator.git

# 进入项目目录
cd logic-gates-simulator

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt
```

## 2. 代码规范

### 2.1 命名规范

```python
# 类名：使用大驼峰命名法
class AndGate:
    pass

# 函数和方法：使用小写字母和下划线
def evaluate(self, *inputs):
    pass

# 常量：使用大写字母和下划线
MAX_INPUTS = 8

# 私有属性：使用下划线前缀
self._value = 0
self._history = []
```

### 2.2 文档字符串

```python
class AndGate(Gate):
    """与门

    所有输入为1时输出1。

    Truth Table:
        A | B | OUT
        0 | 0 | 0
        0 | 1 | 0
        1 | 0 | 0
        1 | 1 | 1

    Examples:
        >>> gate = AndGate()
        >>> gate.evaluate(0, 0)
        0
        >>> gate.evaluate(1, 1)
        1
    """

    def evaluate(self, *inputs: int) -> int:
        """计算AND门输出

        Args:
            *inputs: 两个输入信号

        Returns:
            int: 输出信号

        Raises:
            InvalidInputError: 输入无效
        """
        pass
```

### 2.3 类型注解

```python
from typing import List, Dict, Tuple, Optional

def evaluate(self, a: int, b: int) -> Tuple[int, int]:
    """计算半加器输出"""
    pass

def get_truth_table(self) -> List[Dict]:
    """获取真值表"""
    pass
```

## 3. 开发流程

### 3.1 功能开发流程

1. **创建分支**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **编写代码**
   - 实现功能
   - 编写测试
   - 更新文档

3. **运行测试**
   ```bash
   python -m pytest tests/
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **推送分支**
   ```bash
   git push origin feature/new-feature
   ```

6. **创建Pull Request**

### 3.2 提交规范

使用语义化提交信息：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat: add 4-bit ALU implementation
fix: correct XOR gate truth table
docs: update API documentation
test: add unit tests for counter
```

### 3.3 版本管理

使用语义化版本号：

- **主版本号**: 不兼容的API更改
- **次版本号**: 向后兼容的功能性新增
- **修订号**: 向后兼容的问题修正

示例：`1.0.0`, `1.1.0`, `1.1.1`

## 4. 代码审查

### 4.1 审查清单

- [ ] 代码符合PEP 8规范
- [ ] 所有公共方法有文档字符串
- [ ] 类型注解完整
- [ ] 测试覆盖充分
- [ ] 无硬编码值
- [ ] 错误处理完善
- [ ] 性能考虑

### 4.2 审查示例

```python
# 好的代码
class AndGate(Gate):
    """与门"""

    @property
    def name(self) -> str:
        return "AND"

    @property
    def num_inputs(self) -> int:
        return 2

    def evaluate(self, *inputs: int) -> int:
        """计算AND门输出"""
        self._validate_inputs(inputs)
        return int(all(inputs))

# 需要改进的代码
class AndGate(Gate):
    def evaluate(self, *inputs):
        if len(inputs) != 2:
            raise Exception("Wrong number of inputs")
        if inputs[0] == 1 and inputs[1] == 1:
            return 1
        else:
            return 0
```

## 5. 测试开发

### 5.1 测试编写规范

```python
class TestAndGate:
    """AND门测试"""

    def setup_method(self):
        """测试前准备"""
        self.gate = AndGate()

    def test_evaluate_00(self):
        """测试输入00"""
        assert self.gate.evaluate(0, 0) == 0

    def test_evaluate_11(self):
        """测试输入11"""
        assert self.gate.evaluate(1, 1) == 1

    def test_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(InvalidInputError):
            self.gate.evaluate(0, 2)
```

### 5.2 测试覆盖率

```bash
# 运行带覆盖率的测试
python -m pytest tests/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 5.3 测试最佳实践

1. **测试命名**: 使用描述性的测试名称
2. **测试独立**: 每个测试应该独立运行
3. **测试覆盖**: 覆盖正常路径和异常路径
4. **测试速度**: 保持测试快速运行
5. **测试维护**: 定期更新测试

## 6. 文档开发

### 6.1 文档类型

- **README.md**: 项目介绍和快速开始
- **API文档**: 详细的API说明
- **示例代码**: 使用示例
- **开发文档**: 开发指南

### 6.2 文档编写规范

```markdown
# 标题

## 二级标题

### 三级标题

正文内容。

```python
# 代码示例
def example():
    pass
```

**注意**: 重要信息。
```

### 6.3 文档更新流程

1. 更新相关文档
2. 运行测试确保代码正确
3. 提交文档更改
4. 更新版本号（如果需要）

## 7. 发布流程

### 7.1 发布准备

1. 更新版本号
2. 更新CHANGELOG.md
3. 运行所有测试
4. 构建文档

### 7.2 发布步骤

```bash
# 1. 更新版本号
# 编辑 src/__init__.py

# 2. 提交更改
git add .
git commit -m "chore: release v1.0.0"

# 3. 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 4. 推送标签
git push origin v1.0.0

# 5. 创建GitHub Release
```

### 7.3 发布后

1. 验证发布
2. 更新文档
3. 通知用户

## 8. 故障排除

### 8.1 常见问题

#### 导入错误

```python
# 错误
from gates import AndGate

# 正确
from src.gates import AndGate
```

#### 测试失败

```bash
# 运行特定测试
python -m pytest tests/test_gates.py::TestAndGate::test_evaluate_11 -v

# 查看详细错误
python -m pytest tests/test_gates.py -v --tb=long
```

#### 性能问题

```python
# 使用缓存优化
from functools import lru_cache

@lru_cache(maxsize=128)
def evaluate(self, *inputs):
    pass
```

### 8.2 调试技巧

```python
# 使用print调试
def evaluate(self, *inputs):
    print(f"Inputs: {inputs}")
    result = self._logic_func(*inputs)
    print(f"Result: {result}")
    return result

# 使用pdb调试
import pdb; pdb.set_trace()
```

### 8.3 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate(self, *inputs):
    logger.info(f"Evaluating {self.name} with inputs {inputs}")
    result = self._logic_func(*inputs)
    logger.info(f"Result: {result}")
    return result
```

## 9. 最佳实践

### 9.1 代码设计

- **单一职责**: 每个类只负责一件事
- **开闭原则**: 对扩展开放，对修改关闭
- **依赖倒置**: 依赖抽象而非具体实现

### 9.2 性能优化

- **避免重复计算**: 使用缓存
- **减少内存分配**: 复用对象
- **使用高效算法**: 选择合适的算法

### 9.3 安全考虑

- **输入验证**: 验证所有输入
- **错误处理**: 优雅处理错误
- **资源管理**: 正确释放资源

## 10. 参考资源

### 10.1 Python资源

- [Python官方文档](https://docs.python.org/3/)
- [PEP 8风格指南](https://peps.python.org/pep-0008/)
- [pytest文档](https://docs.pytest.org/)

### 10.2 数字电路资源

- [Nand2Tetris](https://www.nand2tetris.org/)
- [数字逻辑设计](https://en.wikipedia.org/wiki/Digital_logic)

### 10.3 开发工具

- [Git](https://git-scm.com/)
- [VS Code](https://code.visualstudio.com/)
- [PyCharm](https://www.jetbrains.com/pycharm/)
