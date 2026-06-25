# 03 - 实现细节

## 1. 项目结构

```
constraint-solver/
├── CMakeLists.txt              # 构建配置
├── README.md                   # 项目文档
├── include/
│   ├── geometry.h             # 几何实体定义
│   ├── constraint.h           # 约束定义
│   └── solver.h               # 求解器接口
├── src/
│   └── solver.cpp             # 求解器实现
├── tests/
│   ├── test_constraints.cpp   # 约束单元测试
│   └── test_solver.cpp        # 求解器集成测试
├── examples/
│   ├── basic_example.cpp      # 基础示例
│   ├── cad_sketch.cpp         # CAD 草图示例
│   └── tangent_demo.cpp       # 相切约束演示
└── docs/
    ├── 01-RESEARCH.md         # 研究报告
    ├── 02-DESIGN.md           # 设计文档
    ├── 03-IMPLEMENTATION.md   # 实现细节（本文件）
    ├── 04-TESTING.md          # 测试文档
    └── 05-DEVELOPMENT.md      # 开发日志
```

## 2. 核心实现

### 2.1 几何实体 (geometry.h)

#### Point2D

```cpp
struct Point2D {
    double x, y;
    int id;

    // 基本运算
    double distanceTo(const Point2D& other) const;
    double distanceSquaredTo(const Point2D& other) const;

    // 向量运算
    Point2D operator+(const Point2D& other) const;
    Point2D operator-(const Point2D& other) const;
    Point2D operator*(double scalar) const;
    double dot(const Point2D& other) const;
    double cross(const Point2D& other) const;
    double length() const;
    Point2D normalized() const;
};
```

**设计决策**：
- 使用 `double` 而非 `float` 以获得更高精度
- 提供 `distanceSquaredTo()` 避免不必要的 `sqrt` 计算
- 实现向量运算用于约束计算

#### Line2D

```cpp
struct Line2D {
    Point2D start, end;
    int id;

    Point2D direction() const;   // 方向向量
    Point2D normal() const;      // 法向量
    double length() const;       // 长度
    double angleWith(const Line2D& other) const;  // 与另一线的角度
    Point2D closestPointTo(const Point2D& p) const;  // 最近点
    double distanceToPoint(const Point2D& p) const;  // 到点的距离
};
```

**关键算法 - 点到线段距离**：

```cpp
Point2D Line2D::closestPointTo(const Point2D& p) const {
    Point2D d = direction();
    double len2 = d.dot(d);
    if (len2 < 1e-12) return start;  // 退化为点

    double t = (p - start).dot(d) / len2;
    t = std::max(0.0, std::min(1.0, t));  // 限制在线段内
    return start + d * t;
}
```

#### Circle2D

```cpp
struct Circle2D {
    Point2D center;
    double radius;
    int id;

    double area() const;
    double circumference() const;
    double distanceToPoint(const Point2D& p) const;
    bool containsPoint(const Point2D& p) const;
};
```

### 2.2 约束系统 (constraint.h)

#### 约束基类

```cpp
class Constraint {
public:
    ConstraintType type;
    std::string name;
    std::vector<int> param_indices;  // 关联的参数索引
    double target;                    // 目标值

    virtual double residual(const std::vector<double>& params) const = 0;
    virtual std::vector<double> gradient(const std::vector<double>& params) const = 0;
    virtual std::string description() const = 0;
};
```

**设计决策**：
- 使用虚函数实现多态
- `param_indices` 存储参数在全局向量中的索引
- `target` 存储约束目标值（如距离、角度）

#### 距离约束实现

```cpp
class DistanceConstraint : public Constraint {
public:
    DistanceConstraint(int p1_idx, int p2_idx, double distance) {
        type = ConstraintType::Distance;
        name = "Distance";
        param_indices = {p1_idx, p1_idx + 1, p2_idx, p2_idx + 1};
        target = distance;
    }

    double residual(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return dx * dx + dy * dy - target * target;
    }

    std::vector<double> gradient(const std::vector<double>& p) const override {
        double dx = p[param_indices[0]] - p[param_indices[2]];
        double dy = p[param_indices[1]] - p[param_indices[3]];
        return {2.0 * dx, 2.0 * dy, -2.0 * dx, -2.0 * dy};
    }
};
```

**梯度推导**：

设 f = (x1-x2)² + (y1-y2)² - d²

则：
- ∂f/∂x1 = 2(x1-x2)
- ∂f/∂y1 = 2(y1-y2)
- ∂f/∂x2 = -2(x1-x2)
- ∂f/∂y2 = -2(y1-y2)

#### 平行约束实现

```cpp
class ParallelConstraint : public Constraint {
    double residual(const std::vector<double>& p) const override {
        // 方向向量
        double dx1 = p[2] - p[0], dy1 = p[3] - p[1];
        double dx2 = p[6] - p[4], dy2 = p[7] - p[5];
        // 叉积（应为 0）
        return dx1 * dy2 - dy1 * dx2;
    }
};
```

#### 相切约束实现

```cpp
class TangentLineCircleConstraint : public Constraint {
    double residual(const std::vector<double>& p) const override {
        // 线段: (sx,sy) -> (ex,ey)
        // 圆: (cx,cy), radius r
        double dx = ex - sx, dy = ey - sy;
        double len_sq = dx * dx + dy * dy;

        // 点到直线距离（叉积公式）
        double dist = abs((cx-sx)*dy - (cy-sy)*dx) / sqrt(len_sq);

        return dist * dist - r * r;
    }
};
```

### 2.3 求解器 (solver.h / solver.cpp)

#### 参数管理

```cpp
class ConstraintSolver {
private:
    std::vector<double> params_;  // 参数向量
    std::vector<EntityInfo> entities_;  // 实体信息
    std::vector<std::unique_ptr<Constraint>> constraints_;
};
```

#### 实体创建

```cpp
int ConstraintSolver::addPoint(double x, double y) {
    int id = next_entity_id_++;
    int param_start = params_.size();

    params_.push_back(x);
    params_.push_back(y);

    entities_.push_back({EntityInfo::Point, param_start, id});
    return id;
}
```

#### 约束添加

```cpp
void ConstraintSolver::addDistance(int p1_id, int p2_id, double distance) {
    // 查找实体参数索引
    int idx1 = findParamIndex(p1_id, EntityInfo::Point);
    int idx2 = findParamIndex(p2_id, EntityInfo::Point);

    if (idx1 >= 0 && idx2 >= 0) {
        constraints_.push_back(
            std::make_unique<DistanceConstraint>(idx1, idx2, distance));
    }
}
```

#### 残差计算

```cpp
std::vector<double> ConstraintSolver::computeResiduals() const {
    std::vector<double> residuals;
    residuals.reserve(constraints_.size());

    for (const auto& c : constraints_) {
        residuals.push_back(c->residual(params_));
    }

    return residuals;
}
```

#### 雅可比矩阵计算

```cpp
std::vector<std::vector<double>> ConstraintSolver::computeJacobian() const {
    int m = constraints_.size();  // 约束数
    int n = params_.size();       // 参数数

    std::vector<std::vector<double>> J(m, std::vector<double>(n, 0.0));

    for (int i = 0; i < m; ++i) {
        auto grad = constraints_[i]->gradient(params_);
        for (size_t j = 0; j < constraints_[i]->param_indices.size(); ++j) {
            int col = constraints_[i]->param_indices[j];
            J[i][col] = grad[j];
        }
    }

    return J;
}
```

#### 线性系统求解

使用正规方程 + Tikhonov 正则化：

```cpp
bool ConstraintSolver::solveLinearSystem(
    const std::vector<std::vector<double>>& J,
    const std::vector<double>& r,
    std::vector<double>& dx) const
{
    // 构建正规方程: (J^T J + λI) dx = -J^T r
    int m = J.size(), n = J[0].size();

    // A = J^T J + λI
    std::vector<std::vector<double>> A(n, std::vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            double sum = 0.0;
            for (int k = 0; k < m; ++k) {
                sum += J[k][i] * J[k][j];
            }
            A[i][j] = sum;
        }
        A[i][i] += config_.regularization;
    }

    // b = -J^T r
    std::vector<double> b(n, 0.0);
    for (int i = 0; i < n; ++i) {
        double sum = 0.0;
        for (int k = 0; k < m; ++k) {
            sum += J[k][i] * r[k];
        }
        b[i] = -sum;
    }

    // 高斯消元求解
    return gaussianElimination(A, b, dx);
}
```

#### 主求解循环

```cpp
SolverResult ConstraintSolver::solve() {
    for (int iter = 0; iter < config_.max_iterations; ++iter) {
        // 计算残差
        auto residuals = computeResiduals();
        double norm = residualNorm(residuals);

        // 检查收敛
        if (norm < config_.tolerance) {
            return {SolverStatus::Converged, iter, norm, params_, "Converged"};
        }

        // 计算雅可比
        auto J = computeJacobian();

        // 求解线性系统
        std::vector<double> dx;
        if (!solveLinearSystem(J, residuals, dx)) {
            return {SolverStatus::SingularMatrix, iter, norm, params_, "Singular"};
        }

        // 更新参数（带阻尼）
        for (size_t i = 0; i < params_.size(); ++i) {
            params_[i] += config_.damping * dx[i];
        }
    }

    return {SolverStatus::MaxIterations, config_.max_iterations, ...};
}
```

## 3. 数值稳定性

### 3.1 正则化

使用 Tikhonov 正则化防止奇异矩阵：

```cpp
A[i][i] += config_.regularization;  // 通常 1e-12
```

### 3.2 阻尼

使用阻尼系数控制步长：

```cpp
params_[i] += config_.damping * dx[i];  // damping 通常 0.5-1.0
```

### 3.3 数值微分

对于复杂约束，使用数值微分计算梯度：

```cpp
std::vector<double> gradient(const std::vector<double>& p) const {
    std::vector<double> grad(param_indices.size(), 0.0);
    double eps = 1e-8;
    double f0 = residual(p);

    for (size_t i = 0; i < param_indices.size(); ++i) {
        std::vector<double> p_plus = p;
        p_plus[param_indices[i]] += eps;
        grad[i] = (residual(p_plus) - f0) / eps;
    }

    return grad;
}
```

### 3.4 退化检测

检测几何退化情况：

```cpp
if (len_sq < 1e-12) return start;  // 线段退化为点
if (len1 < 1e-12 || len2 < 1e-12) return 0.0;  // 零长度向量
```

## 4. 测试覆盖

### 4.1 约束测试

- 残差计算正确性
- 梯度计算正确性（与数值微分对比）
- 边界情况处理

### 4.2 求解器测试

- 简单系统求解
- 复杂系统求解
- 过度约束检测
- 收敛性验证

### 4.3 集成测试

- 矩形约束求解
- 三角形约束求解
- 圆约束求解

## 5. 已知限制

1. **初始猜测敏感**：Newton 方法对初始猜测敏感
2. **单解**：只返回一个解，可能不是用户期望的
3. **全局搜索**：没有全局优化，可能陷入局部最小
4. **3D 支持**：仅支持 2D 约束
5. **性能**：未优化大规模系统

## 6. 未来改进

1. **图分解**：利用约束图结构提高效率
2. **增量求解**：支持增量约束添加
3. **多解处理**：返回所有可能的解
4. **3D 扩展**：支持三维约束
5. **并行计算**：利用多核加速
