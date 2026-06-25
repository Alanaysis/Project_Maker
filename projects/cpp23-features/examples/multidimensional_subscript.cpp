/**
 * @file multidimensional_subscript.cpp
 * @brief C++23 多维下标运算符示例
 *
 * C++23 允许 operator[] 接受多个参数，支持多维数组访问。
 *
 * 主要特点：
 * - operator[] 可以接受多个参数
 * - 更自然的多维数组语法
 * - 与 Python 等语言的语法一致
 * - 支持自定义类型
 *
 * 编译命令：
 * g++ -std=c++23 -o multidimensional_subscript multidimensional_subscript.cpp
 */

#include <iostream>
#include <vector>
#include <stdexcept>

// ========== 1. 基本的多维数组类 ==========

template<typename T>
class Matrix {
private:
    std::vector<T> data_;
    size_t rows_, cols_;

public:
    Matrix(size_t rows, size_t cols)
        : data_(rows * cols), rows_(rows), cols_(cols) {}

    // C++23 多维下标运算符
    T& operator[](size_t row, size_t col) {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Matrix index out of range");
        }
        return data_[row * cols_ + col];
    }

    const T& operator[](size_t row, size_t col) const {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Matrix index out of range");
        }
        return data_[row * cols_ + col];
    }

    size_t rows() const { return rows_; }
    size_t cols() const { return cols_; }
};

// ========== 2. 三维张量类 ==========

template<typename T>
class Tensor3D {
private:
    std::vector<T> data_;
    size_t dim1_, dim2_, dim3_;

public:
    Tensor3D(size_t d1, size_t d2, size_t d3)
        : data_(d1 * d2 * d3), dim1_(d1), dim2_(d2), dim3_(d3) {}

    // 三维下标
    T& operator[](size_t i, size_t j, size_t k) {
        if (i >= dim1_ || j >= dim2_ || k >= dim3_) {
            throw std::out_of_range("Tensor index out of range");
        }
        return data_[i * dim2_ * dim3_ + j * dim3_ + k];
    }

    const T& operator[](size_t i, size_t j, size_t k) const {
        if (i >= dim1_ || j >= dim2_ || k >= dim3_) {
            throw std::out_of_range("Tensor index out of range");
        }
        return data_[i * dim2_ * dim3_ + j * dim3_ + k];
    }

    size_t dim1() const { return dim1_; }
    size_t dim2() const { return dim2_; }
    size_t dim3() const { return dim3_; }
};

// ========== 3. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建 3x4 矩阵
    Matrix<int> mat(3, 4);

    // 使用多维下标访问
    mat[0, 0] = 1;
    mat[0, 1] = 2;
    mat[1, 2] = 100;
    mat[2, 3] = 200;

    std::cout << "Matrix (3x4):" << std::endl;
    for (size_t i = 0; i < mat.rows(); ++i) {
        for (size_t j = 0; j < mat.cols(); ++j) {
            std::cout << mat[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 4. 三维张量 ==========

void tensor_example() {
    std::cout << "\n=== 三维张量 ===" << std::endl;

    // 创建 2x3x4 张量
    Tensor3D<int> tensor(2, 3, 4);

    // 填充数据
    int value = 1;
    for (size_t i = 0; i < tensor.dim1(); ++i) {
        for (size_t j = 0; j < tensor.dim2(); ++j) {
            for (size_t k = 0; k < tensor.dim3(); ++k) {
                tensor[i, j, k] = value++;
            }
        }
    }

    // 打印张量
    std::cout << "Tensor (2x3x4):" << std::endl;
    for (size_t i = 0; i < tensor.dim1(); ++i) {
        std::cout << "Layer " << i << ":" << std::endl;
        for (size_t j = 0; j < tensor.dim2(); ++j) {
            for (size_t k = 0; k < tensor.dim3(); ++k) {
                std::cout << tensor[i, j, k] << "\t";
            }
            std::cout << std::endl;
        }
        std::cout << std::endl;
    }
}

// ========== 5. 实际应用：图像像素访问 ==========

class Image {
private:
    std::vector<uint8_t> pixels_;
    size_t width_, height_;

public:
    Image(size_t w, size_t h) : pixels_(w * h), width_(w), height_(h) {}

    // 使用多维下标访问像素
    uint8_t& operator[](size_t x, size_t y) {
        if (x >= width_ || y >= height_) {
            throw std::out_of_range("Pixel index out of range");
        }
        return pixels_[y * width_ + x];
    }

    const uint8_t& operator[](size_t x, size_t y) const {
        if (x >= width_ || y >= height_) {
            throw std::out_of_range("Pixel index out of range");
        }
        return pixels_[y * width_ + x];
    }

    size_t width() const { return width_; }
    size_t height() const { return height_; }
};

void image_example() {
    std::cout << "\n=== 实际应用：图像像素访问 ===" << std::endl;

    Image img(4, 4);

    // 设置像素值
    for (size_t y = 0; y < img.height(); ++y) {
        for (size_t x = 0; x < img.width(); ++x) {
            img[x, y] = static_cast<uint8_t>((x + y) * 32);
        }
    }

    // 打印图像
    std::cout << "Image pixels:" << std::endl;
    for (size_t y = 0; y < img.height(); ++y) {
        for (size_t x = 0; x < img.width(); ++x) {
            std::cout << static_cast<int>(img[x, y]) << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 6. 实际应用：游戏地图 ==========

class GameMap {
private:
    std::vector<char> tiles_;
    size_t width_, height_;

public:
    GameMap(size_t w, size_t h, char fill = '.')
        : tiles_(w * h, fill), width_(w), height_(h) {}

    char& operator[](size_t x, size_t y) {
        if (x >= width_ || y >= height_) {
            throw std::out_of_range("Map index out of range");
        }
        return tiles_[y * width_ + x];
    }

    const char& operator[](size_t x, size_t y) const {
        if (x >= width_ || y >= height_) {
            throw std::out_of_range("Map index out of range");
        }
        return tiles_[y * width_ + x];
    }

    void print() const {
        for (size_t y = 0; y < height_; ++y) {
            for (size_t x = 0; x < width_; ++x) {
                std::cout << (*this)[x, y];
            }
            std::cout << std::endl;
        }
    }

    size_t width() const { return width_; }
    size_t height() const { return height_; }
};

void game_map_example() {
    std::cout << "\n=== 实际应用：游戏地图 ===" << std::endl;

    GameMap map(8, 6, '.');

    // 设置墙壁
    map[0, 0] = '#';
    map[7, 0] = '#';
    map[0, 5] = '#';
    map[7, 5] = '#';

    // 设置玩家
    map[3, 2] = 'P';

    // 设置宝箱
    map[6, 4] = 'T';

    std::cout << "Game map:" << std::endl;
    map.print();
}

// ========== 7. 实际应用：矩阵运算 ==========

void matrix_operations() {
    std::cout << "\n=== 实际应用：矩阵运算 ===" << std::endl;

    // 创建矩阵
    Matrix<int> a(2, 3);
    Matrix<int> b(3, 2);
    Matrix<int> c(2, 2, 0);

    // 初始化矩阵 A
    a[0, 0] = 1; a[0, 1] = 2; a[0, 2] = 3;
    a[1, 0] = 4; a[1, 1] = 5; a[1, 2] = 6;

    // 初始化矩阵 B
    b[0, 0] = 7; b[0, 1] = 8;
    b[1, 0] = 9; b[1, 1] = 10;
    b[2, 0] = 11; b[2, 1] = 12;

    // 矩阵乘法: C = A * B
    for (size_t i = 0; i < a.rows(); ++i) {
        for (size_t j = 0; j < b.cols(); ++j) {
            for (size_t k = 0; k < a.cols(); ++k) {
                c[i, j] += a[i, k] * b[k, j];
            }
        }
    }

    // 打印结果
    std::cout << "Matrix A:" << std::endl;
    for (size_t i = 0; i < a.rows(); ++i) {
        for (size_t j = 0; j < a.cols(); ++j) {
            std::cout << a[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    std::cout << "\nMatrix B:" << std::endl;
    for (size_t i = 0; i < b.rows(); ++i) {
        for (size_t j = 0; j < b.cols(); ++j) {
            std::cout << b[i, j] << "\t";
        }
        std::cout << std::endl;
    }

    std::cout << "\nMatrix C = A * B:" << std::endl;
    for (size_t i = 0; i < c.rows(); ++i) {
        for (size_t j = 0; j < c.cols(); ++j) {
            std::cout << c[i, j] << "\t";
        }
        std::cout << std::endl;
    }
}

// ========== 8. 实际应用：统计表 ==========

class StatTable {
private:
    std::vector<double> data_;
    size_t rows_, cols_;
    std::vector<std::string> row_names_;
    std::vector<std::string> col_names_;

public:
    StatTable(size_t rows, size_t cols)
        : data_(rows * cols, 0.0), rows_(rows), cols_(cols) {}

    void set_row_names(std::vector<std::string> names) { row_names_ = std::move(names); }
    void set_col_names(std::vector<std::string> names) { col_names_ = std::move(names); }

    double& operator[](size_t row, size_t col) {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Table index out of range");
        }
        return data_[row * cols_ + col];
    }

    const double& operator[](size_t row, size_t col) const {
        if (row >= rows_ || col >= cols_) {
            throw std::out_of_range("Table index out of range");
        }
        return data_[row * cols_ + col];
    }

    void print() const {
        // 打印列名
        if (!col_names_.empty()) {
            std::cout << "\t";
            for (const auto& name : col_names_) {
                std::cout << name << "\t";
            }
            std::cout << std::endl;
        }

        // 打印数据
        for (size_t i = 0; i < rows_; ++i) {
            if (!row_names_.empty()) {
                std::cout << row_names_[i] << "\t";
            }
            for (size_t j = 0; j < cols_; ++j) {
                std::cout << (*this)[i, j] << "\t";
            }
            std::cout << std::endl;
        }
    }
};

void stat_table_example() {
    std::cout << "\n=== 实际应用：统计表 ===" << std::endl;

    StatTable table(3, 4);
    table.set_row_names({"Q1", "Q2", "Q3"});
    table.set_col_names({"Jan", "Feb", "Mar", "Apr"});

    // 填充数据
    table[0, 0] = 100; table[0, 1] = 120; table[0, 2] = 130; table[0, 3] = 115;
    table[1, 0] = 150; table[1, 1] = 160; table[1, 2] = 170; table[1, 3] = 165;
    table[2, 0] = 200; table[2, 1] = 210; table[2, 2] = 220; table[2, 3] = 215;

    std::cout << "Sales statistics:" << std::endl;
    table.print();
}

int main() {
    std::cout << "C++23 多维下标运算符示例\n" << std::endl;

    basic_usage();
    tensor_example();
    image_example();
    game_map_example();
    matrix_operations();
    stat_table_example();

    return 0;
}
