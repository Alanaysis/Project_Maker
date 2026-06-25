# 03_DESIGN.md - 技术设计

## 文件组织

### 头文件库结构
```
include/
├── advanced_templates/     # 高级模板技术
├── compile_time/          # 编译期算法
├── type_computation/      # 类型计算
├── sfinae/                # SFINAE 与 Concepts
├── design_patterns/       # 模板设计模式
└── applications/          # 实际应用
```

### 模块依赖关系
```
type_computation (基础层)
    ↓
compile_time (算法层)
    ↓
advanced_templates (技术层)
    ↓
sfinae (检测层)
    ↓
design_patterns (模式层)
    ↓
applications (应用层)
```

## 架构设计

### 1. 类型列表架构

```cpp
// 基础类型列表
template <typename... Ts>
struct type_list {
    static constexpr std::size_t size = sizeof...(Ts);
    static constexpr bool empty = (size == 0);
};

// 操作通过独立的 trait 实现
template <typename List, typename T>
using push_back = typename push_back_impl<List, T>::type;

// 支持链式操作
using result = push_back<push_front<type_list<>, int>, double>;
```

### 2. 表达式模板架构

```cpp
// 表达式基类 (CRTP)
template <typename Derived, typename T>
class Expression {
public:
    constexpr T operator[](std::size_t i) const {
        return derived()[i];
    }
};

// 二元表达式
template <typename LHS, typename RHS, typename Op>
class BinaryExpr : public Expression<...> {
    const LHS& lhs_;
    const RHS& rhs_;
};

// 运算符返回表达式，不立即计算
template <typename L, typename R>
auto operator+(const Expression<L>& lhs, const Expression<R>& rhs) {
    return BinaryExpr<L, R, AddOp>(lhs, rhs);
}

// 赋值时才遍历计算
template <typename T, std::size_t N>
class Vector : public Expression<Vector<T, N>, T> {
    template <typename Expr>
    Vector& operator=(const Expression<Expr, T>& expr) {
        for (std::size_t i = 0; i < N; ++i) {
            data_[i] = expr[i];  // 单次遍历
        }
    }
};
```

### 3. 策略类架构

```cpp
// 主机类
template <typename T,
          template <typename> class CreationPolicy,
          template <typename> class OwnershipPolicy,
          typename ThreadingPolicy>
class SmartPtr {
    typename OwnershipPolicy<T>::storage_type pointee_;
};

// 策略类
template <typename T>
struct CreateUsingNew {
    static T* create() { return new T(); }
    static void destroy(T* ptr) { delete ptr; }
};

// 使用
using MyPtr = SmartPtr<int, CreateUsingNew, DeepCopy, SingleThreaded>;
```

### 4. 状态机架构

```cpp
// 状态定义
struct Closed : State<Closed> { static constexpr const char* name = "Closed"; };
struct Open : State<Open> { static constexpr const char* name = "Open"; };

// 转换规则
template <typename From, typename To, typename Event>
struct Transition { ... };

// 状态机
template <typename Initial, typename... Transitions>
class StateMachine {
    template <typename Event>
    void handle_event(const Event&) {
        // 编译期查找转换规则
        using target = find_transition<current_state, Event>;
        static_assert(!std::is_same_v<target, void>,
                      "Invalid transition");
    }
};
```

### 5. 单位系统架构

```cpp
// 维度定义
template <int M, int L, int T, int I, int Theta, int N, int J>
struct Dimension { ... };

// 单位定义
template <typename Dim, typename Scale = std::ratio<1>>
struct Unit { ... };

// 量（带单位的数值）
template <typename Unit, typename T = double>
class Quantity {
    T value_;
public:
    // 编译期单位检查
    template <typename OtherUnit>
    Quantity(const Quantity<OtherUnit, T>& other) {
        static_assert(std::is_same_v<dimension, OtherUnit::dimension>,
                      "Cannot convert between different dimensions");
    }
};
```

## 设计原则

### 1. 零开销抽象
- 编译期计算不在运行时产生开销
- 表达式模板避免临时对象
- 策略类避免虚函数调用

### 2. 类型安全
- 编译期类型检查
- SFINAE/Concepts 约束
- static_assert 断言

### 3. 可组合性
- Mixin 模式支持功能组合
- 策略类支持行为配置
- 类型列表支持类型组合

### 4. 可读性
- 详细中文注释
- 清晰的命名
- 分步骤实现

### 5. 可测试性
- 编译期断言验证
- 独立的测试文件
- 边界情况覆盖

## 性能考虑

### 编译时间
- 避免过深的模板递归
- 使用前向声明减少依赖
- 合理使用 `constexpr`

### 运行时性能
- 表达式模板减少内存分配
- 编译期计算移至编译时
- 内联友好的设计

### 内存使用
- 空基类优化
- 标签类型零大小
- 编译期常量不占运行时内存
