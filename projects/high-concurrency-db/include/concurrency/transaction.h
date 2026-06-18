#pragma once

#include "core/common.h"
#include "core/config.h"
#include <set>
#include <mutex>
#include <atomic>

namespace minidb {

// 事务状态
enum class TransactionState {
    GROWING,    // 增长阶段 (获取锁)
    SHRINKING,  // 收缩阶段 (释放锁)
    COMMITTED,  // 已提交
    ABORTED     // 已中止
};

/**
 * @brief 事务类
 *
 * 代表一个数据库事务，管理：
 * - 事务状态
 * - 持有的锁
 * - 事务 ID
 */
class Transaction {
public:
    /**
     * @brief 构造函数
     * @param txn_id 事务 ID
     * @param isolation_level 隔离级别
     */
    explicit Transaction(transaction_id_t txn_id,
                         IsolationLevel isolation_level = DEFAULT_ISOLATION_LEVEL);

    /**
     * @brief 析构函数
     */
    ~Transaction() = default;

    /**
     * @brief 获取事务 ID
     * @return 事务 ID
     */
    transaction_id_t getTransactionId() const { return txn_id_; }

    /**
     * @brief 获取事务状态
     * @return 事务状态
     */
    TransactionState getState() const { return state_; }

    /**
     * @brief 设置事务状态
     * @param state 新状态
     */
    void setState(TransactionState state);

    /**
     * @brief 获取隔离级别
     * @return 隔离级别
     */
    IsolationLevel getIsolationLevel() const { return isolation_level_; }

    /**
     * @brief 添加已锁定的资源
     * @param resource 资源标识
     */
    void addLockedResource(const std::string& resource);

    /**
     * @brief 移除已锁定的资源
     * @param resource 资源标识
     */
    void removeLockedResource(const std::string& resource);

    /**
     * @brief 获取已锁定的资源列表
     * @return 资源列表
     */
    std::set<std::string> getLockedResources() const;

    /**
     * @brief 检查是否已锁定某个资源
     * @param resource 资源标识
     * @return 是否已锁定
     */
    bool hasLocked(const std::string& resource) const;

    /**
     * @brief 开始事务
     */
    void begin();

    /**
     * @brief 提交事务
     */
    void commit();

    /**
     * @brief 中止事务
     */
    void abort();

    /**
     * @brief 检查事务是否活跃
     * @return 是否活跃
     */
    bool isActive() const {
        return state_ == TransactionState::GROWING ||
               state_ == TransactionState::SHRINKING;
    }

private:
    transaction_id_t txn_id_;           // 事务 ID
    TransactionState state_;            // 事务状态
    IsolationLevel isolation_level_;    // 隔离级别
    std::set<std::string> locked_resources_;  // 已锁定的资源
    mutable std::mutex latch_;          // 互斥锁
};

/**
 * @brief 事务管理器
 *
 * 管理事务的创建、提交和中止
 */
class TransactionManager {
public:
    TransactionManager() : next_txn_id_(1) {}
    ~TransactionManager() = default;

    /**
     * @brief 创建新事务
     * @return 事务指针
     */
    Transaction* begin();

    /**
     * @brief 提交事务
     * @param txn 事务
     */
    void commit(Transaction* txn);

    /**
     * @brief 中止事务
     * @param txn 事务
     */
    void abort(Transaction* txn);

    /**
     * @brief 获取事务
     * @param txn_id 事务 ID
     * @return 事务指针，如果不存在返回 nullptr
     */
    Transaction* getTransaction(transaction_id_t txn_id);

    /**
     * @brief 获取活跃事务数量
     * @return 活跃事务数量
     */
    size_t getActiveTransactionCount() const;

private:
    std::atomic<transaction_id_t> next_txn_id_;
    std::unordered_map<transaction_id_t, std::unique_ptr<Transaction>> transactions_;
    std::mutex latch_;
};

}  // namespace minidb
