# 03 - 技术设计：C++ 编译期计算

## 文件组织

### 头文件（include/compile_time/）

```
include/compile_time/
├── fixed_string.hpp    # 编译期字符串
├── array.hpp           # 编译期数组
├── map.hpp             # 编译期映射
├── set.hpp             # 编译期集合
├── math.hpp            # 编译期数学函数
├── hash.hpp            # 编译期哈希
├── regex.hpp           # 编译期正则表达式
├── config.hpp          # 编译期配置解析
├── lookup.hpp          # 编译期查找表
├── unit.hpp            # 编译期单位转换
├── state_machine.hpp   # 编译期状态机
└── reflection.hpp      # 编译期反射
```

### 示例文件（examples/）

每个示例文件对应一个独立的概念或特性，文件名清晰表达其内容。

## 核心设计

### 1. fixed_string 设计

```cpp
template<std::size_t N>
struct fixed_string {
    char data[N]{};
    std::size_t size = N - 1;

    constexpr fixed_string(const char (&str)[N]) {
        for (std::size_t i = 0; i < N; ++i)
            data[i] = str[i];
    }

    constexpr char operator[](std::size_t i) const { return data[i]; }
    constexpr std::size_t length() const { return size; }

    // 用于模板参数推导
    template<std::size_t M>
    constexpr bool operator==(const fixed_string<M>& other) const {
        if constexpr (N != M) return false;
        for (std::size_t i = 0; i < N; ++i)
            if (data[i] != other.data[i]) return false;
        return true;
    }
};

// C++20 CTAD 推导指引
template<std::size_t N>
fixed_string(const char (&)[N]) -> fixed_string<N>;
```

### 2. compile_time_array 设计

```cpp
template<typename T, std::size_t N>
struct compile_time_array {
    T data[N]{};

    constexpr T& operator[](std::size_t i) { return data[i]; }
    constexpr const T& operator[](std::size_t i) const { return data[i]; }
    constexpr std::size_t size() const { return N; }

    constexpr auto begin() { return data; }
    constexpr auto end() { return data + N; }
    constexpr auto begin() const { return data; }
    constexpr auto end() const { return data + N; }

    // 编译期排序
    constexpr compile_time_array sorted() const {
        compile_time_array result = *this;
        // 插入排序（编译期友好）
        for (std::size_t i = 1; i < N; ++i) {
            T key = result.data[i];
            std::size_t j = i;
            while (j > 0 && result.data[j - 1] > key) {
                result.data[j] = result.data[j - 1];
                --j;
            }
            result.data[j] = key;
        }
        return result;
    }
};
```

### 3. compile_time_map 设计

```cpp
template<typename Key, typename Value, std::size_t N>
struct compile_time_map {
    struct entry {
        Key key;
        Value value;
    };

    entry entries[N]{};

    constexpr Value& operator[](const Key& key) {
        for (auto& e : entries)
            if (e.key == key) return e.value;
        // 编译期报错：key 不存在
        throw "Key not found";
    }

    constexpr const Value& at(const Key& key) const {
        for (const auto& e : entries)
            if (e.key == key) return e.value;
        throw "Key not found";
    }

    constexpr bool contains(const Key& key) const {
        for (const auto& e : entries)
            if (e.key == key) return true;
        return false;
    }
};
```

### 4. 编译期数学函数设计

```cpp
namespace ct_math {
    // 编译期平方根（牛顿迭代法）
    constexpr double sqrt(double x) {
        if (x < 0) return 0;  // 错误处理
        double guess = x / 2.0;
        for (int i = 0; i < 100; ++i) {
            guess = (guess + x / guess) / 2.0;
        }
        return guess;
    }

    // 编译期幂函数
    constexpr double pow(double base, int exp) {
        if (exp < 0) return 1.0 / pow(base, -exp);
        double result = 1.0;
        for (int i = 0; i < exp; ++i) {
            result *= base;
        }
        return result;
    }

    // 编译期阶乘
    constexpr unsigned long long factorial(int n) {
        unsigned long long result = 1;
        for (int i = 2; i <= n; ++i) {
            result *= i;
        }
        return result;
    }

    // 编译期正弦函数（泰勒级数）
    constexpr double sin(double x) {
        // 归一化到 [-π, π]
        while (x > 3.14159265358979323846) x -= 2 * 3.14159265358979323846;
        while (x < -3.14159265358979323846) x += 2 * 3.14159265358979323846;

        double result = 0;
        double term = x;
        for (int n = 1; n <= 20; ++n) {
            result += term;
            term *= -x * x / ((2 * n) * (2 * n + 1));
        }
        return result;
    }
}
```

### 5. 编译期状态机设计

```cpp
template<auto states, auto events, auto transitions>
struct state_machine {
    static constexpr auto current_state = states[0];  // 初始状态

    template<auto event>
    static constexpr auto process() {
        // 查找转移
        constexpr auto transition = find_transition<current_state, event>();
        return state_machine<states, events, transition.target>{};
    }
};
```

## 示例设计原则

### 1. 渐进式学习

每个示例从简单到复杂，逐步引入新概念：

```cpp
// 第一步：最简单的 constexpr 函数
constexpr int add(int a, int b) { return a + b; }

// 第二步：constexpr 变量
constexpr int result = add(3, 4);

// 第三步：constexpr 类
struct Point {
    constexpr Point(int x, int y) : x(x), y(y) {}
    constexpr int distance_squared() const { return x*x + y*y; }
    int x, y;
};

// 第四步：编译期断言验证
static_assert(add(3, 4) == 7);
static_assert(Point(3, 4).distance_squared() == 25);
```

### 2. 实际应用场景

每个概念都配合实际应用场景：

```cpp
// 不仅仅是示例，而是实际有用的功能
constexpr auto sin_table = generate_lookup_table<360>([](int deg) {
    return ct_math::sin(deg * 3.14159265358979323846 / 180.0);
});
```

### 3. 性能对比

每个重要特性都包含性能对比：

```cpp
// 编译期版本
constexpr auto compile_time_result = heavy_computation();

// 运行时版本
auto runtime_result = heavy_computation();

// 性能测试
auto start = std::chrono::high_resolution_clock::now();
for (int i = 0; i < 1000000; ++i) {
    volatile auto result = runtime_result;
}
auto end = std::chrono::high_resolution_clock::now();
```

## 错误处理策略

### 1. 编译期错误

使用 `static_assert` 和 `constexpr` 抛出异常：

```cpp
constexpr int divide(int a, int b) {
    if (b == 0) {
        throw "Division by zero";  // 编译期报错
    }
    return a / b;
}
```

### 2. 运行时错误

使用 `std::optional` 或 `std::expected`（C++23）：

```cpp
constexpr std::optional<int> safe_divide(int a, int b) {
    if (b == 0) return std::nullopt;
    return a / b;
}
```

## 测试策略

### 1. 编译期测试

使用 `static_assert` 验证编译期计算结果：

```cpp
static_assert(factorial(5) == 120);
static_assert(sqrt(4.0) == 2.0);
```

### 2. 运行时测试

使用传统的测试框架验证运行时行为：

```cpp
void test_constexpr_function() {
    constexpr auto result = factorial(10);
    assert(result == 3628800);
}
```

### 3. 性能测试

使用 `std::chrono` 测量执行时间：

```cpp
auto start = std::chrono::high_resolution_clock::now();
// ... 测试代码 ...
auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
```
