/**
 * @file mdspan_example.cpp
 * @brief C++23 std::mdspan 示例
 *
 * std::mdspan 是 C++23 引入的多维数组视图，类似 NumPy 的 ndarray。
 * 它提供了零开销的多维数组抽象，支持灵活的内存布局。
 *
 * 主要特点：
 * - 零开销抽象：不引入额外运行时开销
 * - 灵活的内存布局：支持行优先、列优先等
 * - 与现有代码兼容：可以包装现有的连续内存
 * - 便于科学计算：支持多维数组操作
 *
 * 编译命令：
 * g++ -std=c++23 -o mdspan_example mdspan_example.cpp
 */

#include <iostream>
#include <vector>
#include <mdspan>
#include <numeric>
#include <algorithm>
#include <cassert>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建一个 3x4 的二维数组
    std::vector<int> data(12);
    std::iota(data.begin(), data.end(), 1);  // 填充 1-12

    // 创建 mdspan 视图
    std::mdspan<int, std::extents<size_t, 3, 4>> matrix(data.data());

    // 访问元素
    std::cout << "Matrix (3x4):" << std::endl;
    for (size_t i = 0; i < matrix.extent(0); ++i) {
        for (size_t j = 0; j < matrix.extent(1); ++j) {
            std::cout << matrix[i, j] << "\t";  // C++23 多维下标
        }
        std::cout << std::endl;
    }

    // 修改元素
    matrix[1, 2] = 100;
    std::cout << "\nAfter modifying [1,2] to 100:" << std::endl;
    std::cout << "matrix[1,2] = " << matrix[1, 2] << std::endl;
}

// ========== 2. 动态维度 ==========

void dynamic_extents() {
    std::cout << "\n=== 动态维度 ===" << std::endl;

    // 使用动态维度
    std::vector<int> data(20);
    std::iota(data.begin(), data.end(), 1);

    // 创建 4x5 的动态 mdspan
    std::mdspan<int, std::dextents<size_t, 2>> matrix(data.data(), 4, 5);

    std::cout << "Dynamic matrix (4x5):" << std::endl;
    for (size_t i = 0; i < matrix.extent(0); ++i) {
        for (size_t j = 0; j < matrix.extent(1); ++j) {
            std::cout << matrix[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    // 动态维度可以在运行时确定
    size_t rows = 2, cols = 10;
    std::mdspan<int, std::dextents<size_t, 2>> another_matrix(data.data(), rows, cols);

    std::cout << "\nAnother matrix (2x10):" << std::endl;
    for (size_t i = 0; i < another_matrix.extent(0); ++i) {
        for (size_t j = 0; j < another_matrix.extent(1); ++j) {
            std::cout << another_matrix[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 3. 混合维度 ==========

void mixed_extents() {
    std::cout << "\n=== 混合维度 (静态+动态) ===" << std::endl;

    // 静态行数，动态列数
    std::vector<int> data(15);
    std::iota(data.begin(), data.end(), 1);

    // 3 行，动态列数
    std::mdspan<int, std::extents<size_t, 3, std::dynamic_extent>> matrix(data.data(), 5);

    std::cout << "Mixed extents matrix (3x5):" << std::endl;
    for (size_t i = 0; i < matrix.extent(0); ++i) {
        for (size_t j = 0; j < matrix.extent(1); ++j) {
            std::cout << matrix[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 4. 不同内存布局 ==========

void layout_example() {
    std::cout << "\n=== 不同内存布局 ===" << std::endl;

    std::vector<int> data(12);
    std::iota(data.begin(), data.end(), 1);

    // 行优先布局 (默认)
    std::mdspan<int, std::extents<size_t, 3, 4>, std::layout_right> row_major(data.data());
    std::cout << "Row-major (layout_right):" << std::endl;
    for (size_t i = 0; i < row_major.extent(0); ++i) {
        for (size_t j = 0; j < row_major.extent(1); ++j) {
            std::cout << row_major[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    // 列优先布局
    std::mdspan<int, std::extents<size_t, 3, 4>, std::layout_left> col_major(data.data());
    std::cout << "\nColumn-major (layout_left):" << std::endl;
    for (size_t i = 0; i < col_major.extent(0); ++i) {
        for (size_t j = 0; j < col_major.extent(1); ++j) {
            std::cout << col_major[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    // 验证内存布局
    std::cout << "\nMemory layout verification:" << std::endl;
    std::cout << "Row-major [0,1] address offset: " << &row_major[0, 1] - data.data() << std::endl;
    std::cout << "Column-major [0,1] address offset: " << &col_major[0, 1] - data.data() << std::endl;
}

// ========== 5. 一维 mdspan ==========

void one_dimensional() {
    std::cout << "\n=== 一维 mdspan ===" << std::endl;

    std::vector<int> data = {1, 2, 3, 4, 5, 6, 7, 8};

    // 一维 mdspan
    std::mdspan<int, std::dextents<size_t, 1>> vec(data.data(), data.size());

    std::cout << "1D mdspan:" << std::endl;
    for (size_t i = 0; i < vec.extent(0); ++i) {
        std::cout << vec[i] << " ";
    }
    std::cout << std::endl;

    // 与 std::span 的区别
    std::cout << "mdspan size: " << vec.size() << std::endl;
    std::cout << "mdspan extent(0): " << vec.extent(0) << std::endl;
}

// ========== 6. 三维数组 ==========

void three_dimensional() {
    std::cout << "\n=== 三维数组 ===" << std::endl;

    // 2x3x4 的三维数组
    std::vector<int> data(24);
    std::iota(data.begin(), data.end(), 1);

    std::mdspan<int, std::dextents<size_t, 3>> tensor(data.data(), 2, 3, 4);

    std::cout << "3D tensor (2x3x4):" << std::endl;
    for (size_t i = 0; i < tensor.extent(0); ++i) {
        std::cout << "Layer " << i << ":" << std::endl;
        for (size_t j = 0; j < tensor.extent(1); ++j) {
            for (size_t k = 0; k < tensor.extent(2); ++k) {
                std::cout << tensor[i, j, k] << "\t";
            }
            std::cout << std::endl;
        }
        std::cout << std::endl;
    }
}

// ========== 7. 实际应用：图像处理 ==========

// 使用 mdspan 表示灰度图像
struct GrayImage {
    std::vector<uint8_t> pixels;
    size_t width, height;

    GrayImage(size_t w, size_t h) : pixels(w * h), width(w), height(h) {}

    auto as_mdspan() {
        return std::mdspan<uint8_t, std::dextents<size_t, 2>>(pixels.data(), height, width);
    }
};

// 图像处理函数
void apply_brightness(std::mdspan<uint8_t, std::dextents<size_t, 2>> image, int brightness) {
    for (size_t y = 0; y < image.extent(0); ++y) {
        for (size_t x = 0; x < image.extent(1); ++x) {
            int val = static_cast<int>(image[y, x]) + brightness;
            image[y, x] = static_cast<uint8_t>(std::clamp(val, 0, 255));
        }
    }
}

void image_processing_example() {
    std::cout << "\n=== 实际应用：图像处理 ===" << std::endl;

    // 创建一个 4x4 的灰度图像
    GrayImage img(4, 4);

    // 填充渐变
    auto view = img.as_mdspan();
    for (size_t y = 0; y < view.extent(0); ++y) {
        for (size_t x = 0; x < view.extent(1); ++x) {
            view[y, x] = static_cast<uint8_t>((y * 4 + x) * 16);
        }
    }

    // 打印原始图像
    std::cout << "Original image:" << std::endl;
    for (size_t y = 0; y < view.extent(0); ++y) {
        for (size_t x = 0; x < view.extent(1); ++x) {
            std::cout << static_cast<int>(view[y, x]) << "\t";
        }
        std::cout << std::endl;
    }

    // 增加亮度
    apply_brightness(view, 50);

    // 打印处理后的图像
    std::cout << "\nAfter brightness +50:" << std::endl;
    for (size_t y = 0; y < view.extent(0); ++y) {
        for (size_t x = 0; x < view.extent(1); ++x) {
            std::cout << static_cast<int>(view[y, x]) << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 8. 矩阵运算示例 ==========

void matrix_operations() {
    std::cout << "\n=== 矩阵运算 ===" << std::endl;

    // 创建矩阵
    std::vector<int> data_a = {1, 2, 3, 4, 5, 6};
    std::vector<int> data_b = {7, 8, 9, 10, 11, 12};
    std::vector<int> data_c(4, 0);

    std::mdspan<int, std::extents<size_t, 2, 3>> a(data_a.data());
    std::mdspan<int, std::extents<size_t, 3, 2>> b(data_b.data());
    std::mdspan<int, std::extents<size_t, 2, 2>> c(data_c.data());

    // 矩阵乘法: C = A * B
    for (size_t i = 0; i < a.extent(0); ++i) {
        for (size_t j = 0; j < b.extent(1); ++j) {
            for (size_t k = 0; k < a.extent(1); ++k) {
                c[i, j] += a[i, k] * b[k, j];
            }
        }
    }

    // 打印结果
    std::cout << "Matrix A (2x3):" << std::endl;
    for (size_t i = 0; i < a.extent(0); ++i) {
        for (size_t j = 0; j < a.extent(1); ++j) {
            std::cout << a[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    std::cout << "\nMatrix B (3x2):" << std::endl;
    for (size_t i = 0; i < b.extent(0); ++i) {
        for (size_t j = 0; j < b.extent(1); ++j) {
            std::cout << b[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    std::cout << "\nMatrix C = A * B (2x2):" << std::endl;
    for (size_t i = 0; i < c.extent(0); ++i) {
        for (size_t j = 0; j < c.extent(1); ++j) {
            std::cout << c[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 9. submdspan 示例 ==========

void submdspan_example() {
    std::cout << "\n=== submdspan (子视图) ===" << std::endl;

    std::vector<int> data(20);
    std::iota(data.begin(), data.end(), 1);

    std::mdspan<int, std::extents<size_t, 4, 5>> matrix(data.data());

    std::cout << "Original matrix (4x5):" << std::endl;
    for (size_t i = 0; i < matrix.extent(0); ++i) {
        for (size_t j = 0; j < matrix.extent(1); ++j) {
            std::cout << matrix[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    // 获取子视图 (第 1-2 行，第 1-3 列)
    auto sub = std::submdspan(matrix, std::pair{1, 3}, std::pair{1, 4});

    std::cout << "\nSubmatrix (rows 1-2, cols 1-3):" << std::endl;
    for (size_t i = 0; i < sub.extent(0); ++i) {
        for (size_t j = 0; j < sub.extent(1); ++j) {
            std::cout << sub[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::mdspan 示例\n" << std::endl;

    basic_usage();
    dynamic_extents();
    mixed_extents();
    layout_example();
    one_dimensional();
    three_dimensional();
    image_processing_example();
    matrix_operations();
    submdspan_example();

    return 0;
}
