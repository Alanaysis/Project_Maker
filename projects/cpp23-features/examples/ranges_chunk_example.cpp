/**
 * @file ranges_chunk_example.cpp
 * @brief C++23 std::views::chunk 示例
 *
 * std::views::chunk 是 C++23 引入的分块视图。
 * 它将一个范围分割成固定大小的块。
 *
 * 主要特点：
 * - 将范围分割成固定大小的块
 * - 支持惰性求值
 * - 最后一个块可能小于指定大小
 * - 适用于批处理和分页
 *
 * 编译命令：
 * g++ -std=c++23 -o ranges_chunk_example ranges_chunk_example.cpp
 */

#include <iostream>
#include <vector>
#include <string>
#include <ranges>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建一个范围
    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 分成大小为 3 的块
    auto chunks = data | std::views::chunk(3);

    std::cout << "Original: ";
    for (int n : data) std::cout << n << " ";
    std::cout << std::endl;

    std::cout << "Chunks of 3:" << std::endl;
    for (auto chunk : chunks) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 2. 不同大小的分块 ==========

void different_sizes() {
    std::cout << "\n=== 不同大小的分块 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 分成大小为 2 的块
    std::cout << "Chunks of 2:" << std::endl;
    for (auto chunk : data | std::views::chunk(2)) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }

    // 分成大小为 4 的块
    std::cout << "\nChunks of 4:" << std::endl;
    for (auto chunk : data | std::views::chunk(4)) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }

    // 分成大小为 5 的块
    std::cout << "\nChunks of 5:" << std::endl;
    for (auto chunk : data | std::views::chunk(5)) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }
}

// ========== 3. 实际应用：批处理 ==========

void batch_processing() {
    std::cout << "\n=== 实际应用：批处理 ===" << std::endl;

    // 模拟大量数据
    std::vector<int> large_data;
    for (int i = 1; i <= 20; ++i) {
        large_data.push_back(i);
    }

    // 分批处理
    const size_t batch_size = 5;
    size_t batch_num = 1;

    for (auto batch : large_data | std::views::chunk(batch_size)) {
        std::cout << "Processing batch " << batch_num++ << ": [";
        bool first = true;
        for (int n : batch) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;

        // 模拟处理
        // process_batch(batch);
    }
}

// ========== 4. 实际应用：分页 ==========

void pagination() {
    std::cout << "\n=== 实际应用：分页 ===" << std::endl;

    // 模拟数据库记录
    std::vector<std::string> records;
    for (int i = 1; i <= 15; ++i) {
        records.push_back("Record_" + std::to_string(i));
    }

    // 分页显示
    const size_t page_size = 4;
    size_t page_num = 1;

    for (auto page : records | std::views::chunk(page_size)) {
        std::cout << "Page " << page_num++ << ":" << std::endl;
        for (const auto& record : page) {
            std::cout << "  - " << record << std::endl;
        }
        std::cout << std::endl;
    }
}

// ========== 5. 与其他视图组合 ==========

void combination_with_other_views() {
    std::cout << "\n=== 与其他视图组合 ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    // 先过滤再分块
    auto evens_chunked = data
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::chunk(3);

    std::cout << "Evens chunked by 3:" << std::endl;
    for (auto chunk : evens_chunked) {
        std::cout << "  [";
        bool first = true;
        for (int n : chunk) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }

    // 先分块再转换
    auto chunk_sums = data
        | std::views::chunk(4)
        | std::views::transform([](auto chunk) {
            int sum = 0;
            for (int n : chunk) sum += n;
            return sum;
        });

    std::cout << "\nChunk sums (chunks of 4):" << std::endl;
    for (int sum : chunk_sums) {
        std::cout << "  " << sum << std::endl;
    }
}

// ========== 6. 实际应用：矩阵处理 ==========

void matrix_processing() {
    std::cout << "\n=== 实际应用：矩阵处理 ===" << std::endl;

    // 创建一个一维数组表示的矩阵
    std::vector<int> flat_matrix = {
        1, 2, 3, 4,
        5, 6, 7, 8,
        9, 10, 11, 12
    };

    // 将一维数组转换为二维视图
    auto rows = flat_matrix | std::views::chunk(4);

    std::cout << "Matrix (3x4):" << std::endl;
    for (auto row : rows) {
        std::cout << "  [";
        bool first = true;
        for (int n : row) {
            if (!first) std::cout << ", ";
            std::cout << n;
            first = false;
        }
        std::cout << "]" << std::endl;
    }

    // 计算每行的和
    std::cout << "\nRow sums:" << std::endl;
    size_t row_num = 1;
    for (auto row : rows) {
        int sum = 0;
        for (int n : row) sum += n;
        std::cout << "  Row " << row_num++ << ": " << sum << std::endl;
    }
}

// ========== 7. 实际应用：数据聚合 ==========

void data_aggregation() {
    std::cout << "\n=== 实际应用：数据聚合 ===" << std::endl;

    // 模拟销售数据
    std::vector<double> daily_sales = {
        100.5, 150.2, 200.0, 175.3, 125.8,  // 第1周
        180.4, 160.7, 190.1, 210.5, 195.2,  // 第2周
        140.6, 155.9, 170.3, 185.7, 200.1   // 第3周
    };

    // 按周聚合
    auto weeks = daily_sales | std::views::chunk(5);

    std::cout << "Weekly sales summary:" << std::endl;
    size_t week_num = 1;
    for (auto week : weeks) {
        double total = 0;
        double min_val = std::numeric_limits<double>::max();
        double max_val = std::numeric_limits<double>::lowest();

        for (double sale : week) {
            total += sale;
            min_val = std::min(min_val, sale);
            max_val = std::max(max_val, sale);
        }

        double avg = total / 5;
        std::cout << "  Week " << week_num++ << ":" << std::endl;
        std::cout << "    Total: " << total << std::endl;
        std::cout << "    Average: " << avg << std::endl;
        std::cout << "    Min: " << min_val << std::endl;
        std::cout << "    Max: " << max_val << std::endl;
    }
}

// ========== 8. 实际应用：文本处理 ==========

void text_processing() {
    std::cout << "\n=== 实际应用：文本处理 ===" << std::endl;

    // 将文本分成固定长度的行
    std::string text = "This is a long text that needs to be split into fixed-width lines for display purposes.";
    const size_t line_width = 20;

    auto lines = text | std::views::chunk(line_width);

    std::cout << "Text split into " << line_width << "-character lines:" << std::endl;
    for (auto line : lines) {
        std::cout << "  |";
        for (char c : line) std::cout << c;
        std::cout << "|" << std::endl;
    }

    // 将数字字符串分成组
    std::string numbers = "1234567890123456";
    auto groups = numbers | std::views::chunk(4);

    std::cout << "\nNumber groups (4 digits each):" << std::endl;
    for (auto group : groups) {
        std::cout << "  ";
        for (char c : group) std::cout << c;
        std::cout << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::views::chunk 示例\n" << std::endl;

    basic_usage();
    different_sizes();
    batch_processing();
    pagination();
    combination_with_other_views();
    matrix_processing();
    data_aggregation();
    text_processing();

    return 0;
}
