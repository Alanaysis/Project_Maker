#include "ec/reed_solomon.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <cstring>

namespace disaster_recovery {
namespace ec {

ReedSolomon::ReedSolomon(int data_shards, int parity_shards)
    : data_shards_(data_shards),
      parity_shards_(parity_shards),
      total_shards_(data_shards + parity_shards),
      initialized_(false) {
    if (data_shards <= 0 || parity_shards <= 0) {
        throw std::invalid_argument("Shard counts must be positive");
    }
    if (total_shards_ > 256) {
        throw std::invalid_argument("Total shards cannot exceed 256");
    }

    // 初始化有限域
    gf_.init();

    // 构建编码矩阵
    buildEncodeMatrix();

    initialized_ = true;
}

ReedSolomon::~ReedSolomon() = default;

void ReedSolomon::buildEncodeMatrix() {
    // 使用范德蒙德矩阵构造编码矩阵
    // 编码矩阵大小: total_shards_ x data_shards_
    encode_matrix_.resize(total_shards_,
                          std::vector<uint8_t>(data_shards_));

    // 前k行是单位矩阵（数据分片）
    for (int i = 0; i < data_shards_; i++) {
        for (int j = 0; j < data_shards_; j++) {
            encode_matrix_[i][j] = (i == j) ? 1 : 0;
        }
    }

    // 后m行是范德蒙德矩阵（校验分片）
    for (int i = 0; i < parity_shards_; i++) {
        for (int j = 0; j < data_shards_; j++) {
            // V(i,j) = α^(i*j)，其中α是本原元
            encode_matrix_[data_shards_ + i][j] =
                gf_.power(2, i * j);
        }
    }
}

int ReedSolomon::encode(const uint8_t* data, size_t size,
                        std::vector<std::vector<uint8_t>>& shards) {
    if (!initialized_) {
        return -1;
    }
    if (data == nullptr || size == 0) {
        return -1;
    }

    // 计算分片大小
    size_t shard_size = calculateShardSize(size);

    // 初始化分片
    shards.resize(total_shards_);
    for (auto& shard : shards) {
        shard.resize(shard_size, 0);
    }

    // 将数据复制到数据分片
    size_t offset = 0;
    for (int i = 0; i < data_shards_; i++) {
        if (offset >= size) break;  // 防止 size - offset 无符号下溢
        size_t copy_size = std::min(shard_size, size - offset);
        if (copy_size > 0) {
            std::memcpy(shards[i].data(), data + offset, copy_size);
        }
        offset += copy_size;
    }

    // 计算校验分片
    // 校验分片 = 编码矩阵 * 数据分片
    for (int i = 0; i < parity_shards_; i++) {
        for (size_t j = 0; j < shard_size; j++) {
            uint8_t sum = 0;
            for (int k = 0; k < data_shards_; k++) {
                sum = gf_.add(sum,
                    gf_.multiply(encode_matrix_[data_shards_ + i][k],
                                shards[k][j]));
            }
            shards[data_shards_ + i][j] = sum;
        }
    }

    return 0;
}

int ReedSolomon::decode(const std::vector<std::vector<uint8_t>>& shards,
                        const std::vector<bool>& shard_available,
                        std::vector<uint8_t>& data) {
    if (!initialized_) {
        return -1;
    }
    if (shards.size() != static_cast<size_t>(total_shards_)) {
        return -1;
    }
    if (shard_available.size() != static_cast<size_t>(total_shards_)) {
        return -1;
    }

    // 检查是否有足够的可用分片
    int available_count = 0;
    for (bool available : shard_available) {
        if (available) available_count++;
    }
    if (available_count < data_shards_) {
        return -1;  // 无法恢复
    }

    // 选择k个可用分片
    std::vector<int> available_indices;
    for (int i = 0; i < total_shards_ && available_indices.size() < static_cast<size_t>(data_shards_); i++) {
        if (shard_available[i]) {
            available_indices.push_back(i);
        }
    }

    // 构造解码矩阵
    // 从编码矩阵中选择对应的行
    std::vector<std::vector<uint8_t>> decode_matrix(
        data_shards_, std::vector<uint8_t>(data_shards_));
    for (int i = 0; i < data_shards_; i++) {
        for (int j = 0; j < data_shards_; j++) {
            decode_matrix[i][j] = encode_matrix_[available_indices[i]][j];
        }
    }

    // 求解解码矩阵的逆
    std::vector<std::vector<uint8_t>> inverse_matrix;
    if (invertMatrix(decode_matrix, inverse_matrix) != 0) {
        return -1;  // 矩阵不可逆
    }

    // 获取分片大小
    size_t shard_size = shards[0].size();

    // 初始化输出数据
    data.resize(data_shards_ * shard_size, 0);

    // 使用解码矩阵恢复数据
    for (int i = 0; i < data_shards_; i++) {
        for (size_t j = 0; j < shard_size; j++) {
            uint8_t sum = 0;
            for (int k = 0; k < data_shards_; k++) {
                sum = gf_.add(sum,
                    gf_.multiply(inverse_matrix[i][k],
                                shards[available_indices[k]][j]));
            }
            data[i * shard_size + j] = sum;
        }
    }

    return 0;
}

size_t ReedSolomon::calculateShardSize(size_t data_size) const {
    // 向上取整
    return (data_size + data_shards_ - 1) / data_shards_;
}

void ReedSolomon::matrixMultiply(
    const std::vector<std::vector<uint8_t>>& matrix,
    const std::vector<uint8_t>& input,
    std::vector<uint8_t>& output) {
    int rows = matrix.size();
    int cols = matrix[0].size();

    output.resize(rows, 0);
    for (int i = 0; i < rows; i++) {
        uint8_t sum = 0;
        for (int j = 0; j < cols; j++) {
            sum = gf_.add(sum, gf_.multiply(matrix[i][j], input[j]));
        }
        output[i] = sum;
    }
}

int ReedSolomon::gaussianElimination(
    std::vector<std::vector<uint8_t>>& A,
    std::vector<uint8_t>& b,
    std::vector<uint8_t>& x) {
    int n = A.size();

    // 前向消元
    for (int i = 0; i < n; i++) {
        // 选主元（选择非零元素）
        int pivot = -1;
        for (int j = i; j < n; j++) {
            if (A[j][i] != 0) {
                pivot = j;
                break;
            }
        }

        if (pivot == -1) {
            return -1;  // 矩阵奇异
        }

        // 交换行
        if (pivot != i) {
            swapRows(A, i, pivot);
            swapElements(b, i, pivot);
        }

        // 归一化
        uint8_t inv = gf_.inverse(A[i][i]);
        for (int j = i; j < n; j++) {
            A[i][j] = gf_.multiply(A[i][j], inv);
        }
        b[i] = gf_.multiply(b[i], inv);

        // 消元
        for (int j = i + 1; j < n; j++) {
            if (A[j][i] != 0) {
                uint8_t factor = A[j][i];
                for (int k = i; k < n; k++) {
                    A[j][k] = gf_.subtract(A[j][k],
                        gf_.multiply(factor, A[i][k]));
                }
                b[j] = gf_.subtract(b[j],
                    gf_.multiply(factor, b[i]));
            }
        }
    }

    // 回代
    x.resize(n, 0);
    for (int i = n - 1; i >= 0; i--) {
        x[i] = b[i];
        for (int j = i + 1; j < n; j++) {
            x[i] = gf_.subtract(x[i],
                gf_.multiply(A[i][j], x[j]));
        }
    }

    return 0;
}

int ReedSolomon::invertMatrix(
    const std::vector<std::vector<uint8_t>>& matrix,
    std::vector<std::vector<uint8_t>>& inverse) {
    int n = matrix.size();

    // 创建增广矩阵 [A | I]
    std::vector<std::vector<uint8_t>> augmented(
        n, std::vector<uint8_t>(2 * n, 0));

    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            augmented[i][j] = matrix[i][j];
        }
        augmented[i][n + i] = 1;
    }

    // 高斯-约旦消元
    for (int i = 0; i < n; i++) {
        // 选主元
        int pivot = -1;
        for (int j = i; j < n; j++) {
            if (augmented[j][i] != 0) {
                pivot = j;
                break;
            }
        }

        if (pivot == -1) {
            return -1;  // 矩阵不可逆
        }

        // 交换行
        if (pivot != i) {
            std::swap(augmented[i], augmented[pivot]);
        }

        // 归一化
        uint8_t inv = gf_.inverse(augmented[i][i]);
        for (int j = 0; j < 2 * n; j++) {
            augmented[i][j] = gf_.multiply(augmented[i][j], inv);
        }

        // 消元
        for (int j = 0; j < n; j++) {
            if (j != i && augmented[j][i] != 0) {
                uint8_t factor = augmented[j][i];
                for (int k = 0; k < 2 * n; k++) {
                    augmented[j][k] = gf_.subtract(augmented[j][k],
                        gf_.multiply(factor, augmented[i][k]));
                }
            }
        }
    }

    // 提取逆矩阵
    inverse.resize(n, std::vector<uint8_t>(n));
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            inverse[i][j] = augmented[i][n + j];
        }
    }

    return 0;
}

void ReedSolomon::selectSubmatrix(
    const std::vector<bool>& available,
    std::vector<std::vector<uint8_t>>& submatrix) {
    std::vector<int> indices;
    for (int i = 0; i < total_shards_; i++) {
        if (available[i]) {
            indices.push_back(i);
        }
    }

    submatrix.resize(data_shards_,
                     std::vector<uint8_t>(data_shards_));
    for (int i = 0; i < data_shards_; i++) {
        for (int j = 0; j < data_shards_; j++) {
            submatrix[i][j] = encode_matrix_[indices[i]][j];
        }
    }
}

void ReedSolomon::swapRows(
    std::vector<std::vector<uint8_t>>& matrix,
    int row1, int row2) {
    std::swap(matrix[row1], matrix[row2]);
}

void ReedSolomon::swapElements(
    std::vector<uint8_t>& vec,
    int i, int j) {
    std::swap(vec[i], vec[j]);
}

}  // namespace ec
}  // namespace disaster_recovery
