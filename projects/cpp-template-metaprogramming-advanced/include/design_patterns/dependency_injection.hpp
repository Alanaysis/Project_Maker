#pragma once
/**
 * @file dependency_injection.hpp
 * @brief 依赖注入 (Dependency Injection)
 *
 * 使用模板实现编译期依赖注入，避免运行时虚函数调用。
 *
 * 核心模式：
 *   - 构造函数注入
 *   - 接口注入
 *   - 策略注入
 */

#include <iostream>
#include <string>
#include <memory>
#include <functional>
#include <unordered_map>
#include <typeindex>
#include <any>

namespace tmp {

// ============================================================================
// 1. 构造函数注入
// ============================================================================

/**
 * @brief 日志器接口
 */
struct ILogger {
    virtual ~ILogger() = default;
    virtual void log(const std::string& msg) = 0;
};

/**
 * @brief 控制台日志器
 */
struct ConsoleLogger : ILogger {
    void log(const std::string& msg) override {
        std::cout << "[Console] " << msg << std::endl;
    }
};

/**
 * @brief 空日志器
 */
struct NullLogger : ILogger {
    void log(const std::string&) override {}
};

/**
 * @brief 使用构造函数注入的服务
 */
class UserService {
    std::shared_ptr<ILogger> logger_;

public:
    // 依赖通过构造函数注入
    explicit UserService(std::shared_ptr<ILogger> logger)
        : logger_(std::move(logger)) {}

    void create_user(const std::string& name) {
        logger_->log("Creating user: " + name);
        // ... 创建用户逻辑
        logger_->log("User created successfully");
    }
};

// ============================================================================
// 2. 模板化依赖注入（编译期多态）
// ============================================================================

/**
 * @brief 模板化服务 - 依赖通过模板参数注入
 * @tparam Logger 日志器类型（编译期确定）
 */
template <typename Logger>
class TemplateUserService {
    Logger logger_;

public:
    void create_user(const std::string& name) {
        logger_.log("Creating user: " + name);
        // ... 创建用户逻辑
        logger_.log("User created successfully");
    }
};

/**
 * @brief 模板化日志器
 */
struct TemplateConsoleLogger {
    void log(const std::string& msg) {
        std::cout << "[TemplateConsole] " << msg << std::endl;
    }
};

struct TemplateNullLogger {
    void log(const std::string&) {}
};

// ============================================================================
// 3. 简单 DI 容器
// ============================================================================

/**
 * @brief 简单的依赖注入容器
 * 使用类型擦除存储服务实例
 */
class DIContainer {
    std::unordered_map<std::type_index, std::any> services_;

public:
    /**
     * @brief 注册服务实例
     */
    template <typename Interface, typename Implementation>
    void register_instance(std::shared_ptr<Implementation> impl) {
        services_[std::type_index(typeid(Interface))] = std::move(impl);
    }

    /**
     * @brief 注册服务工厂
     */
    template <typename Interface>
    void register_factory(std::function<std::shared_ptr<Interface>()> factory) {
        services_[std::type_index(typeid(Interface))] = std::move(factory);
    }

    /**
     * @brief 解析服务
     */
    template <typename Interface>
    std::shared_ptr<Interface> resolve() {
        auto it = services_.find(std::type_index(typeid(Interface)));
        if (it == services_.end()) {
            throw std::runtime_error("Service not registered");
        }

        // 尝试作为实例解析
        if (auto* ptr = std::any_cast<std::shared_ptr<Interface>>(&it->second)) {
            return *ptr;
        }

        // 尝试作为工厂解析
        if (auto* factory = std::any_cast<
                std::function<std::shared_ptr<Interface>()>>(&it->second)) {
            return (*factory)();
        }

        throw std::runtime_error("Type mismatch in DI container");
    }

    /**
     * @brief 检查服务是否已注册
     */
    template <typename Interface>
    bool is_registered() const {
        return services_.find(std::type_index(typeid(Interface))) !=
               services_.end();
    }
};

// ============================================================================
// 4. 编译期 DI 容器
// ============================================================================

/**
 * @brief 编译期依赖注入容器
 * 使用模板参数在编译期绑定依赖
 */
template <typename... Bindings>
class CompileTimeContainer {
    std::tuple<Bindings...> bindings_;

public:
    /**
     * @brief 获取指定类型的服务
     */
    template <typename Interface>
    auto resolve() {
        return std::get<Interface>(bindings_);
    }

    /**
     * @brief 获取指定类型的服务（const）
     */
    template <typename Interface>
    auto resolve() const {
        return std::get<Interface>(bindings_);
    }
};

// ============================================================================
// 5. 服务定位器模式
// ============================================================================

/**
 * @brief 服务定位器 - 全局服务注册和查找
 */
class ServiceLocator {
    static std::unordered_map<std::type_index, std::any>& services() {
        static std::unordered_map<std::type_index, std::any> s;
        return s;
    }

public:
    template <typename Interface>
    static void register_service(std::shared_ptr<Interface> impl) {
        services()[std::type_index(typeid(Interface))] = std::move(impl);
    }

    template <typename Interface>
    static std::shared_ptr<Interface> get() {
        auto it = services().find(std::type_index(typeid(Interface)));
        if (it == services().end()) {
            throw std::runtime_error("Service not found");
        }
        return std::any_cast<std::shared_ptr<Interface>>(it->second);
    }

    static void clear() {
        services().clear();
    }
};

// ============================================================================
// 6. 依赖注入的工厂模式
// ============================================================================

/**
 * @brief 工厂接口
 */
template <typename Product>
struct IFactory {
    virtual ~IFactory() = default;
    virtual std::unique_ptr<Product> create() = 0;
};

/**
 * @brief 模板化工厂 - 编译期确定产品类型
 */
template <typename Product, typename ConcreteProduct>
struct ConcreteFactory : IFactory<Product> {
    std::unique_ptr<Product> create() override {
        return std::make_unique<ConcreteProduct>();
    }
};

/**
 * @brief 使用 DI 的工厂创建器
 */
template <typename Product>
class FactoryCreator {
    std::shared_ptr<IFactory<Product>> factory_;

public:
    explicit FactoryCreator(std::shared_ptr<IFactory<Product>> factory)
        : factory_(std::move(factory)) {}

    std::unique_ptr<Product> create() {
        return factory_->create();
    }
};

}  // namespace tmp
