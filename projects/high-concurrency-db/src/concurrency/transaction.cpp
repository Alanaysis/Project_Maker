#include "concurrency/transaction.h"
#include <iostream>

namespace minidb {

// ==================== Transaction ====================

Transaction::Transaction(transaction_id_t txn_id, IsolationLevel isolation_level)
    : txn_id_(txn_id), state_(TransactionState::GROWING),
      isolation_level_(isolation_level) {
    MINIDB_LOG("Transaction created: " + std::to_string(txn_id));
}

void Transaction::setState(TransactionState state) {
    std::lock_guard<std::mutex> lock(latch_);
    state_ = state;
}

void Transaction::addLockedResource(const std::string& resource) {
    std::lock_guard<std::mutex> lock(latch_);
    locked_resources_.insert(resource);
}

void Transaction::removeLockedResource(const std::string& resource) {
    std::lock_guard<std::mutex> lock(latch_);
    locked_resources_.erase(resource);
}

std::set<std::string> Transaction::getLockedResources() const {
    std::lock_guard<std::mutex> lock(latch_);
    return locked_resources_;
}

bool Transaction::hasLocked(const std::string& resource) const {
    std::lock_guard<std::mutex> lock(latch_);
    return locked_resources_.find(resource) != locked_resources_.end();
}

void Transaction::begin() {
    std::lock_guard<std::mutex> lock(latch_);
    state_ = TransactionState::GROWING;
    MINIDB_LOG("Transaction " + std::to_string(txn_id_) + " began");
}

void Transaction::commit() {
    std::lock_guard<std::mutex> lock(latch_);
    state_ = TransactionState::COMMITTED;
    MINIDB_LOG("Transaction " + std::to_string(txn_id_) + " committed");
}

void Transaction::abort() {
    std::lock_guard<std::mutex> lock(latch_);
    state_ = TransactionState::ABORTED;
    MINIDB_LOG("Transaction " + std::to_string(txn_id_) + " aborted");
}

// ==================== TransactionManager ====================

Transaction* TransactionManager::begin() {
    std::lock_guard<std::mutex> lock(latch_);

    transaction_id_t txn_id = next_txn_id_.fetch_add(1);
    auto txn = std::make_unique<Transaction>(txn_id);
    Transaction* txn_ptr = txn.get();

    transactions_[txn_id] = std::move(txn);

    MINIDB_LOG("TransactionManager: Created transaction " +
               std::to_string(txn_id));
    return txn_ptr;
}

void TransactionManager::commit(Transaction* txn) {
    if (!txn) return;

    std::lock_guard<std::mutex> lock(latch_);

    txn->commit();

    // 从活跃事务列表中移除
    transactions_.erase(txn->getTransactionId());

    MINIDB_LOG("TransactionManager: Committed transaction " +
               std::to_string(txn->getTransactionId()));
}

void TransactionManager::abort(Transaction* txn) {
    if (!txn) return;

    std::lock_guard<std::mutex> lock(latch_);

    txn->abort();

    // 从活跃事务列表中移除
    transactions_.erase(txn->getTransactionId());

    MINIDB_LOG("TransactionManager: Aborted transaction " +
               std::to_string(txn->getTransactionId()));
}

Transaction* TransactionManager::getTransaction(transaction_id_t txn_id) {
    std::lock_guard<std::mutex> lock(latch_);

    auto it = transactions_.find(txn_id);
    if (it == transactions_.end()) {
        return nullptr;
    }
    return it->second.get();
}

size_t TransactionManager::getActiveTransactionCount() const {
    std::lock_guard<std::mutex> lock(latch_);
    return transactions_.size();
}

}  // namespace minidb
