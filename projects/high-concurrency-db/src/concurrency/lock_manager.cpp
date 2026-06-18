#include "concurrency/lock_manager.h"
#include <iostream>
#include <chrono>

namespace minidb {

bool LockManager::lockShared(Transaction* txn, const std::string& resource) {
    if (!txn) return false;

    std::unique_lock<std::mutex> lock_table_lock(lock_table_latch_);

    // 获取或创建锁请求队列
    auto it = lock_table_.find(resource);
    if (it == lock_table_.end()) {
        auto queue = std::make_shared<LockRequestQueue>();
        lock_table_[resource] = queue;
        it = lock_table_.find(resource);
    }

    auto queue = it->second;
    lock_table_lock.unlock();

    // 在队列级别加锁
    std::unique_lock<std::mutex> queue_lock(queue->mutex);

    // 检查事务是否已持有该资源的锁
    for (auto& req : queue->request_queue) {
        if (req.txn_id == txn->getTransactionId() && req.granted) {
            if (req.mode == LockMode::EXCLUSIVE) {
                // 已持有排他锁，共享锁请求自动满足
                return true;
            }
            // 已持有共享锁，不需要再次获取
            return true;
        }
    }

    // 创建锁请求
    LockRequest request(txn->getTransactionId(), LockMode::SHARED);
    queue->request_queue.push_back(request);

    // 等待锁授予
    while (true) {
        // 检查是否可以授予锁
        bool can_grant = true;
        for (auto& req : queue->request_queue) {
            if (req.granted && req.mode == LockMode::EXCLUSIVE) {
                can_grant = false;
                break;
            }
        }

        if (can_grant) {
            // 授予锁
            for (auto& req : queue->request_queue) {
                if (req.txn_id == txn->getTransactionId() &&
                    req.mode == LockMode::SHARED && !req.granted) {
                    req.granted = true;
                    break;
                }
            }
            txn->addLockedResource(resource);
            return true;
        }

        // 等待
        queue->cv.wait_for(queue_lock, std::chrono::milliseconds(LOCK_TIMEOUT_MS));

        // 检查超时
        if (txn->getState() == TransactionState::ABORTED) {
            // 事务已中止，移除请求
            queue->request_queue.remove_if(
                [&](const LockRequest& r) {
                    return r.txn_id == txn->getTransactionId() && !r.granted;
                });
            return false;
        }
    }

    return false;
}

bool LockManager::lockExclusive(Transaction* txn, const std::string& resource) {
    if (!txn) return false;

    std::unique_lock<std::mutex> lock_table_lock(lock_table_latch_);

    // 获取或创建锁请求队列
    auto it = lock_table_.find(resource);
    if (it == lock_table_.end()) {
        auto queue = std::make_shared<LockRequestQueue>();
        lock_table_[resource] = queue;
        it = lock_table_.find(resource);
    }

    auto queue = it->second;
    lock_table_lock.unlock();

    // 在队列级别加锁
    std::unique_lock<std::mutex> queue_lock(queue->mutex);

    // 检查事务是否已持有该资源的锁
    for (auto& req : queue->request_queue) {
        if (req.txn_id == txn->getTransactionId() && req.granted) {
            if (req.mode == LockMode::EXCLUSIVE) {
                // 已持有排他锁
                return true;
            }
            // 已持有共享锁，需要升级
            return lockUpgrade(txn, resource);
        }
    }

    // 创建锁请求
    LockRequest request(txn->getTransactionId(), LockMode::EXCLUSIVE);
    queue->request_queue.push_back(request);

    // 等待锁授予
    while (true) {
        // 检查是否可以授予锁
        bool can_grant = true;
        for (auto& req : queue->request_queue) {
            if (req.granted && req.txn_id != txn->getTransactionId()) {
                can_grant = false;
                break;
            }
        }

        if (can_grant) {
            // 授予锁
            for (auto& req : queue->request_queue) {
                if (req.txn_id == txn->getTransactionId() &&
                    req.mode == LockMode::EXCLUSIVE && !req.granted) {
                    req.granted = true;
                    break;
                }
            }
            txn->addLockedResource(resource);
            return true;
        }

        // 等待
        queue->cv.wait_for(queue_lock, std::chrono::milliseconds(LOCK_TIMEOUT_MS));

        // 检查超时
        if (txn->getState() == TransactionState::ABORTED) {
            // 事务已中止，移除请求
            queue->request_queue.remove_if(
                [&](const LockRequest& r) {
                    return r.txn_id == txn->getTransactionId() && !r.granted;
                });
            return false;
        }
    }

    return false;
}

bool LockManager::lockUpgrade(Transaction* txn, const std::string& resource) {
    if (!txn) return false;

    std::unique_lock<std::mutex> lock_table_lock(lock_table_latch_);

    auto it = lock_table_.find(resource);
    if (it == lock_table_.end()) {
        return false;
    }

    auto queue = it->second;
    lock_table_lock.unlock();

    std::unique_lock<std::mutex> queue_lock(queue->mutex);

    // 检查是否有其他升级进行中
    if (queue->upgrading) {
        return false;
    }

    // 查找共享锁请求
    for (auto& req : queue->request_queue) {
        if (req.txn_id == txn->getTransactionId() &&
            req.mode == LockMode::SHARED && req.granted) {

            queue->upgrading = true;

            // 等待其他锁释放
            while (true) {
                bool can_upgrade = true;
                for (auto& other_req : queue->request_queue) {
                    if (other_req.granted &&
                        other_req.txn_id != txn->getTransactionId()) {
                        can_upgrade = false;
                        break;
                    }
                }

                if (can_upgrade) {
                    // 升级锁
                    req.mode = LockMode::EXCLUSIVE;
                    queue->upgrading = false;
                    return true;
                }

                queue->cv.wait_for(queue_lock,
                                   std::chrono::milliseconds(LOCK_TIMEOUT_MS));

                if (txn->getState() == TransactionState::ABORTED) {
                    queue->upgrading = false;
                    return false;
                }
            }
        }
    }

    return false;
}

bool LockManager::unlock(Transaction* txn, const std::string& resource) {
    if (!txn) return false;

    std::unique_lock<std::mutex> lock_table_lock(lock_table_latch_);

    auto it = lock_table_.find(resource);
    if (it == lock_table_.end()) {
        return false;
    }

    auto queue = it->second;
    lock_table_lock.unlock();

    std::unique_lock<std::mutex> queue_lock(queue->mutex);

    // 移除锁请求
    queue->request_queue.remove_if(
        [&](const LockRequest& r) {
            return r.txn_id == txn->getTransactionId();
        });

    txn->removeLockedResource(resource);

    // 通知等待的事务
    queue->cv.notify_all();

    return true;
}

void LockManager::unlockAll(Transaction* txn) {
    if (!txn) return;

    auto resources = txn->getLockedResources();
    for (const auto& resource : resources) {
        unlock(txn, resource);
    }
}

bool LockManager::isCompatible(const LockRequestQueue& queue, LockMode mode,
                                transaction_id_t txn_id) {
    for (const auto& req : queue.request_queue) {
        if (!req.granted) continue;
        if (req.txn_id == txn_id) continue;

        // 检查兼容性
        if (mode == LockMode::SHARED && req.mode == LockMode::EXCLUSIVE) {
            return false;
        }
        if (mode == LockMode::EXCLUSIVE) {
            return false;
        }
    }
    return true;
}

void LockManager::grantLock(LockRequestQueue& queue, LockRequest& request) {
    request.granted = true;
}

}  // namespace minidb
