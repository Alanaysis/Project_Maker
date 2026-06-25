/**
 * @file parallel_algorithms.cpp
 * @brief C++17 并行算法示例
 *
 * C++17 引入了并行执行策略，允许标准算法利用多核处理器。
 * 通过指定执行策略，可以轻松实现并行计算。
 *
 * 主要优势：
 * 1. 简单易用 - 只需添加执行策略参数
 * 2. 自动并行化 - 运行时决定并行度
 * 3. 可移植 - 标准化的并行接口
 *
 * 注意：需要编译器支持并链接 TBB（GCC）或其他并行库
 */

#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <random>
#include <chrono>
#include <execution>
#include <string>
#include <functional>
#include <cmath>

// 1. 基本并行算法
void basic_parallel_example() {
    std::cout << "\n[基本并行算法]" << std::endl;

    // 创建大数据集
    const size_t size = 1000000;
    std::vector<int> data(size);

    // 填充随机数据
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 1000);

    for (auto& val : data) {
        val = dis(gen);
    }

    // 串行排序
    auto data_copy = data;
    auto start = std::chrono::high_resolution_clock::now();
    std::sort(std::execution::seq, data_copy.begin(), data_copy.end());
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行排序
    data_copy = data;
    start = std::chrono::high_resolution_clock::now();
    std::sort(std::execution::par, data_copy.begin(), data_copy.end());
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行+向量化排序
    data_copy = data;
    start = std::chrono::high_resolution_clock::now();
    std::sort(std::execution::par_unseq, data_copy.begin(), data_copy.end());
    end = std::chrono::high_resolution_clock::now();
    auto duration_par_unseq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential sort: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel sort: " << duration_par.count() << " ms" << std::endl;
    std::cout << "Parallel+vectorized sort: " << duration_par_unseq.count() << " ms" << std::endl;
    std::cout << "Speedup (parallel): "
              << static_cast<double>(duration_seq.count()) / duration_par.count() << "x" << std::endl;
}

// 2. 执行策略
void execution_policy_example() {
    std::cout << "\n[执行策略]" << std::endl;

    std::vector<int> data = {5, 3, 1, 4, 2, 8, 7, 6};

    // 串行执行
    auto data_seq = data;
    std::sort(std::execution::seq, data_seq.begin(), data_seq.end());
    std::cout << "Sequential: ";
    for (int v : data_seq) std::cout << v << " ";
    std::cout << std::endl;

    // 并行执行
    auto data_par = data;
    std::sort(std::execution::par, data_par.begin(), data_par.end());
    std::cout << "Parallel: ";
    for (int v : data_par) std::cout << v << " ";
    std::cout << std::endl;

    // 并行+向量化执行
    auto data_par_unseq = data;
    std::sort(std::execution::par_unseq, data_par_unseq.begin(), data_par_unseq.end());
    std::cout << "Parallel+vectorized: ";
    for (int v : data_par_unseq) std::cout << v << " ";
    std::cout << std::endl;

    // 不并行执行（C++20）
    // std::sort(std::execution::unseq, data.begin(), data.end());
}

// 3. 并行 for_each
void parallel_for_each_example() {
    std::cout << "\n[并行 for_each]" << std::endl;

    const size_t size = 1000000;
    std::vector<double> data(size, 1.0);

    // 串行 for_each
    auto start = std::chrono::high_resolution_clock::now();
    std::for_each(std::execution::seq, data.begin(), data.end(),
                  [](double& x) { x = std::sqrt(x); });
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 重置数据
    std::fill(data.begin(), data.end(), 1.0);

    // 并行 for_each
    start = std::chrono::high_resolution_clock::now();
    std::for_each(std::execution::par, data.begin(), data.end(),
                  [](double& x) { x = std::sqrt(x); });
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential for_each: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel for_each: " << duration_par.count() << " ms" << std::endl;
}

// 4. 并行 transform
void parallel_transform_example() {
    std::cout << "\n[并行 transform]" << std::endl;

    const size_t size = 1000000;
    std::vector<int> input(size);
    std::vector<int> output(size);

    // 填充数据
    std::iota(input.begin(), input.end(), 1);

    // 串行 transform
    auto start = std::chrono::high_resolution_clock::now();
    std::transform(std::execution::seq, input.begin(), input.end(), output.begin(),
                   [](int x) { return x * x; });
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 transform
    start = std::chrono::high_resolution_clock::now();
    std::transform(std::execution::par, input.begin(), input.end(), output.begin(),
                   [](int x) { return x * x; });
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential transform: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel transform: " << duration_par.count() << " ms" << std::endl;

    // 验证结果
    std::cout << "First 5 results: ";
    for (size_t i = 0; i < 5; ++i) {
        std::cout << output[i] << " ";
    }
    std::cout << std::endl;
}

// 5. 并行 reduce
void parallel_reduce_example() {
    std::cout << "\n[并行 reduce]" << std::endl;

    const size_t size = 10000000;
    std::vector<int> data(size);
    std::iota(data.begin(), data.end(), 1);

    // 串行 reduce
    auto start = std::chrono::high_resolution_clock::now();
    long long sum_seq = std::reduce(std::execution::seq, data.begin(), data.end(), 0LL);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 reduce
    start = std::chrono::high_resolution_clock::now();
    long long sum_par = std::reduce(std::execution::par, data.begin(), data.end(), 0LL);
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential reduce: " << duration_seq.count() << " ms (sum=" << sum_seq << ")" << std::endl;
    std::cout << "Parallel reduce: " << duration_par.count() << " ms (sum=" << sum_par << ")" << std::endl;
    std::cout << "Results match: " << (sum_seq == sum_par ? "true" : "false") << std::endl;
}

// 6. 并行 find
void parallel_find_example() {
    std::cout << "\n[并行 find]" << std::endl;

    const size_t size = 10000000;
    std::vector<int> data(size);
    std::iota(data.begin(), data.end(), 1);

    int target = size - 1;  // 查找最后一个元素

    // 串行 find
    auto start = std::chrono::high_resolution_clock::now();
    auto it_seq = std::find(std::execution::seq, data.begin(), data.end(), target);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 find
    start = std::chrono::high_resolution_clock::now();
    auto it_par = std::find(std::execution::par, data.begin(), data.end(), target);
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Target: " << target << std::endl;
    std::cout << "Sequential find: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel find: " << duration_par.count() << " ms" << std::endl;
    std::cout << "Found: " << (it_par != data.end() ? "true" : "false") << std::endl;
}

// 7. 并行 count
void parallel_count_example() {
    std::cout << "\n[并行 count]" << std::endl;

    const size_t size = 10000000;
    std::vector<int> data(size);

    // 填充随机数据
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 100);

    for (auto& val : data) {
        val = dis(gen);
    }

    int target = 42;

    // 串行 count
    auto start = std::chrono::high_resolution_clock::now();
    auto count_seq = std::count(std::execution::seq, data.begin(), data.end(), target);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 count
    start = std::chrono::high_resolution_clock::now();
    auto count_par = std::count(std::execution::par, data.begin(), data.end(), target);
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Target: " << target << std::endl;
    std::cout << "Sequential count: " << duration_seq.count() << " ms (count=" << count_seq << ")" << std::endl;
    std::cout << "Parallel count: " << duration_par.count() << " ms (count=" << count_par << ")" << std::endl;
}

// 8. 并行 inclusive_scan
void parallel_scan_example() {
    std::cout << "\n[并行 inclusive_scan]" << std::endl;

    const size_t size = 10000000;
    std::vector<int> data(size);
    std::vector<int> result_seq(size);
    std::vector<int> result_par(size);

    std::iota(data.begin(), data.end(), 1);

    // 串行 inclusive_scan
    auto start = std::chrono::high_resolution_clock::now();
    std::inclusive_scan(std::execution::seq, data.begin(), data.end(), result_seq.begin());
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 inclusive_scan
    start = std::chrono::high_resolution_clock::now();
    std::inclusive_scan(std::execution::par, data.begin(), data.end(), result_par.begin());
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential inclusive_scan: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel inclusive_scan: " << duration_par.count() << " ms" << std::endl;

    // 验证结果
    std::cout << "First 5 results: ";
    for (size_t i = 0; i < 5; ++i) {
        std::cout << result_par[i] << " ";
    }
    std::cout << std::endl;

    std::cout << "Results match: "
              << (result_seq == result_par ? "true" : "false") << std::endl;
}

// 9. 并行 copy
void parallel_copy_example() {
    std::cout << "\n[并行 copy]" << std::endl;

    const size_t size = 10000000;
    std::vector<int> source(size);
    std::vector<int> dest_seq(size);
    std::vector<int> dest_par(size);

    std::iota(source.begin(), source.end(), 1);

    // 串行 copy
    auto start = std::chrono::high_resolution_clock::now();
    std::copy(std::execution::seq, source.begin(), source.end(), dest_seq.begin());
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行 copy
    start = std::chrono::high_resolution_clock::now();
    std::copy(std::execution::par, source.begin(), source.end(), dest_par.begin());
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Data size: " << size << std::endl;
    std::cout << "Sequential copy: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel copy: " << duration_par.count() << " ms" << std::endl;

    // 验证结果
    std::cout << "Results match: "
              << (dest_seq == dest_par ? "true" : "false") << std::endl;
}

// 10. 实际应用：图像处理
void image_processing_example() {
    std::cout << "\n[实际应用：图像处理]" << std::endl;

    // 模拟图像数据（灰度值 0-255）
    const size_t width = 1920;
    const size_t height = 1080;
    const size_t size = width * height;

    std::vector<uint8_t> image(size);
    std::vector<uint8_t> result_seq(size);
    std::vector<uint8_t> result_par(size);

    // 填充随机像素
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 255);

    for (auto& pixel : image) {
        pixel = dis(gen);
    }

    // 图像亮度调整函数
    auto adjust_brightness = [](uint8_t pixel, int adjustment) -> uint8_t {
        int result = pixel + adjustment;
        return static_cast<uint8_t>(std::clamp(result, 0, 255));
    };

    int brightness = 50;

    // 串行处理
    auto start = std::chrono::high_resolution_clock::now();
    std::transform(std::execution::seq, image.begin(), image.end(), result_seq.begin(),
                   [adjust_brightness, brightness](uint8_t pixel) {
                       return adjust_brightness(pixel, brightness);
                   });
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_seq = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // 并行处理
    start = std::chrono::high_resolution_clock::now();
    std::transform(std::execution::par, image.begin(), image.end(), result_par.begin(),
                   [adjust_brightness, brightness](uint8_t pixel) {
                       return adjust_brightness(pixel, brightness);
                   });
    end = std::chrono::high_resolution_clock::now();
    auto duration_par = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Image size: " << width << "x" << height << std::endl;
    std::cout << "Sequential processing: " << duration_seq.count() << " ms" << std::endl;
    std::cout << "Parallel processing: " << duration_par.count() << " ms" << std::endl;
    std::cout << "Speedup: "
              << static_cast<double>(duration_seq.count()) / duration_par.count() << "x" << std::endl;
}

// 11. 注意事项
void considerations_example() {
    std::cout << "\n[注意事项]" << std::endl;

    std::cout << "1. 数据竞争:" << std::endl;
    std::cout << "   - 确保算法不会产生数据竞争" << std::endl;
    std::cout << "   - 并行算法保证无数据竞争" << std::endl;

    std::cout << "\n2. 性能考虑:" << std::endl;
    std::cout << "   - 小数据集可能串行更快" << std::endl;
    std::cout << "   - 并行化有开销" << std::endl;
    std::cout << "   - 需要实际测试" << std::endl;

    std::cout << "\n3. 异常安全:" << std::endl;
    std::cout << "   - 并行算法可能抛出异常" << std::endl;
    std::cout << "   - 异常会终止所有并行任务" << std::endl;

    std::cout << "\n4. 编译器支持:" << std::endl;
    std::cout << "   - GCC: 需要链接 TBB" << std::endl;
    std::cout << "   - Clang: 需要链接 TBB 或其他实现" << std::endl;
    std::cout << "   - MSVC: 内置支持" << std::endl;
}

// 12. 最佳实践
void best_practices_example() {
    std::cout << "\n[最佳实践]" << std::endl;

    std::cout << "1. 选择合适的执行策略:" << std::endl;
    std::cout << "   - seq: 串行执行" << std::endl;
    std::cout << "   - par: 并行执行" << std::endl;
    std::cout << "   - par_unseq: 并行+向量化" << std::endl;

    std::cout << "\n2. 性能测试:" << std::endl;
    std::cout << "   - 在目标硬件上测试" << std::endl;
    std::cout << "   - 考虑数据大小和特性" << std::endl;
    std::cout << "   - 比较不同策略的性能" << std::endl;

    std::cout << "\n3. 错误处理:" << std::endl;
    std::cout << "   - 处理可能的异常" << std::endl;
    std::cout << "   - 验证结果正确性" << std::endl;

    std::cout << "\n4. 调试:" << std::endl;
    std::cout << "   - 使用串行模式调试" << std::endl;
    std::cout << "   - 使用消毒器检测问题" << std::endl;
}

// 主示例函数
void parallel_algorithms_example() {
    std::cout << "=== 并行算法 ===" << std::endl;

    basic_parallel_example();
    execution_policy_example();
    parallel_for_each_example();
    parallel_transform_example();
    parallel_reduce_example();
    parallel_find_example();
    parallel_count_example();
    parallel_scan_example();
    parallel_copy_example();
    image_processing_example();
    considerations_example();
    best_practices_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    parallel_algorithms_example();
    return 0;
}
#endif
