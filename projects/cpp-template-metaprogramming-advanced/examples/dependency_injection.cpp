/**
 * @file dependency_injection.cpp
 * @brief 依赖注入示例
 */

#include <iostream>
#include <memory>
#include "../include/design_patterns/dependency_injection.hpp"

int main() {
    using namespace tmp;

    std::cout << "=== Dependency Injection ===" << std::endl;
    std::cout << std::endl;

    // 1. 构造函数注入
    std::cout << "--- 1. Constructor Injection ---" << std::endl;

    auto console_logger = std::make_shared<ConsoleLogger>();
    UserService service1(console_logger);
    service1.create_user("Alice");

    auto null_logger = std::make_shared<NullLogger>();
    UserService service2(null_logger);
    service2.create_user("Bob");  // 无输出
    std::cout << std::endl;

    // 2. 模板化注入（编译期多态）
    std::cout << "--- 2. Template Injection (Compile-time) ---" << std::endl;

    TemplateUserService<TemplateConsoleLogger> template_service1;
    template_service1.create_user("Charlie");

    TemplateUserService<TemplateNullLogger> template_service2;
    template_service2.create_user("Dave");  // 无输出
    std::cout << std::endl;

    // 3. DI 容器
    std::cout << "--- 3. DI Container ---" << std::endl;

    DIContainer container;
    container.register_instance<ILogger>(std::make_shared<ConsoleLogger>());

    auto logger = container.resolve<ILogger>();
    logger->log("Message from DI container");
    std::cout << std::endl;

    // 4. 服务定位器
    std::cout << "--- 4. Service Locator ---" << std::endl;

    ServiceLocator::register_service<ILogger>(std::make_shared<ConsoleLogger>());
    auto located_logger = ServiceLocator::get<ILogger>();
    located_logger->log("Message from service locator");

    ServiceLocator::clear();
    std::cout << std::endl;

    std::cout << "Key benefits:" << std::endl;
    std::cout << "  - Loose coupling between components" << std::endl;
    std::cout << "  - Easy testing with mock dependencies" << std::endl;
    std::cout << "  - Template injection = zero runtime overhead" << std::endl;

    return 0;
}
