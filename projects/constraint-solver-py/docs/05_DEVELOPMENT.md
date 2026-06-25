# 开发文档

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- pytest (测试)

### 1.2 安装依赖

```bash
pip install pytest
```

### 1.3 项目结构

```
constraint-solver-py/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── variable.py
│   ├── domain.py
│   ├── constraint.py
│   ├── propagation.py
│   ├── search.py
│   └── solver.py
├── examples/               # 应用示例
│   ├── __init__.py
│   ├── sudoku.py
│   ├── n_queens.py
│   └── timetable.py
├── tests/                  # 测试代码
│   ├── __init__.py
│   ├── test_solver.py
│   └── test_applications.py
└── docs/                   # 文档
```

## 2. 编码规范

### 2.1 代码风格

- 遵循 PEP 8
- 使用 Type Hints
- 编写 Docstrings

```python
def solve(
    self,
    variables: Dict[str, Variable],
    constraints: List[Constraint],
    assignment: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """求解 CSP。

    Args:
        variables: 变量名字典
        constraints: 约束列表
        assignment: 初始赋值 (可选)

    Returns:
        完整赋值字典，或 None 表示无解
    """
    ...
```

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `CSPSolver` |
| 函数名 | snake_case | `add_variable` |
| 变量名 | snake_case | `domain_size` |
| 常量名 | UPPER_CASE | `MAX_SOLUTIONS` |
| 私有成员 | 前缀 `_` | `_variables` |

### 2.3 注释规范

```python
# 单行注释: 解释为什么
# AC-3 需要队列来管理待处理的弧

"""
多行注释: 解释复杂的算法或设计决策

AC-3 算法通过迭代地修订弧来实现弧相容。
如果某个变量的域变为空，则 CSP 无解。
"""
```

## 3. 测试指南

### 3.1 测试结构

```python
class TestCSPSolver:
    """CSP 求解器测试。"""

    def test_simple_csp(self):
        """测试简单的 CSP 问题。"""
        solver = CSPSolver()
        x = solver.add_variable("x", [1, 2, 3])
        y = solver.add_variable("y", [1, 2, 3])
        solver.add_all_different([x, y])
        result = solver.solve()
        assert result is not None
        assert result["x"] != result["y"]

    def test_no_solution(self):
        """测试无解的情况。"""
        solver = CSPSolver()
        x = solver.add_variable("x", [1])
        y = solver.add_variable("y", [1])
        solver.add_all_different([x, y])
        result = solver.solve()
        assert result is None
```

### 3.2 测试命名

- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试函数: `test_*`

### 3.3 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_solver.py -v

# 运行特定测试类
pytest tests/test_solver.py::TestCSPSolver -v

# 运行特定测试函数
pytest tests/test_solver.py::TestCSPSolver::test_simple_csp -v

# 显示覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 4. 开发流程

### 4.1 新增约束类型

1. 在 `constraint.py` 中创建新类
2. 继承 `Constraint` 基类
3. 实现 `is_satisfied()` 和 `revise()` 方法
4. 在 `solver.py` 中添加便捷方法
5. 编写测试用例

```python
class MyConstraint(Constraint):
    """自定义约束。"""

    def __init__(self, name: str, variables: Sequence[Variable]) -> None:
        super().__init__(name, variables)

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """检查约束是否满足。"""
        ...

    def revise(self, xi: Variable, xj: Variable) -> bool:
        """AC-3 修订。"""
        ...
```

### 4.2 新增应用场景

1. 在 `examples/` 目录创建新文件
2. 使用 `CSPSolver` API 建模问题
3. 实现问题特定的求解和输出
4. 编写测试用例
5. 更新 `examples/__init__.py`

### 4.3 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `test`: 测试更新
- `refactor`: 重构

示例:
```
feat(constraint): 添加 MyConstraint 约束类型

- 实现 is_satisfied() 方法
- 实现 revise() 方法
- 添加测试用例
```

## 5. 调试技巧

### 5.1 打印域状态

```python
for name, var in variables.items():
    print(f"{name}: {var.domain}")
```

### 5.2 跟踪传播

```python
ac3 = AC3()
result = ac3.propagate(variables, constraints)
print(f"AC-3 步骤数: {ac3.steps}")
print(f"传播结果: {'成功' if result else '失败'}")
```

### 5.3 可视化搜索树

```python
search = BacktrackingSearch()
result = search.solve(variables, constraints)
print(f"扩展节点数: {search.nodes_expanded}")
print(f"回溯次数: {search.backtrack_count}")
```

## 6. 性能优化

### 6.1 域表示优化

使用位集 (bit set) 表示小域:
```python
# 对于域大小 <= 64 的情况
domain_bits: int = 0b111  # 表示 {0, 1, 2}
```

### 6.2 约束图优化

使用邻接表而不是邻接矩阵:
```python
# 邻接表
neighbors: Dict[str, List[Variable]] = {...}
```

### 6.3 值选择优化

使用增量维护的域:
```python
# 而不是每次都复制域
saved_domains = {name: var.domain.copy() ...}
```

## 7. 已知问题

### 7.1 当前限制

- 不支持无限域
- 不支持全局约束的专用传播
- 不支持并行求解

### 7.2 计划改进

- 添加更多全局约束 (如 cumulative)
- 实现专用的 AllDifferent 传播
- 支持并行回溯搜索
