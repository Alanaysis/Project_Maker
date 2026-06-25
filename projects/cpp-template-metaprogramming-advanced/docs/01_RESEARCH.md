# 01_RESEARCH.md - 市场调研

## 高级模板技术应用

### 1. 行业应用现状

#### 数值计算库
- **Eigen**: 大量使用表达式模板优化矩阵运算
- **Blitz++**: 表达式模板的先驱
- **xtensor**: 类 NumPy 的 C++ 数组库

#### 游戏引擎
- **Unreal Engine**: 使用策略类配置内存管理
- **Unity (DOTS)**: 使用模板元编程实现 ECS
- **自定义引擎**: CRTP 用于组件系统

#### 嵌入式系统
- **编译期计算**: 减少运行时开销
- **类型安全**: 编译期错误检查
- **零开销抽象**: 策略类替代虚函数

#### 金融系统
- **编译期单位检查**: 防止货币计算错误
- **类型安全的计算**: 避免隐式转换

### 2. 开源项目案例

#### Boost 库
- `boost::mpl`: 模板元编程库
- `boost::hana`: 现代元编程库
- `boost::units`: 类型安全的单位系统

#### 标准库
- `std::tuple`: 类型列表的实现
- `std::variant`: 类型安全的联合体
- `std::optional`: 可选值
- `<type_traits>`: 类型特征库

#### 实际项目
- **LLVM/Clang**: 使用模板元编程优化编译器
- **Folly (Facebook)**: 大量模板元编程技巧
- **Abseil (Google)**: 现代 C++ 工具库

### 3. 技术趋势

#### C++20 带来的变化
- **Concepts**: 替代复杂的 SFINAE
- **Ranges**: 函数式编程风格
- **Modules**: 改善编译速度
- `constexpr` 扩展: 更多编译期计算

#### 未来方向
- 编译期反射 (Reflection)
- 编译期代码生成
- 更强大的 `constexpr`

## 实际项目案例

### 案例 1: Eigen 矩阵库
```cpp
// 表达式模板避免临时对象
Matrix3d a, b, c, d;
d = a + b + c;  // 不创建临时矩阵
```

### 案例 2: 单位系统
```cpp
// 编译期单位检查
auto distance = 100.0_m;
auto time = 9.58_s;
auto speed = distance / time;  // 自动推导单位
auto error = distance + time;  // 编译错误！
```

### 案例 3: 策略化容器
```cpp
// 不同配置的容器
using SafeVector = Vector<int, ThrowBoundsCheck>;
using FastVector = Vector<int, NoBoundsCheck>;
using ThreadSafeVector = Vector<int, MutexLocking>;
```

### 案例 4: 编译期序列化
```cpp
// 自动序列化
struct Person { string name; int age; };
auto json = serialize(person);  // 编译期生成
```

## 学习资源

### 书籍
1. 《C++ Templates: The Complete Guide》2nd Edition
2. 《Modern C++ Design》Andrei Alexandrescu
3. 《C++ Template Metaprogramming》David Abrahams
4. 《Effective Modern C++》Scott Meyers

### 在线资源
- CppCon 会议视频
- C++ Reference
- Stack Overflow C++ 标签
- Reddit r/cpp

### 实践项目
- 实现自己的 `tuple`
- 实现编译期正则引擎
- 实现类型安全的 ORM
- 实现物理单位库
