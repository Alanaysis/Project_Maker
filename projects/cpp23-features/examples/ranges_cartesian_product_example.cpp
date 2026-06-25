/**
 * @file ranges_cartesian_product_example.cpp
 * @brief C++23 std::views::cartesian_product 示例
 *
 * std::views::cartesian_product 是 C++23 引入的笛卡尔积视图。
 * 它可以生成多个范围的所有可能组合。
 *
 * 主要特点：
 * - 生成多个范围的所有组合
 * - 支持任意数量的范围
 * - 适用于组合问题和穷举搜索
 * - 支持惰性求值
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_cartesian_product_example ranges_cartesian_product_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::vector<int> nums1 = {1, 2, 3};
    std::vector<char> chars = {'A', 'B'};

    // 生成笛卡尔积
    std::cout << "Cartesian product of {1,2,3} x {A,B}:" << std::endl;
    for (auto [n, c] : std::views::cartesian_product(nums1, chars)) {
        std::cout << "  (" << n << ", " << c << ")" << std::endl;
    }
}

// ========== 2. 三个范围的笛卡尔积 ==========

void three_ranges() {
    std::cout << "\n=== 三个范围的笛卡尔积 ===" << std::endl;

    std::vector<int> sizes = {1, 2};
    std::vector<std::string> colors = {"Red", "Blue"};
    std::vector<std::string> shapes = {"Circle", "Square"};

    std::cout << "All combinations:" << std::endl;
    for (auto [size, color, shape] : std::views::cartesian_product(sizes, colors, shapes)) {
        std::cout << "  " << size << " " << color << " " << shape << std::endl;
    }
}

// ========== 3. 实际应用：生成测试用例 ==========

void test_case_generation() {
    std::cout << "\n=== 实际应用：生成测试用例 ===" << std::endl;

    // 测试参数
    std::vector<std::string> browsers = {"Chrome", "Firefox", "Safari"};
    std::vector<std::string> os_list = {"Windows", "macOS", "Linux"};
    std::vector<int> screen_sizes = {1024, 1920, 2560};

    std::cout << "Test case matrix:" << std::endl;
    int test_id = 1;
    for (auto [browser, os, screen] : std::views::cartesian_product(browsers, os_list, screen_sizes)) {
        std::cout << "  Test " << test_id++ << ": "
                  << browser << " on " << os << " @ " << screen << "px" << std::endl;
    }
}

// ========== 4. 实际应用：密码生成 ==========

void password_generation() {
    std::cout << "\n=== 实际应用：密码生成 ===" << std::endl;

    // 字符集
    std::vector<char> digits = {'0', '1', '2'};
    std::vector<char> letters = {'A', 'B'};

    // 生成 2 位密码
    std::cout << "2-character passwords (digits + letters):" << std::endl;
    for (auto [d, l] : std::views::cartesian_product(digits, letters)) {
        std::cout << "  " << d << l << std::endl;
    }

    // 生成 3 位密码
    std::vector<char> symbols = {'!', '@'};
    std::cout << "\n3-character passwords (digits + letters + symbols):" << std::endl;
    for (auto [d, l, s] : std::views::cartesian_product(digits, letters, symbols)) {
        std::cout << "  " << d << l << s << std::endl;
    }
}

// ========== 5. 实际应用：坐标系统 ==========

void coordinate_system() {
    std::cout << "\n=== 实际应用：坐标系统 ===" << std::endl;

    // 2D 坐标
    std::vector<int> x_coords = {0, 1, 2};
    std::vector<int> y_coords = {0, 1, 2};

    std::cout << "2D grid points:" << std::endl;
    for (auto [x, y] : std::views::cartesian_product(x_coords, y_coords)) {
        std::cout << "  (" << x << ", " << y << ")" << std::endl;
    }

    // 3D 坐标
    std::vector<int> z_coords = {0, 1};
    std::cout << "\n3D grid points (first few):" << std::endl;
    int count = 0;
    for (auto [x, y, z] : std::views::cartesian_product(x_coords, y_coords, z_coords)) {
        if (count++ >= 6) break;
        std::cout << "  (" << x << ", " << y << ", " << z << ")" << std::endl;
    }
}

// ========== 6. 实际应用：配置组合 ==========

void configuration_combinations() {
    std::cout << "\n=== 实际应用：配置组合 ===" << std::endl;

    // 系统配置选项
    std::vector<std::string> themes = {"Light", "Dark"};
    std::vector<std::string> languages = {"English", "Chinese"};
    std::vector<int> font_sizes = {12, 14, 16};

    std::cout << "Configuration combinations:" << std::endl;
    for (auto [theme, lang, font] : std::views::cartesian_product(themes, languages, font_sizes)) {
        std::cout << "  Theme: " << theme
                  << ", Language: " << lang
                  << ", Font: " << font << "px" << std::endl;
    }
}

// ========== 7. 实际应用：游戏状态 ==========

void game_states() {
    std::cout << "\n=== 实际应用：游戏状态 ===" << std::endl;

    // 游戏状态
    std::vector<std::string> player_states = {"Idle", "Running", "Jumping"};
    std::vector<std::string> weapon_states = {"None", "Sword", "Bow"};
    std::vector<int> health_levels = {100, 50, 25};

    std::cout << "Possible game states:" << std::endl;
    for (auto [player, weapon, health] : std::views::cartesian_product(player_states, weapon_states, health_levels)) {
        std::cout << "  Player: " << player
                  << ", Weapon: " << weapon
                  << ", Health: " << health << "%" << std::endl;
    }
}

// ========== 8. 实际应用：数据生成 ==========

void data_generation() {
    std::cout << "\n=== 实际应用：数据生成 ===" << std::endl;

    // 生成模拟数据
    std::vector<std::string> categories = {"Electronics", "Clothing", "Food"};
    std::vector<std::string> regions = {"North", "South", "East", "West"};
    std::vector<int> quarters = {1, 2, 3, 4};

    std::cout << "Sales report structure:" << std::endl;
    for (auto [category, region, quarter] : std::views::cartesian_product(categories, regions, quarters)) {
        std::cout << "  " << category << " - " << region << " - Q" << quarter << std::endl;
    }
}

// ========== 9. 实际应用：算法测试 ==========

void algorithm_testing() {
    std::cout << "\n=== 实际应用：算法测试 ===" << std::endl;

    // 测试参数范围
    std::vector<int> sizes = {100, 1000, 10000};
    std::vector<int> iterations = {10, 100};

    std::cout << "Algorithm test matrix:" << std::endl;
    for (auto [size, iter] : std::views::cartesian_product(sizes, iterations)) {
        std::cout << "  Size: " << size << ", Iterations: " << iter << std::endl;
    }
}

// ========== 10. 实际应用：组合优化 ==========

void combinatorial_optimization() {
    std::cout << "\n=== 实际应用：组合优化 ===" << std::endl;

    // 物品选择
    std::vector<std::string> items = {"ItemA", "ItemB", "ItemC"};
    std::vector<int> quantities = {0, 1, 2};

    std::cout << "Inventory combinations (up to 2 of each):" << std::endl;
    for (auto [item, qty] : std::views::cartesian_product(items, quantities)) {
        std::cout << "  " << item << ": " << qty << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::cartesian_product 示例\n" << std::endl;

    basic_usage();
    three_ranges();
    test_case_generation();
    password_generation();
    coordinate_system();
    configuration_combinations();
    game_states();
    data_generation();
    algorithm_testing();
    combinatorial_optimization();

    return 0;
}
