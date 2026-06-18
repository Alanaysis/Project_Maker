#pragma once

#include "core/common.h"
#include "concurrency/transaction.h"
#include <unordered_map>
#include <list>
#include <mutex>
#include <condition_variable>
#include <memory>

namespace minidb {

// 锁模式
enum class LockMode {
    SHARED,     // 共享锁 (读锁)
    EXCLUSIVE   // 排他锁 (写锁)
};

// 锁请求
struct LockRequest {
    transaction_id_t txn_id;
    LockMode mode;
    bool granted;

    LockRequest(transaction_id_t id, LockMode m)
        : txn_id(id), mode(m), granted(false) {}
};

// 锁请求队列
struct LockRequestQueue {
    std::list<LockRequest> request_queue;
    bool upgrading = false;  // 是否有锁升级进行中
    std::mutex mutex;
    std::condition_variable cv;
};

/**
 * @brief 锁管理器
 *
 * 管理表级和行级锁，支持：
 * - 共享锁 (读锁)
 * - 排他锁 (写锁)
 * - 锁升级
 * - 死锁检测 (简化版)
 */
class LockManager {
public:
    LockManager() = default;
    ~LockManager() = default;

    // 禁止拷贝
    LockManager(const LockManager&) = delete;
    LockManager& operator=(const LockManager&) = delete;

    /**
     * @brief 获取共享锁
     * @param txn 事务
     * @param resource 资源标识 (如表名)
     * @return 是否成功
     */
    bool lockShared(Transaction* txn, const std::string& resource);

    /**
     * @brief 获取排他锁
     * @param txn 事务
     * @param resource 资源标识 (如表名)
     * @return 是否成功
     */
    bool lockExclusive(Transaction* txn, const std::string& resource);

    /**
     * @brief 锁升级 (共享锁 -> 排他锁)
     * @param txn 事务
     * @param resource 资源标识
     * @return 是否成功
     */
    bool lockUpgrade(Transaction* txn, const std::string& resource);

    /**
     * @brief 释放锁
     * @param txn 事务
     * @param resource 资源标识
     * @return 是否成功
     */
    bool unlock(Transaction* txn, const std::string& resource);

    /**
     * @brief 释放事务的所有锁
     * @param txn 事务
     */
    void unlockAll(Transaction* txn);

private:
    /**
     * @brief 检查锁兼容性
     * @param queue 锁请求队列
     * @param mode 请求的锁模式
     * @param txn_id 事务 ID
     * @return 是否兼容
     */
    bool isCompatible(const LockRequestQueue& queue, LockMode mode,
                      transaction_id_t txn_id);

    /**
     * @brief 授予锁
     * @param queue 锁请求队列
     * @param request 锁请求
     */
    void grantLock(LockRequestQueue& queue, LockRequest& request);

    // 锁表: resource -> LockRequestQueue
    std::unordered_map<std::string, std::shared_ptr<LockRequestQueue>> lock_table_;

    // 锁表的锁
    std::mutex lock_table_latch_;
};

}  // namespace minidb
