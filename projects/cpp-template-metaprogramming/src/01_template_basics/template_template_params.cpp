// =============================================================================
// template_template_params.cpp - 模板模板参数 (Template Template Parameters)
// =============================================================================
// 编译: g++ -std=c++17 -o template_template_params template_template_params.cpp
// 运行: ./template_template_params
// =============================================================================

#include <iostream>
#include <vector>
#include <list>
#include <deque>
#include <set>
#include <memory>
#include <string>
#include <type_traits>

// ---------------------------------------------------------------------------
// 1. 基本模板模板参数
// ---------------------------------------------------------------------------

// 接受一个模板（带一个类型参数）作为模板参数
template <template <typename> class Container, typename T>
class ContainerWrapper {
public:
    void add(const T& value) {
        container_.push_back(value);
    }

    void print() const {
        std::cout << "  [ContainerWrapper] Size: " << container_.size() << ", Elements: ";
        for (const auto& elem : container_) {
            std::cout << elem << " ";
        }
        std::cout << std::endl;
    }

    std::size_t size() const { return container_.size(); }

private:
    Container<T> container_;
};

// ---------------------------------------------------------------------------
// 2. 带默认模板参数的模板模板参数
// ---------------------------------------------------------------------------

// 接受带两个模板参数的容器（如 std::vector<T, Alloc>）
template <template <typename, typename> class Container,
          typename T,
          typename Allocator = std::allocator<T>>
class AllocatorAwareWrapper {
public:
    void add(const T& value) {
        container_.push_back(value);
    }

    void print() const {
        std::cout << "  [AllocatorAwareWrapper] Size: " << container_.size() << std::endl;
    }

    std::size_t size() const { return container_.size(); }

private:
    Container<T, Allocator> container_;
};

// ---------------------------------------------------------------------------
// 3. 模板模板参数用于策略选择
// ---------------------------------------------------------------------------

// 比较策略
template <typename T>
struct Ascending {
    bool operator()(const T& a, const T& b) const { return a < b; }
};

template <typename T>
struct Descending {
    bool operator()(const T& a, const T& b) const { return a > b; }
};

// 使用模板模板参数选择排序策略
template <template <typename> class Compare, typename T>
class SortedContainer {
public:
    void add(const T& value) {
        // 简单的插入排序
        auto it = data_.begin();
        while (it != data_.end() && Compare<T>()(*it, value)) {
            ++it;
        }
        data_.insert(it, value);
    }

    void print() const {
        std::cout << "  [SortedContainer] ";
        for (const auto& elem : data_) {
            std::cout << elem << " ";
        }
        std::cout << std::endl;
    }

private:
    std::vector<T> data_;
};

// ---------------------------------------------------------------------------
// 4. 模板模板参数与分配器
// ---------------------------------------------------------------------------

// 自定义分配器
template <typename T>
class LoggingAllocator {
public:
    using value_type = T;

    LoggingAllocator() = default;

    template <typename U>
    LoggingAllocator(const LoggingAllocator<U>&) {}

    T* allocate(std::size_t n) {
        std::cout << "  [Allocator] Allocating " << n * sizeof(T) << " bytes" << std::endl;
        return static_cast<T*>(::operator new(n * sizeof(T)));
    }

    void deallocate(T* p, std::size_t n) {
        std::cout << "  [Allocator] Deallocating " << n * sizeof(T) << " bytes" << std::endl;
        ::operator delete(p);
    }
};

// 使用模板模板参数接受带分配器的容器
template <template <typename, typename> class Container,
          typename T,
          typename Alloc = std::allocator<T>>
class CustomAllocatorContainer {
public:
    void add(const T& value) {
        container_.push_back(value);
    }

    void print() const {
        std::cout << "  Size: " << container_.size() << std::endl;
    }

private:
    Container<T, Alloc> container_;
};

// ---------------------------------------------------------------------------
// 5. 模板模板参数用于工厂模式
// ---------------------------------------------------------------------------

// 智能指针策略
template <typename T>
using UniquePtr = std::unique_ptr<T>;

template <typename T>
using SharedPtr = std::shared_ptr<T>;

// 工厂，使用模板模板参数选择指针类型
template <template <typename> class PointerType, typename T>
class Factory {
public:
    template <typename... Args>
    static PointerType<T> create(Args&&... args) {
        return PointerType<T>(new T(std::forward<Args>(args)...));
    }
};

// ---------------------------------------------------------------------------
// 6. 模板模板参数用于策略组合
// ---------------------------------------------------------------------------

// 日志策略
template <typename T>
struct NullLogger {
    void log(const T&) const {}
};

template <typename T>
struct ConsoleLogger {
    void log(const T& value) const {
        std::cout << "  [LOG] " << value << std::endl;
    }
};

// 验证策略
template <typename T>
struct NoValidation {
    bool validate(const T&) const { return true; }
};

template <typename T>
struct RangeValidation {
    RangeValidation(T min, T max) : min_(min), max_(max) {}
    bool validate(const T& value) const {
        return value >= min_ && value <= max_;
    }
private:
    T min_, max_;
};

// 组合多个策略
template <typename T,
          template <typename> class Logger = NullLogger,
          template <typename> class Validator = NoValidation>
class PolicyBasedContainer {
public:
    bool add(const T& value) {
        Validator<T> validator;
        if (!validator.validate(value)) {
            Logger<T> logger;
            logger.log("Validation failed for: " + std::to_string(value));
            return false;
        }
        data_.push_back(value);
        Logger<T> logger;
        logger.log("Added: " + std::to_string(value));
        return true;
    }

    void print() const {
        std::cout << "  [PolicyBasedContainer] Size: " << data_.size() << std::endl;
    }

private:
    std::vector<T> data_;
};

// ---------------------------------------------------------------------------
// 7. 模板模板参数与类型萃取
// ---------------------------------------------------------------------------

// 检查是否为某种容器
template <typename T>
struct is_vector : std::false_type {};

template <typename T, typename A>
struct is_vector<std::vector<T, A>> : std::true_type {};

template <typename T>
constexpr bool is_vector_v = is_vector<T>::value;

// 通用容器检测
template <typename T>
struct is_container {
private:
    template <typename U>
    static auto test(int) -> decltype(
        std::declval<U>().begin(),
        std::declval<U>().end(),
        std::declval<U>().size(),
        std::true_type{});

    template <typename>
    static std::false_type test(...);

public:
    static constexpr bool value = decltype(test<T>(0))::value;
};

template <typename T>
constexpr bool is_container_v = is_container<T>::value;

// ---------------------------------------------------------------------------
// 8. 递归模板模板参数
// ---------------------------------------------------------------------------

// 嵌套容器
template <template <typename> class Outer,
          template <typename> class Inner,
          typename T>
class NestedContainer {
public:
    void add_group() {
        outer_.push_back(Inner<T>());
    }

    void add_to_last(const T& value) {
        if (!outer_.empty()) {
            outer_.back().push_back(value);
        }
    }

    void print() const {
        std::cout << "  [NestedContainer] Groups: " << outer_.size() << std::endl;
        for (std::size_t i = 0; i < outer_.size(); ++i) {
            std::cout << "    Group " << i << ": ";
            for (const auto& elem : outer_[i]) {
                std::cout << elem << " ";
            }
            std::cout << std::endl;
        }
    }

private:
    Outer<Inner<T>> outer_;
};

// ---------------------------------------------------------------------------
// 9. 模板模板参数用于类型转换
// ---------------------------------------------------------------------------

// 类型映射
template <typename T>
struct AddConst {
    using type = const T;
};

template <typename T>
struct AddPointer {
    using type = T*;
};

// 使用模板模板参数进行批量类型转换
template <template <typename> class Transform, typename... Types>
struct TransformAll;

template <template <typename> class Transform, typename T, typename... Rest>
struct TransformAll<Transform, T, Rest...> {
    using first = typename Transform<T>::type;
    // 简化：只转换第一个类型
};

// ---------------------------------------------------------------------------
// 10. 实际应用：插件系统
// ---------------------------------------------------------------------------

// 插件接口
template <typename T>
struct Plugin {
    virtual ~Plugin() = default;
    virtual void process(T& data) = 0;
    virtual std::string name() const = 0;
};

// 插件管理器，使用模板模板参数选择容器
template <template <typename> class Container, typename T>
class PluginManager {
public:
    void register_plugin(std::unique_ptr<Plugin<T>> plugin) {
        std::cout << "  Registering plugin: " << plugin->name() << std::endl;
        plugins_.push_back(std::move(plugin));
    }

    void process_all(T& data) {
        for (auto& plugin : plugins_) {
            plugin->process(data);
        }
    }

private:
    Container<std::unique_ptr<Plugin<T>>> plugins_;
};

// 示例插件
class DoublePlugin : public Plugin<int> {
public:
    void process(int& data) override { data *= 2; }
    std::string name() const override { return "DoublePlugin"; }
};

class IncrementPlugin : public Plugin<int> {
public:
    void process(int& data) override { data += 1; }
    std::string name() const override { return "IncrementPlugin"; }
};

// ---------------------------------------------------------------------------
// 主函数
// ---------------------------------------------------------------------------

int main() {
    std::cout << "=== 模板模板参数 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本模板模板参数
    std::cout << "1. 基本模板模板参数:" << std::endl;
    ContainerWrapper<std::vector, int> cw;
    cw.add(1);
    cw.add(2);
    cw.add(3);
    cw.print();
    std::cout << std::endl;

    // 2. 带分配器的模板模板参数
    std::cout << "2. 带分配器的模板模板参数:" << std::endl;
    AllocatorAwareWrapper<std::vector, int> aaw;
    aaw.add(10);
    aaw.add(20);
    aaw.print();
    std::cout << std::endl;

    // 3. 策略选择
    std::cout << "3. 模板模板参数用于策略选择:" << std::endl;
    SortedContainer<Ascending, int> asc;
    asc.add(3);
    asc.add(1);
    asc.add(4);
    asc.add(1);
    asc.add(5);
    asc.print();

    SortedContainer<Descending, int> desc;
    desc.add(3);
    desc.add(1);
    desc.add(4);
    desc.add(1);
    desc.add(5);
    desc.print();
    std::cout << std::endl;

    // 4. 自定义分配器
    std::cout << "4. 自定义分配器:" << std::endl;
    CustomAllocatorContainer<std::vector, int, LoggingAllocator<int>> cac;
    cac.add(1);
    cac.add(2);
    cac.print();
    std::cout << std::endl;

    // 5. 工厂模式
    std::cout << "5. 工厂模式:" << std::endl;
    auto unique = Factory<UniquePtr, std::string>::create("hello");
    auto shared = Factory<SharedPtr, std::string>::create("world");
    std::cout << "  unique: " << *unique << std::endl;
    std::cout << "  shared: " << *shared << std::endl;
    std::cout << std::endl;

    // 6. 策略组合
    std::cout << "6. 策略组合:" << std::endl;
    PolicyBasedContainer<int, ConsoleLogger, NoValidation> pbc;
    pbc.add(42);
    pbc.add(100);
    pbc.print();
    std::cout << std::endl;

    // 7. 类型萃取
    std::cout << "7. 模板模板参数与类型萃取:" << std::endl;
    std::cout << "vector<int> is_vector: " << is_vector_v<std::vector<int>> << std::endl;
    std::cout << "list<int> is_vector: " << is_vector_v<std::list<int>> << std::endl;
    std::cout << "vector<int> is_container: " << is_container_v<std::vector<int>> << std::endl;
    std::cout << "int is_container: " << is_container_v<int> << std::endl;
    std::cout << std::endl;

    // 8. 嵌套容器
    std::cout << "8. 嵌套容器:" << std::endl;
    NestedContainer<std::vector, std::vector, int> nc;
    nc.add_group();
    nc.add_to_last(1);
    nc.add_to_last(2);
    nc.add_group();
    nc.add_to_last(3);
    nc.add_to_last(4);
    nc.print();
    std::cout << std::endl;

    // 10. 插件系统
    std::cout << "10. 插件系统:" << std::endl;
    PluginManager<std::vector, int> pm;
    pm.register_plugin(std::make_unique<DoublePlugin>());
    pm.register_plugin(std::make_unique<IncrementPlugin>());

    int value = 5;
    std::cout << "  Before: " << value << std::endl;
    pm.process_all(value);
    std::cout << "  After: " << value << std::endl;
    std::cout << std::endl;

    std::cout << "=== 模板模板参数演示完成 ===" << std::endl;
    return 0;
}
