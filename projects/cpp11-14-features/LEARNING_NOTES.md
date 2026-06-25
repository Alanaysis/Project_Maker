# C++11/14 新特性学习笔记

## 1. 移动语义和右值引用

### 1.1 核心概念

**左值（lvalue）**：有名字、可取地址的表达式
```cpp
int x = 42;    // x 是左值
int& ref = x;  // ref 是左值引用
```

**右值（rvalue）**：临时的、即将销毁的表达式
```cpp
int&& rref = 42;      // 42 是右值
int&& rref2 = x + 1;  // x + 1 是右值
```

**右值引用**：绑定到右值的引用，使用 `&&` 声明
```cpp
void process(int&& arg) {
    // arg 绑定到右值
}
```

### 1.2 移动语义

**移动构造函数**：
```cpp
class Buffer {
    int* data_;
    size_t size_;

public:
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
};
```

**移动赋值运算符**：
```cpp
Buffer& operator=(Buffer&& other) noexcept {
    if (this != &other) {
        delete[] data_;
        data_ = other.data_;
        size_ = other.size_;
        other.data_ = nullptr;
        other.size_ = 0;
    }
    return *this;
}
```

### 1.3 std::move

`std::move` 将左值转换为右值引用：
```cpp
std::string s1 = "Hello";
std::string s2 = std::move(s1);  // s1 被移动到 s2
// s1 现在处于有效但未指定的状态
```

### 1.4 完美转发

`std::forward` 保持参数的值类别：
```cpp
template<typename T>
void wrapper(T&& arg) {
    target(std::forward<T>(arg));
}
```

### 1.5 关键要点

1. 移动语义避免不必要的拷贝
2. `noexcept` 标记很重要，STL 容器会优先使用移动
3. 移动后的对象处于有效但未指定的状态
4. `std::move` 不移动任何东西，只是转换类型
5. 完美转发保持参数的值类别

## 2. Lambda 表达式

### 2.1 基本语法

```cpp
[capture](params) -> return_type { body }
```

**示例**：
```cpp
auto add = [](int a, int b) -> int { return a + b; };
auto result = add(3, 4);  // 7
```

### 2.2 捕获列表

| 捕获方式 | 语法 | 说明 |
|---------|------|------|
| 值捕获 | `[x]` | 拷贝外部变量 |
| 引用捕获 | `[&x]` | 引用外部变量 |
| 隐式值捕获 | `[=]` | 拷贝所有外部变量 |
| 隐式引用捕获 | `[&]` | 引用所有外部变量 |
| 混合捕获 | `[=, &x]` | 值捕获为主，x 引用捕获 |

### 2.3 泛型 Lambda（C++14）

```cpp
auto generic_add = [](auto a, auto b) { return a + b; };
generic_add(3, 4);           // 7
generic_add(3.14, 2.86);     // 6.0
generic_add("Hello", "World"); // "HelloWorld"
```

### 2.4 Lambda 与 STL 算法

```cpp
std::vector<int> vec = {5, 2, 8, 1, 9};

// 排序
std::sort(vec.begin(), vec.end(), [](int a, int b) {
    return a < b;
});

// 查找
auto it = std::find_if(vec.begin(), vec.end(), [](int n) {
    return n > 5;
});

// 转换
std::transform(vec.begin(), vec.end(), vec.begin(), [](int n) {
    return n * n;
});
```

### 2.5 关键要点

1. Lambda 是匿名函数对象
2. 捕获列表决定如何访问外部变量
3. 值捕获是只读的，引用捕获可修改
4. 泛型 Lambda 使用 `auto` 参数
5. Lambda 可以作为函数参数传递

## 3. 智能指针

### 3.1 unique_ptr

**独占所有权**：
```cpp
auto ptr = std::make_unique<int>(42);
auto ptr2 = std::move(ptr);  // 所有权转移
// ptr 现在为空
```

**特点**：
- 不可拷贝，只能移动
- 自动释放资源
- 零开销（与裸指针相同）

### 3.2 shared_ptr

**共享所有权**：
```cpp
auto ptr1 = std::make_shared<int>(42);
auto ptr2 = ptr1;  // 引用计数 +1
// 两者共享同一资源
```

**特点**：
- 引用计数管理
- 可拷贝
- 线程安全的引用计数

### 3.3 weak_ptr

**打破循环引用**：
```cpp
std::shared_ptr<Node> node1 = std::make_shared<Node>();
std::weak_ptr<Node> weak = node1;

if (auto locked = weak.lock()) {
    // 使用 locked
}
```

**特点**：
- 不增加引用计数
- 需要 `lock()` 获取 `shared_ptr`
- 用于打破循环引用

### 3.4 自定义删除器

```cpp
auto deleter = [](FILE* fp) {
    if (fp) fclose(fp);
};

std::unique_ptr<FILE, decltype(deleter)> fp(
    fopen("file.txt", "r"), deleter);
```

### 3.5 关键要点

1. 优先使用 `unique_ptr`
2. 只在需要共享所有权时使用 `shared_ptr`
3. 使用 `weak_ptr` 打破循环引用
4. 使用 `make_unique` 和 `make_shared`
5. 不要混用裸指针和智能指针

## 4. 并发编程

### 4.1 std::thread

```cpp
std::thread t([]() {
    // 线程函数
});
t.join();  // 等待线程完成
```

### 4.2 std::mutex

```cpp
std::mutex mtx;
{
    std::lock_guard<std::mutex> lock(mtx);
    // 临界区
}
```

### 4.3 std::condition_variable

```cpp
std::condition_variable cv;
std::mutex mtx;
bool ready = false;

// 等待线程
std::unique_lock<std::mutex> lock(mtx);
cv.wait(lock, [&]{ return ready; });

// 通知线程
{
    std::lock_guard<std::mutex> lock(mtx);
    ready = true;
}
cv.notify_one();
```

### 4.4 std::future 和 std::promise

```cpp
std::promise<int> promise;
std::future<int> future = promise.get_future();

std::thread t([&promise]() {
    promise.set_value(42);
});

int result = future.get();  // 42
```

### 4.5 std::async

```cpp
auto future = std::async(std::launch::async, []() {
    return 42;
});

int result = future.get();  // 42
```

### 4.6 关键要点

1. 使用 RAII 管理锁（`lock_guard`、`unique_lock`）
2. 避免死锁：按固定顺序获取锁
3. 使用条件变量进行线程间通信
4. 使用 `std::async` 简化异步编程
5. 使用原子操作避免数据竞争

## 5. 可变参数模板

### 5.1 基本语法

```cpp
template<typename... Args>
void print(Args... args) {
    // 使用 args...
}
```

### 5.2 参数包展开

**递归展开**：
```cpp
void print() {}  // 终止条件

template<typename T, typename... Args>
void print(T first, Args... rest) {
    std::cout << first << " ";
    print(rest...);
}
```

**折叠表达式（C++17）**：
```cpp
template<typename... Args>
void print(Args... args) {
    (std::cout << ... << args) << std::endl;
}
```

### 5.3 完美转发

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> make_unique_custom(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
```

### 5.4 关键要点

1. 参数包 `Args...` 包含任意数量的参数
2. `sizeof...(args)` 获取参数数量
3. 使用递归或折叠表达式展开参数包
4. 完美转发保持参数的值类别
5. 可变参数模板用于实现通用容器和函数

## 6. constexpr

### 6.1 基本用法

```cpp
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int fact5 = factorial(5);  // 编译期计算
```

### 6.2 C++14 放宽

```cpp
constexpr int fibonacci(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; ++i) {
        int temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}
```

### 6.3 constexpr 类

```cpp
class Point {
    int x_, y_;

public:
    constexpr Point(int x, int y) : x_(x), y_(y) {}
    constexpr int x() const { return x_; }
    constexpr int y() const { return y_; }
};
```

### 6.4 关键要点

1. `constexpr` 函数可以在编译期计算
2. C++14 放宽了 `constexpr` 函数的限制
3. `constexpr` 类可以在编译期创建和操作
4. `static_assert` 用于编译期断言
5. `constexpr` 提升运行时性能

## 7. auto 和 decltype

### 7.1 auto 类型推导

```cpp
auto i = 42;           // int
auto d = 3.14;         // double
auto s = std::string("Hello");  // std::string
```

**注意**：`auto` 去除引用和顶层 `const`

### 7.2 decltype 类型推导

```cpp
int x = 42;
const int& cref = x;

decltype(x) a = x;      // int
decltype(cref) b = x;    // const int&
```

**注意**：`decltype` 保留引用和 `const`

### 7.3 返回类型后置

```cpp
template<typename T, typename U>
auto add(T t, U u) -> decltype(t + u) {
    return t + u;
}
```

### 7.4 关键要点

1. `auto` 简化类型声明
2. `decltype` 获取表达式的类型
3. `auto` 去除引用和 `const`，`decltype` 保留
4. 返回类型后置用于模板函数
5. C++14 支持 `auto` 返回类型推导

## 8. 范围 for 循环

### 8.1 基本语法

```cpp
std::vector<int> vec = {1, 2, 3, 4, 5};
for (int val : vec) {
    std::cout << val << " ";
}
```

### 8.2 引用遍历

```cpp
for (auto& val : vec) {
    val *= 2;  // 修改原数据
}
```

### 8.3 自定义容器

```cpp
class MyContainer {
    std::vector<int> data_;

public:
    auto begin() { return data_.begin(); }
    auto end() { return data_.end(); }
};
```

### 8.4 关键要点

1. 范围 for 简化容器遍历
2. 使用 `auto&` 避免拷贝
3. 使用 `const auto&` 进行只读遍历
4. 自定义容器需要提供 `begin()` 和 `end()`
5. 编译器将范围 for 转换为普通 for 循环

## 9. 初始化列表

### 9.1 统一初始化

```cpp
int x{42};
std::vector<int> vec{1, 2, 3, 4, 5};
std::map<std::string, int> map{{"one", 1}, {"two", 2}};
```

### 9.2 std::initializer_list

```cpp
class MyVector {
    std::vector<int> data_;

public:
    MyVector(std::initializer_list<int> init) : data_(init) {}
};

MyVector vec = {1, 2, 3, 4, 5};
```

### 9.3 聚合初始化

```cpp
struct Point {
    int x;
    int y;
    int z;
};

Point p = {1, 2, 3};
```

### 9.4 关键要点

1. 统一初始化语法使用花括号 `{}`
2. `std::initializer_list` 用于接受初始化列表
3. 聚合初始化用于简单结构体
4. 初始化列表防止窄化转换
5. `auto` 推导初始化列表为 `std::initializer_list`

## 10. 学习建议

### 10.1 学习顺序

1. **基础语法**：auto、范围 for、初始化列表
2. **核心特性**：右值引用、移动语义、完美转发
3. **函数式编程**：Lambda 表达式
4. **资源管理**：智能指针
5. **并发编程**：线程、互斥锁、条件变量
6. **高级特性**：可变参数模板、constexpr

### 10.2 实践建议

1. **多写代码**：每个特性都写示例
2. **阅读源码**：学习标准库实现
3. **参与项目**：在实际项目中使用新特性
4. **阅读书籍**：《Effective Modern C++》
5. **关注社区**：CppCon 演讲、博客文章

### 10.3 常见陷阱

1. **移动后使用**：移动后的对象处于未指定状态
2. **循环引用**：使用 `shared_ptr` 导致内存泄漏
3. **数据竞争**：多线程访问共享数据
4. **窄化转换**：初始化列表中的类型转换
5. **Lambda 捕获**：值捕获 vs 引用捕获
