# 04 - 产品思考

## 学习目标

### 1. 初级目标

#### 理解 C++23 概念
- 了解 C++23 标准的重要性
- 掌握主要特性分类
- 理现代 C++ 发展趋势

#### 掌握基础特性
- 熟悉常用标准库新工具
- 了解 Ranges 基本概念
- 掌握简单的语法改进

#### 能够使用示例
- 编译运行示例代码
- 理解示例中的关键代码
- 能够修改示例进行实验

### 2. 中级目标

#### 熟练使用新特性
- 在项目中应用 C++23 特性
- 选择合适的特性解决问题
- 理解特性的适用场景

#### 理解设计原理
- 了解特性的设计动机
- 理解与 C++20 的关系
- 掌握最佳实践

#### 能够阅读文档
- 阅读 C++ 标准文档
- 理解提案内容
- 跟踪语言发展

### 3. 高级目标

#### 深入理解特性
- 掌握特性的实现细节
- 理解性能影响
- 了解边界情况

#### 能够贡献
- 参与标准讨论
- 提交 bug 报告
- 分享使用经验

#### 指导他人
- 帮助团队学习
- 编写技术文档
- 组织培训

## 关键要点

### 1. 错误处理革命

#### std::expected 的意义
- **类型安全**: 编译时检查错误处理
- **性能**: 避免异常开销
- **表达力**: 明确的函数契约
- **组合性**: 链式错误处理

#### 使用建议
```cpp
// 好的做法
std::expected<int, Error> parse(std::string_view input);

// 避免的做法
int parse(std::string_view input); // 可能抛异常
```

### 2. Ranges 范式转变

#### 声明式编程
- 描述"做什么"而非"怎么做"
- 组合简单操作
- 减少循环嵌套

#### 示例对比
```cpp
// 传统方式
std::vector<int> result;
for (auto& vec : matrix) {
    for (auto& val : vec) {
        if (val > 0) {
            result.push_back(val);
        }
    }
}

// Ranges 方式
auto result = matrix 
    | std::views::join
    | std::views::filter([](int x) { return x > 0; })
    | std::ranges::to<std::vector>();
```

### 3. 多维数据处理

#### std::mdspan 价值
- 零开销抽象
- 灵活的内存布局
- 与现有代码兼容
- 便于科学计算

#### 应用场景
- 图像处理
- 矩阵运算
- 张量计算
- 物理模拟

### 4. 协程标准化

#### std::generator 的意义
- 标准化的协程生成器
- 简化异步编程
- 提高代码可读性
- 便于组合

#### 使用场景
- 惰性计算
- 流式处理
- 状态机
- 生成器模式

### 5. 编译时计算

#### constexpr/consteval 扩展
- 更多标准库函数支持 constexpr
- consteval 强制编译期求值
- if consteval 条件编译

#### 价值
- 运行时性能提升
- 编译时错误检查
- 减少运行时依赖

## 学习路径设计

### 路径 1: 实用主义路径

**目标**: 快速上手，解决实际问题

**顺序**:
1. std::print - 最简单的改进
2. std::expected - 错误处理
3. ranges::to - 容器转换
4. ranges::enumerate - 带索引迭代
5. std::string::contains - 字符串查找

**时间**: 1-2 天

### 路径 2: Ranges 专项路径

**目标**: 掌握 Ranges 编程

**顺序**:
1. ranges::to - 基础转换
2. ranges::chunk - 分块
3. ranges::slide - 滑动窗口
4. ranges::zip - 并行迭代
5. ranges::enumerate - 带索引
6. ranges::cartesian_product - 笛卡尔积
7. views::join_with - 连接
8. views::stride - 步长

**时间**: 3-5 天

### 路径 3: 语言特性路径

**目标**: 理解语言演进

**顺序**:
1. if consteval - 编译期判断
2. constexpr 扩展 - 编译期计算
3. deducing this - 显式对象参数
4. static operator - 静态运算符
5. multidimensional subscript - 多维下标

**时间**: 2-3 天

### 路径 4: 完整学习路径

**目标**: 全面掌握 C++23

**顺序**:
1. 基础特性 (1 周)
2. 标准库特性 (1 周)
3. Ranges 特性 (1 周)
4. 高级特性 (1 周)
5. 综合实践 (1 周)

**时间**: 5 周

## 常见陷阱

### 1. 编译器支持

#### 问题
- 不同编译器支持程度不同
- 某些特性可能未完全实现

#### 解决方案
- 检查编译器版本
- 使用特性检测宏
- 提供回退方案

### 2. 性能误用

#### 问题
- Ranges 视图可能有隐藏开销
- 不当使用可能影响性能

#### 解决方案
- 理解视图的实现
- 使用基准测试
- 避免过度组合

### 3. 学习曲线

#### 问题
- 新概念需要时间理解
- 与传统 C++ 思维不同

#### 解决方案
- 循序渐进
- 多做练习
- 参考示例代码

## 最佳实践

### 1. 错误处理

```cpp
// 使用 std::expected
std::expected<int, std::string> divide(int a, int b) {
    if (b == 0) {
        return std::unexpected("Division by zero");
    }
    return a / b;
}

// 链式处理
auto result = divide(10, 2)
    .and_then([](int val) { return val * 3; });
```

### 2. Ranges 使用

```cpp
// 组合多个视图
auto result = data
    | std::views::filter(pred)
    | std::views::transform(func)
    | std::views::take(10)
    | std::ranges::to<std::vector>();
```

### 3. 编译时计算

```cpp
// 使用 constexpr
constexpr auto factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// 使用 consteval
consteval auto compile_time_check(int n) {
    if (n < 0) {
        throw "Negative value";
    }
    return n;
}
```

## 总结

C++23 是 C++ 语言现代化的重要一步。通过本项目的学习，开发者可以：

1. **掌握新特性**: 了解 C++23 的主要改进
2. **提升技能**: 学习现代 C++ 编程范式
3. **改进代码**: 应用新特性提升代码质量
4. **跟上发展**: 了解 C++ 语言演进方向

关键是要理解特性的设计动机，选择合适的场景使用，并遵循最佳实践。
