# 约束求解器 (Constraint Solver)

一个功能完整的约束满足问题 (CSP) Python 求解器，支持多种约束类型和搜索策略。

## 特性

### 约束传播
- **弧相容 (AC-3)**: 高效的弧相容算法，通过迭代修订实现域缩减
- **路径相容 (PC-2)**: 更强的相容性检查，确保三元组一致性

### 搜索策略
- **回溯搜索**: 深度优先搜索 + 回溯
- **最小剩余值 (MRV)**: 优先选择域最小的变量，减少分支
- **度启发式**: MRV 平局时选择约束最多的变量
- **最小约束值 (LCV)**: 优先尝试对邻居约束最小的值

### 约束类型
- **AllDifferent**: 所有变量取不同值
- **线性约束**: 支持 `a*x + b*y op c` 形式
- **表约束**: 通过枚举允许的元组定义约束

### 应用示例
- **数独求解**: 9x9 数独，自动行/列/宫约束
- **N 皇后问题**: 支持任意 N，可求所有解
- **排课问题**: 教师/学生组冲突约束

## 项目结构

```
constraint-solver-py/
├── src/
│   ├── __init__.py          # 包入口
│   ├── variable.py          # 变量类
│   ├── domain.py            # 域类
│   ├── constraint.py        # 约束类型
│   ├── propagation.py       # AC-3 / 路径相容
│   ├── search.py            # 回溯搜索
│   └── solver.py            # 主求解器
├── examples/
│   ├── sudoku.py            # 数独求解
│   ├── n_queens.py          # N 皇后
│   └── timetable.py         # 排课问题
├── tests/
│   ├── test_solver.py       # 核心测试
│   └── test_applications.py # 应用测试
├── docs/
│   ├── 01_RESEARCH.md       # 研究背景
│   ├── 02_REQUIREMENTS.md   # 需求分析
│   ├── 03_DESIGN.md         # 系统设计
│   ├── 04_PRODUCT.md        # 产品设计
│   └── 05_DEVELOPMENT.md    # 开发文档
└── README.md
```

## 快速开始

### 基本用法

```python
from src import CSPSolver, Variable, Domain

# 创建求解器
solver = CSPSolver()

# 添加变量
x = solver.add_variable("x", [1, 2, 3])
y = solver.add_variable("y", [1, 2, 3])
z = solver.add_variable("z", [1, 2, 3])

# 添加约束
solver.add_all_different([x, y, z])

# 求解
result = solver.solve()
print(result)  # {'x': 1, 'y': 2, 'z': 3}
```

### 数独求解

```python
from examples.sudoku import SudokuSolver

puzzle = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]

solver = SudokuSolver(puzzle)
solution = solver.solve()
print(SudokuSolver.print_board(solution))
```

### N 皇后问题

```python
from examples.n_queens import NQueensSolver

solver = NQueensSolver(8)
solution = solver.solve()
print(NQueensSolver.print_board(solution))

# 求所有解
all_solutions = solver.solve_all()
print(f"共 {len(all_solutions)} 个解")
```

## 运行示例

```bash
# 数独求解
python examples/sudoku.py

# N 皇后问题
python examples/n_queens.py

# 排课问题
python examples/timetable.py
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行核心测试
pytest tests/test_solver.py -v

# 运行应用测试
pytest tests/test_applications.py -v
```

## 算法复杂度

| 算法 | 时间复杂度 | 空间复杂度 |
|------|-----------|-----------|
| AC-3 | O(e * d³) | O(e) |
| 路径相容 | O(n³ * d³) | O(n²) |
| 回溯搜索 | O(d^n) | O(n) |

其中: n = 变量数, d = 最大域大小, e = 约束数

## 依赖

- Python 3.8+
- pytest (测试)

## License

MIT
