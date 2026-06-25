/**
 * @file generator_example.cpp
 * @brief C++23 std::generator 示例
 *
 * std::generator 是 C++23 引入的协程生成器，简化了协程的使用。
 * 它提供了标准的生成器实现，用于惰性计算和流式处理。
 *
 * 主要特点：
 * - 标准化的协程生成器
 * - 惰性求值
 * - 支持 co_yield 生成值
 * - 便于组合和管道操作
 *
 * 编译命令：
 * g++ -std=c++23 -o generator_example generator_example.cpp
 */

#include <iostream>
#include <generator>
#include <vector>
#include <ranges>
#include <algorithm>
#include <numeric>

// ========== 1. 基本生成器 ==========

// 简单的整数生成器
std::generator<int> count_up(int start, int end) {
    for (int i = start; i <= end; ++i) {
        co_yield i;
    }
}

// 斐波那契生成器
std::generator<long long> fibonacci() {
    long long a = 0, b = 1;
    while (true) {
        co_yield a;
        auto temp = a;
        a = b;
        b = temp + b;
    }
}

void basic_usage() {
    std::cout << "=== 基本生成器 ===" << std::endl;

    // 使用计数生成器
    std::cout << "Count 1 to 5: ";
    for (auto val : count_up(1, 5)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 使用斐波那契生成器 (取前 10 个)
    std::cout << "First 10 Fibonacci numbers: ";
    int count = 0;
    for (auto val : fibonacci()) {
        if (count >= 10) break;
        std::cout << val << " ";
        ++count;
    }
    std::cout << std::endl;
}

// ========== 2. 生成器与 Ranges 结合 ==========

// 生成偶数
std::generator<int> even_numbers(int start = 0) {
    for (int i = start; ; i += 2) {
        co_yield i;
    }
}

// 生成素数 (简单筛法)
std::generator<int> primes() {
    co_yield 2;
    for (int n = 3; ; n += 2) {
        bool is_prime = true;
        for (int d = 3; d * d <= n; d += 2) {
            if (n % d == 0) {
                is_prime = false;
                break;
            }
        }
        if (is_prime) {
            co_yield n;
        }
    }
}

void ranges_integration() {
    std::cout << "\n=== 生成器与 Ranges 结合 ===" << std::endl;

    // 取前 5 个偶数
    auto evens = even_numbers()
        | std::views::take(5);
    std::cout << "First 5 even numbers: ";
    for (auto val : evens) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 取前 10 个素数
    auto first_primes = primes()
        | std::views::take(10);
    std::cout << "First 10 primes: ";
    for (auto val : first_primes) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 使用 transform
    auto squares = count_up(1, 5)
        | std::views::transform([](int x) { return x * x; });
    std::cout << "Squares of 1-5: ";
    for (auto val : squares) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 3. 参数化生成器 ==========

// 生成等差数列
std::generator<int> arithmetic_sequence(int start, int step, size_t count) {
    int current = start;
    for (size_t i = 0; i < count; ++i) {
        co_yield current;
        current += step;
    }
}

// 生成几何数列
std::generator<double> geometric_sequence(double start, double ratio, size_t count) {
    double current = start;
    for (size_t i = 0; i < count; ++i) {
        co_yield current;
        current *= ratio;
    }
}

void parameterized_generators() {
    std::cout << "\n=== 参数化生成器 ===" << std::endl;

    // 等差数列: 2, 5, 8, 11, 14
    std::cout << "Arithmetic sequence (start=2, step=3, count=5): ";
    for (auto val : arithmetic_sequence(2, 3, 5)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 几何数列: 1, 2, 4, 8, 16
    std::cout << "Geometric sequence (start=1, ratio=2, count=5): ";
    for (auto val : geometric_sequence(1.0, 2.0, 5)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 4. 生成器组合 ==========

// 合并两个生成器
template<typename T>
std::generator<T> chain(std::generator<T> gen1, std::generator<T> gen2) {
    for (auto val : gen1) {
        co_yield val;
    }
    for (auto val : gen2) {
        co_yield val;
    }
}

// 交错两个生成器
template<typename T>
std::generator<T> interleave(std::generator<T> gen1, std::generator<T> gen2) {
    auto it1 = gen1.begin();
    auto it2 = gen2.begin();
    while (it1 != gen1.end() || it2 != gen2.end()) {
        if (it1 != gen1.end()) {
            co_yield *it1;
            ++it1;
        }
        if (it2 != gen2.end()) {
            co_yield *it2;
            ++it2;
        }
    }
}

void generator_combination() {
    std::cout << "\n=== 生成器组合 ===" << std::endl;

    // 合并生成器
    auto combined = chain(count_up(1, 3), count_up(10, 12));
    std::cout << "Chained: ";
    for (auto val : combined) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 交错生成器
    auto interleaved = interleave(count_up(1, 5), count_up(100, 104));
    std::cout << "Interleaved: ";
    for (auto val : interleaved) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 5. 实际应用：数据流处理 ==========

// 模拟数据源
std::generator<double> sensor_data() {
    double value = 20.0;
    for (int i = 0; i < 10; ++i) {
        value += (rand() % 100 - 50) / 100.0;
        co_yield value;
    }
}

// 移动平均
std::generator<double> moving_average(std::generator<double> source, size_t window_size) {
    std::vector<double> window;
    for (auto val : source) {
        window.push_back(val);
        if (window.size() > window_size) {
            window.erase(window.begin());
        }
        if (window.size() == window_size) {
            double avg = std::accumulate(window.begin(), window.end(), 0.0) / window_size;
            co_yield avg;
        }
    }
}

void data_stream_example() {
    std::cout << "\n=== 实际应用：数据流处理 ===" << std::endl;

    // 生成传感器数据
    std::cout << "Raw sensor data: ";
    for (auto val : sensor_data()) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 计算移动平均
    std::cout << "Moving average (window=3): ";
    for (auto val : moving_average(sensor_data(), 3)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 6. 递归生成器 ==========

// 生成所有子集
std::generator<std::vector<int>> subsets(const std::vector<int>& nums) {
    size_t n = nums.size();
    for (size_t mask = 0; mask < (1ULL << n); ++mask) {
        std::vector<int> subset;
        for (size_t i = 0; i < n; ++i) {
            if (mask & (1ULL << i)) {
                subset.push_back(nums[i]);
            }
        }
        co_yield subset;
    }
}

// 生成排列
std::generator<std::vector<int>> permutations(std::vector<int> nums) {
    std::ranges::sort(nums);
    do {
        co_yield nums;
    } while (std::ranges::next_permutation(nums).found);
}

void recursive_generators() {
    std::cout << "\n=== 递归生成器 ===" << std::endl;

    // 子集
    std::vector<int> nums = {1, 2, 3};
    std::cout << "Subsets of {1, 2, 3}:" << std::endl;
    for (auto subset : subsets(nums)) {
        std::cout << "{ ";
        for (auto val : subset) {
            std::cout << val << " ";
        }
        std::cout << "}" << std::endl;
    }

    // 排列
    std::cout << "\nPermutations of {1, 2, 3}:" << std::endl;
    for (auto perm : permutations(nums)) {
        std::cout << "[ ";
        for (auto val : perm) {
            std::cout << val << " ";
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 7. 无限生成器 ==========

// 无限自然数
std::generator<int> natural_numbers(int start = 1) {
    int n = start;
    while (true) {
        co_yield n++;
    }
}

// 无限循环
template<typename T>
std::generator<T> cycle(std::vector<T> items) {
    while (true) {
        for (auto& item : items) {
            co_yield item;
        }
    }
}

void infinite_generators() {
    std::cout << "\n=== 无限生成器 ===" << std::endl;

    // 取前 10 个自然数
    std::cout << "First 10 natural numbers: ";
    for (auto val : natural_numbers() | std::views::take(10)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;

    // 循环生成器
    std::vector<char> letters = {'A', 'B', 'C'};
    std::cout << "First 8 cyclic letters: ";
    for (auto val : cycle(letters) | std::views::take(8)) {
        std::cout << val << " ";
    }
    std::cout << std::endl;
}

// ========== 8. 生成器性能 ==========

void performance_comparison() {
    std::cout << "\n=== 生成器 vs 预计算 ===" << std::endl;

    // 使用生成器 (惰性计算)
    std::cout << "Using generator (lazy): ";
    int sum_lazy = 0;
    for (auto val : count_up(1, 1000)) {
        sum_lazy += val;
    }
    std::cout << "Sum of 1-1000 = " << sum_lazy << std::endl;

    // 使用预计算 (急切计算)
    std::cout << "Using precomputed (eager): ";
    std::vector<int> precomputed(1000);
    std::iota(precomputed.begin(), precomputed.end(), 1);
    int sum_eager = std::accumulate(precomputed.begin(), precomputed.end(), 0);
    std::cout << "Sum of 1-1000 = " << sum_eager << std::endl;

    std::cout << "\nNote: Generator is more memory efficient for large sequences." << std::endl;
}

int main() {
    std::cout << "C++23 std::generator 示例\n" << std::endl;

    basic_usage();
    ranges_integration();
    parameterized_generators();
    generator_combination();
    data_stream_example();
    recursive_generators();
    infinite_generators();
    performance_comparison();

    return 0;
}
