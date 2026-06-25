// =============================================================================
// dependency_injection.cpp - 依赖注入容器演示
// =============================================================================
// 编译: g++ -std=c++17 -I../../include -o dependency_injection dependency_injection.cpp
// 运行: ./dependency_injection
// =============================================================================

#include <iostream>
#include <string>
#include <memory>
#include <functional>
#include <unordered_map>
#include <typeindex>
#include <any>

// ---------------------------------------------------------------------------
// 简单的依赖注入容器
// ---------------------------------------------------------------------------
class DIContainer {
public:
    // 注册单例
    template <typename Interface, typename Implementation>
    void register_singleton() {
        auto creator = []() -> std::shared_ptr<void> {
            return std::make_shared<Implementation>();
        };
        factories_[std::type_index(typeid(Interface))] = creator;
    }

    // 注册工厂函数
    template <typename Interface>
    void register_factory(std::function<std::shared_ptr<Interface>()> factory) {
        auto creator = [factory]() -> std::shared_ptr<void> {
            return factory();
        };
        factories_[std::type_index(typeid(Interface))] = creator;
    }

    // 注册实例
    template <typename Interface>
    void register_instance(std::shared_ptr<Interface> instance) {
        instances_[std::type_index(typeid(Interface))] = instance;
    }

    // 解析依赖
    template <typename Interface>
    std::shared_ptr<Interface> resolve() {
        auto type = std::type_index(typeid(Interface));

        // 先检查已有实例
        auto it = instances_.find(type);
        if (it != instances_.end()) {
            return std::static_pointer_cast<Interface>(it->second);
        }

        // 使用工厂创建
        auto factory_it = factories_.find(type);
        if (factory_it != factories_.end()) {
            auto instance = std::static_pointer_cast<Interface>(factory_it->second());
            instances_[type] = instance;
            return instance;
        }

        throw std::runtime_error("Type not registered");
    }

private:
    std::unordered_map<std::type_index,
        std::function<std::shared_ptr<void>()>> factories_;
    std::unordered_map<std::type_index,
        std::shared_ptr<void>> instances_;
};

// ---------------------------------------------------------------------------
// 接口定义
// ---------------------------------------------------------------------------
class ILogger {
public:
    virtual ~ILogger() = default;
    virtual void log(const std::string& message) = 0;
};

class IRepository {
public:
    virtual ~IRepository() = default;
    virtual std::string find(int id) = 0;
    virtual void save(int id, const std::string& data) = 0;
};

class IService {
public:
    virtual ~IService() = default;
    virtual std::string process(int id) = 0;
};

// ---------------------------------------------------------------------------
// 具体实现
// ---------------------------------------------------------------------------
class ConsoleLogger : public ILogger {
public:
    void log(const std::string& message) override {
        std::cout << "  [LOG] " << message << std::endl;
    }
};

class MemoryRepository : public IRepository {
public:
    std::string find(int id) override {
        auto it = data_.find(id);
        if (it != data_.end()) return it->second;
        return "not found";
    }

    void save(int id, const std::string& data) override {
        data_[id] = data;
    }

private:
    std::unordered_map<int, std::string> data_;
};

class UserService : public IService {
public:
    UserService(std::shared_ptr<IRepository> repo, std::shared_ptr<ILogger> logger)
        : repo_(repo), logger_(logger) {}

    std::string process(int id) override {
        logger_->log("Processing user " + std::to_string(id));
        return repo_->find(id);
    }

private:
    std::shared_ptr<IRepository> repo_;
    std::shared_ptr<ILogger> logger_;
};

// ---------------------------------------------------------------------------
// 模板元编程增强的 DI
// ---------------------------------------------------------------------------

// 自动注入的工厂
template <typename T, typename... Dependencies>
class AutoFactory {
public:
    static std::shared_ptr<T> create(DIContainer& container) {
        return std::make_shared<T>(container.resolve<Dependencies>()...);
    }
};

// 注册辅助函数
template <typename Interface, typename Implementation, typename... Dependencies>
void auto_register(DIContainer& container) {
    container.template register_factory<Interface>(
        [&container]() -> std::shared_ptr<Interface> {
            return AutoFactory<Implementation, Dependencies...>::create(container);
        }
    );
}

// ---------------------------------------------------------------------------
// 编译期类型安全的 DI
// ---------------------------------------------------------------------------

// 使用模板实现编译期 DI
template <typename Interface>
struct Dependency {
    using type = Interface;
};

// 服务定位器（编译期类型安全版本）
template <typename... Services>
class ServiceLocator {
public:
    template <typename T>
    void register_service(std::shared_ptr<T> service) {
        std::get<std::shared_ptr<T>>(services_) = service;
    }

    template <typename T>
    std::shared_ptr<T> get() const {
        return std::get<std::shared_ptr<T>>(services_);
    }

private:
    std::tuple<std::shared_ptr<Services>...> services_;
};

int main() {
    std::cout << "=== 依赖注入容器演示 ===" << std::endl;
    std::cout << std::endl;

    // 1. 基本 DI 容器
    std::cout << "1. 基本 DI 容器:" << std::endl;
    DIContainer container;

    // 注册组件
    container.register_instance<ILogger>(std::make_shared<ConsoleLogger>());
    container.register_singleton<IRepository, MemoryRepository>();

    // 注册 UserService，自动注入依赖
    container.register_factory<IService>(
        [&container]() -> std::shared_ptr<IService> {
            return std::make_shared<UserService>(
                container.resolve<IRepository>(),
                container.resolve<ILogger>()
            );
        }
    );

    // 使用服务
    auto service = container.resolve<IService>();
    auto repo = container.resolve<IRepository>();

    repo->save(1, "Alice");
    repo->save(2, "Bob");

    std::cout << "  User 1: " << service->process(1) << std::endl;
    std::cout << "  User 2: " << service->process(2) << std::endl;
    std::cout << std::endl;

    // 2. 自动注入
    std::cout << "2. 自动注入:" << std::endl;
    DIContainer container2;
    container2.register_instance<ILogger>(std::make_shared<ConsoleLogger>());
    container2.register_singleton<IRepository, MemoryRepository>();

    // 使用 AutoFactory 自动注入
    auto_register<IService, UserService, IRepository, ILogger>(container2);

    auto service2 = container2.resolve<IService>();
    auto repo2 = container2.resolve<IRepository>();
    repo2->save(10, "Charlie");
    std::cout << "  User 10: " << service2->process(10) << std::endl;
    std::cout << std::endl;

    // 3. 编译期类型安全的 ServiceLocator
    std::cout << "3. 编译期 ServiceLocator:" << std::endl;
    ServiceLocator<ILogger, IRepository> locator;
    locator.register_service<ILogger>(std::make_shared<ConsoleLogger>());
    locator.register_service<IRepository>(std::make_shared<MemoryRepository>());

    auto logger = locator.get<ILogger>();
    auto repo3 = locator.get<IRepository>();

    logger->log("Using ServiceLocator");
    repo3->save(100, "Dave");
    std::cout << "  User 100: " << repo3->find(100) << std::endl;
    std::cout << std::endl;

    // 4. DI 的优势
    std::cout << "4. 依赖注入的优势:" << std::endl;
    std::cout << "  - 松耦合：组件只依赖接口，不依赖具体实现" << std::endl;
    std::cout << "  - 可测试：可以轻松替换为 Mock 实现" << std::endl;
    std::cout << "  - 可配置：运行时可以切换实现" << std::endl;
    std::cout << "  - 模板元编程可以实现编译期类型安全的 DI" << std::endl;
    std::cout << std::endl;

    std::cout << "=== 依赖注入容器演示完成 ===" << std::endl;
    return 0;
}
