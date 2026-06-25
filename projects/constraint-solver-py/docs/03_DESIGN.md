# 系统设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    应用层 (Examples)                   │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐         │
│  │ Sudoku  │  │ NQueens  │  │ Timetable   │         │
│  └────┬────┘  └────┬─────┘  └──────┬──────┘         │
├───────┼────────────┼───────────────┼─────────────────┤
│       │            │               │                 │
│       └────────────┼───────────────┘                 │
│                    ▼                                 │
│            ┌──────────────┐                          │
│            │  CSPSolver   │  ← 求解器主类             │
│            └──────┬───────┘                          │
│                   │                                  │
├───────────────────┼──────────────────────────────────┤
│                   ▼         核心层 (Core)             │
│  ┌────────────────────────────────────────┐          │
│  │          BacktrackingSearch           │          │
│  │    ┌─────────┐    ┌──────────┐        │          │
│  │    │  AC-3   │    │    PC    │        │          │
│  │    └─────────┘    └──────────┘        │          │
│  └────────────────────────────────────────┘          │
│                   │                                  │
│  ┌────────────────┼────────────────────┐             │
│  │                ▼                    │             │
│  │  ┌──────────┐ ┌──────────┐ ┌──────┐│             │
│  │  │Variable  │ │ Domain   │ │Const.││             │
│  │  └──────────┘ └──────────┘ └──────┘│             │
│  └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| variable.py | 变量定义和管理 | domain.py |
| domain.py | 取值域管理 | - |
| constraint.py | 约束类型定义 | variable.py, domain.py |
| propagation.py | 约束传播算法 | variable.py, constraint.py |
| search.py | 搜索策略 | variable.py, constraint.py, propagation.py |
| solver.py | 主求解器 | 所有核心模块 |

## 2. 类设计

### 2.1 核心类图

```
┌─────────────┐     ┌─────────────┐
│   Variable  │────▶│    Domain    │
├─────────────┤     ├─────────────┤
│ name: str   │     │ _values: set│
│ domain      │     │ size        │
│ value       │     │ is_empty()  │
├─────────────┤     │ remove()    │
│ assign()    │     │ copy()      │
│ unassign()  │     └─────────────┘
│ reset()     │
└─────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│           Constraint (ABC)           │
├──────────────────────────────────────┤
│ name: str                            │
│ variables: List[Variable]            │
├──────────────────────────────────────┤
│ is_satisfied(assignment) → bool      │
│ revise(xi, xj) → bool               │
│ get_neighbors(var) → List[Variable]  │
└──────────────────────────────────────┘
        │
        ├── AllDifferentConstraint
        ├── LinearConstraint
        └── TableConstraint

┌──────────────────────────────────────┐
│           CSPSolver                  │
├──────────────────────────────────────┤
│ _variables: Dict[str, Variable]      │
│ _constraints: List[Constraint]       │
├──────────────────────────────────────┤
│ add_variable() → Variable            │
│ add_all_different() → Constraint     │
│ add_linear() → Constraint            │
│ add_table() → Constraint             │
│ solve() → Dict[str, Any]            │
│ solve_all() → List[Dict]            │
└──────────────────────────────────────┘
```

### 2.2 设计模式

**策略模式**: 约束传播和搜索策略可替换
```python
# 可配置的传播策略
solver = CSPSolver(use_ac3=True)
solver = CSPSolver(use_ac3=False)

# 可配置的值排序
search = BacktrackingSearch(use_lcv=True)
```

**组合模式**: 约束可以组合
```python
solver.add_all_different([x, y, z])
solver.add_linear([x, y], "x + y == 10")
```

## 3. 算法设计

### 3.1 AC-3 算法

```
function AC-3(csp):
    queue ← 所有弧 (Xi, Xj)
    while queue 非空:
        (Xi, Xj) ← queue.dequeue()
        if revise(Xi, Xj):
            if Xi.domain 为空:
                return false
            for Xk in Xi 的邻居 (除了 Xj):
                queue.enqueue((Xk, Xi))
    return true

function revise(Xi, Xj):
    revised ← false
    for each value in Xi.domain:
        if 没有 value' in Xj.domain 满足约束:
            Xi.domain.remove(value)
            revised ← true
    return revised
```

### 3.2 回溯搜索

```
function BACKTRACK(assignment, csp):
    if assignment 完整:
        return assignment
    
    var ← SELECT-UNASSIGNED-VARIABLE(csp)
    for each value in ORDER-DOMAIN-VALUES(var, assignment, csp):
        if value 与 assignment 一致:
            assignment[var] ← value
            saved_domains ← 保存域状态
            
            if AC-3(assignment):
                result ← BACKTRACK(assignment, csp)
                if result ≠ failure:
                    return result
            
            恢复域状态
            删除 assignment[var]
    
    return failure
```

### 3.3 MRV 启发式

```
function SELECT-UNASSIGNED-VARIABLE(csp):
    unassigned ← 所有未赋值变量
    return argmin(|var.domain| for var in unassigned)
```

## 4. 数据结构设计

### 4.1 变量存储

```python
# 使用字典存储变量，支持 O(1) 查找
variables: Dict[str, Variable] = {
    "x": Variable("x", Domain([1, 2, 3])),
    "y": Variable("y", Domain([1, 2, 3])),
}
```

### 4.2 约束存储

```python
# 使用列表存储约束
constraints: List[Constraint] = [
    AllDifferentConstraint(...),
    LinearConstraint(...),
]
```

### 4.3 域存储

```python
# 使用集合存储域值，支持 O(1) 查找和删除
class Domain:
    _values: set[Any]
```

## 5. 接口设计

### 5.1 求解器接口

```python
class CSPSolver:
    def add_variable(name: str, domain: Sequence) -> Variable
    def add_all_different(variables: Sequence[Variable]) -> Constraint
    def add_linear(variables: Sequence[Variable], expr: str) -> Constraint
    def add_table(variables: Sequence[Variable], tuples: Sequence) -> Constraint
    def solve() -> Optional[Dict[str, Any]]
    def solve_all(max_solutions: int) -> List[Dict[str, Any]]
```

### 5.2 约束接口

```python
class Constraint(ABC):
    def is_satisfied(assignment: Dict[str, Any]) -> bool
    def revise(xi: Variable, xj: Variable) -> bool
    def get_neighbors(var: Variable) -> List[Variable]
```

## 6. 错误处理

### 6.1 异常类型

```python
class CSPError(Exception): pass
class NoSolutionError(CSPError): pass
class InvalidDomainError(CSPError): pass
class InvalidConstraintError(CSPError): pass
```

### 6.2 错误处理策略

- 域为空时返回 None (无解)
- 无效输入时抛出 ValueError
- 约束冲突时在传播阶段检测
