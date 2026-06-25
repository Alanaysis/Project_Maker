#include <iostream>

#ifdef HAS_FMT
#include <fmt/format.h>
#endif

/**
 * @file submodule_demo.cpp
 * @brief Git Submodule 示例
 *
 * 演示如何使用 Git Submodule 管理第三方依赖。
 */

int main() {
    std::cout << "=== Git Submodule 示例 ===" << std::endl;
    std::cout << std::endl;

#ifdef HAS_FMT
    std::cout << "fmt 库可用:" << std::endl;
    std::cout << fmt::format("Hello, {}!", "Git Submodule") << std::endl;
#else
    std::cout << "fmt 库未安装" << std::endl;
    std::cout << "请先执行: git submodule add https://github.com/fmtlib/fmt.git third_party/fmt" << std::endl;
#endif

    std::cout << std::endl;
    std::cout << "Git Submodule 使用说明:" << std::endl;
    std::cout << "  1. git submodule add <url> <path>  - 添加子模块" << std::endl;
    std::cout << "  2. git submodule update --init      - 初始化子模块" << std::endl;
    std::cout << "  3. git submodule update --remote     - 更新子模块" << std::endl;
    std::cout << "  4. git submodule status              - 查看子模块状态" << std::endl;

    return 0;
}
