#ifndef DISASTER_RECOVERY_STORAGE_EC_REED_SOLOMON_H_
#define DISASTER_RECOVERY_STORAGE_EC_REED_SOLOMON_H_

#include <cstdint>
#include <vector>
#include <memory>
#include "ec/galois_field.h"

namespace disaster_recovery {
namespace ec {

/**
 * @brief Reed-Solomon 编解码器
 *
 * 实现Reed-Solomon纠删码，将数据编码为k个数据块和m个校验块
 * 可以容忍任意m个块丢失而恢复原始数据
 *
 * @note 这是容灾存储的核心算法
 * @see https://en.wikipedia.org/wiki/Reed%E2%80%93Solomon_error_correction
 */
class ReedSolomon {
public:
    /**
     * @brief 构造函数
     *
     * @param data_shards 数据分片数 (k)
     * @param parity_shards 校验分片数 (m)
     *
     * @note 总分片数 = k + m
     * @note 可以容忍任意m个分片丢失
     */
    ReedSolomon(int data_shards, int parity_shards);

    /**
     * @brief 析构函数
     */
    ~ReedSolomon();

    /**
     * @brief 编码数据
     *
     * 将原始数据编码为多个分片
     *
     * @param data 原始数据指针
     * @param size 数据大小（字节）
     * @param shards 输出的分片列表
     * @return 0表示成功，非0表示失败
     *
     * @note 分片大小 = ceil(size / data_shards)
     * @note 最后一个分片可能会用0填充
     */
    int encode(const uint8_t* data, size_t size,
               std::vector<std::vector<uint8_t>>& shards);

    /**
     * @brief 解码数据
     *
     * 从可用的分片中恢复原始数据
     *
     * @param shards 分片列表（可以包含空分片）
     * @param shard_available 每个分片是否可用的标志
     * @param data 输出的原始数据
     * @return 0表示成功，非0表示失败
     *
     * @note 至少需要k个可用分片才能恢复
     */
    int decode(const std::vector<std::vector<uint8_t>>& shards,
               const std::vector<bool>& shard_available,
               std::vector<uint8_t>& data);

    /**
     * @brief 计算分片大小
     *
     * @param data_size 原始数据大小
     * @return 每个分片的大小
     */
    size_t calculateShardSize(size_t data_size) const;

    /**
     * @brief 获取数据分片数
     *
     * @return 数据分片数 (k)
     */
    int getDataShards() const { return data_shards_; }

    /**
     * @brief 获取校验分片数
     *
     * @return 校验分片数 (m)
     */
    int getParityShards() const { return parity_shards_; }

    /**
     * @brief 获取总分片数
     *
     * @return 总分片数 (k + m)
     */
    int getTotalShards() const { return data_shards_ + parity_shards_; }

    /**
     * @brief 检查是否可以恢复
     *
     * @param available_shards 可用分片数
     * @return true 如果可以恢复，false 否则
     */
    bool canRecover(int available_shards) const {
        return available_shards >= data_shards_;
    }

private:
    int data_shards_;      // 数据分片数 (k)
    int parity_shards_;    // 校验分片数 (m)
    int total_shards_;     // 总分片数 (k + m)

    GaloisField gf_;       // 有限域运算

    // 编码矩阵
    std::vector<std::vector<uint8_t>> encode_matrix_;

    // 是否已初始化
    bool initialized_ = false;

    /**
     * @brief 初始化编码矩阵
     *
     * 使用范德蒙德矩阵构造编码矩阵
     */
    void buildEncodeMatrix();

    /**
     * @brief 矩阵乘法
     *
     * @param matrix 矩阵
     * @param input 输入向量
     * @param output 输出向量
     */
    void matrixMultiply(const std::vector<std::vector<uint8_t>>& matrix,
                        const std::vector<uint8_t>& input,
                        std::vector<uint8_t>& output);

    /**
     * @brief 高斯消元求解
     *
     * 解线性方程组 Ax = b
     *
     * @param A 系数矩阵
     * @param b 右侧向量
     * @param x 解向量
     * @return 0表示成功，非0表示失败
     */
    int gaussianElimination(std::vector<std::vector<uint8_t>>& A,
                            std::vector<uint8_t>& b,
                            std::vector<uint8_t>& x);

    /**
     * @brief 矩阵求逆
     *
     * @param matrix 输入矩阵
     * @param inverse 输出的逆矩阵
     * @return 0表示成功，非0表示失败
     */
    int invertMatrix(const std::vector<std::vector<uint8_t>>& matrix,
                     std::vector<std::vector<uint8_t>>& inverse);

    /**
     * @brief 选择可用分片的子矩阵
     *
     * @param available 可用分片标志
     * @param submatrix 输出的子矩阵
     */
    void selectSubmatrix(const std::vector<bool>& available,
                         std::vector<std::vector<uint8_t>>& submatrix);

    /**
     * @brief 交换矩阵行
     *
     * @param matrix 矩阵
     * @param row1 行1
     * @param row2 行2
     */
    void swapRows(std::vector<std::vector<uint8_t>>& matrix,
                  int row1, int row2);

    /**
     * @brief 交换向量元素
     *
     * @param vec 向量
     * @param i 索引1
     * @param j 索引2
     */
    void swapElements(std::vector<uint8_t>& vec, int i, int j);
};

}  // namespace ec
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_EC_REED_SOLOMON_H_
