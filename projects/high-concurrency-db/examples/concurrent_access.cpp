/**
 * MiniDB 并发访问示例
 *
 * 本示例演示 MiniDB 的并发控制功能：
 * 1. 多线程读写
 * 2. 读写锁机制
 * 3. 事务管理
 * 4. 死锁预防
 */

#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <atomic>
#include <mutex>

#include "core/common.h"
#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"
#include "storage/bplus_tree.h"
#include "concurrency/transaction.h"
#include "concurrency/lock_manager.h"

using namespace minidb;

// 全局同步
std::mutex cout_mutex;

void log(const std::string& message) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << "[" << std::this_thread::get_id() << "] " << message << std::endl;
}

// ==================== 示例 1: 并发 B+ 树操作 ====================

void concurrentBPlusTreeExample() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Example 1: Concurrent B+ Tree Operations" << std::endl;
    std::cout << "========================================" << std::endl;

    DiskManager dm("concurrent_btree.db");
    BufferPoolManager bpm(100, &dm);
    BPlusTree tree(&bpm, "concurrent_index");

    std::atomic<int> insert_count{0};
    std::atomic<int> search_count{0};
    std::atomic<int> not_found_count{0};

    // 并发插入线程
    auto insertWorker = [&](int start, int end) {
        for (int i = start; i < end; ++i) {
            ValueType value(INVALID_PAGE_ID, i);
            if (tree.insert(i, value)) {
                insert_count++;
            }
        }
    };

    // 并发搜索线程
    auto searchWorker = [&](int start, int end) {
        for (int i = start; i < end; ++i) {
            ValueType result;
            if (tree.search(i, &result)) {
                search_count++;
            } else {
                not_found_count++;
            }
        }
    };

    // 启动并发插入
    const int num_threads = 4;
    const int items_per_thread = 250;
    std::vector<std::thread> threads;

    auto start_time = std::chrono::high_resolution_clock::now();

    for (int t = 0; t < num_threads; ++t) {
        int start = t * items_per_thread;
        int end = start + items_per_thread;
        threads.emplace_back(insertWorker, start, end);
    }

    for (auto& t : threads) {
        t.join();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time);

    std::cout << "Inserted " << insert_count << " items in "
              << duration.count() << " ms" << std::endl;
    std::cout << "Tree size: " << tree.getSize() << std::endl;

    // 并发搜索
    threads.clear();
    start_time = std::chrono::high_resolution_clock::now();

    for (int t = 0; t < num_threads; ++t) {
        int start = t * items_per_thread;
        int end = start + items_per_thread;
        threads.emplace_back(searchWorker, start, end);
    }

    for (auto& t : threads) {
        t.join();
    }

    end_time = std::chrono::high_resolution_clock::now();
    duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time);

    std::cout << "Searched " << (search_count + not_found_count) << " items in "
              << duration.count() << " ms" << std::endl;
    std::cout << "Found: " << search_count << ", Not found: " << not_found_count
              << std::endl;

    // 清理
    std::remove("concurrent_btree.db");
}

// ==================== 示例 2: 读写锁并发 ====================

void readWriteLockExample() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Example 2: Read-Write Lock Concurrency" << std::endl;
    std::cout << "========================================" << std::endl;

    LockManager lock_mgr;
    TransactionManager txn_mgr;

    std::atomic<int> read_count{0};
    std::atomic<int> write_count{0};
    std::atomic<bool> running{true};

    // 读者线程
    auto reader = [&](int id) {
        while (running) {
            Transaction* txn = txn_mgr.begin();

            // 获取共享锁
            if (lock_mgr.lockShared(txn, "shared_resource")) {
                read_count++;
                log("Reader " + std::to_string(id) + " reading");

                // 模拟读操作
                std::this_thread::sleep_for(std::chrono::milliseconds(10));

                lock_mgr.unlock(txn, "shared_resource");
            }

            txn_mgr.commit(txn);
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
        }
    };

    // 写者线程
    auto writer = [&](int id) {
        while (running) {
            Transaction* txn = txn_mgr.begin();

            // 获取排他锁
            if (lock_mgr.lockExclusive(txn, "shared_resource")) {
                write_count++;
                log("Writer " + std::to_string(id) + " writing");

                // 模拟写操作
                std::this_thread::sleep_for(std::chrono::milliseconds(50));

                lock_mgr.unlock(txn, "shared_resource");
            }

            txn_mgr.commit(txn);
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }
    };

    // 启动线程
    std::vector<std::thread> threads;

    // 启动读者
    for (int i = 0; i < 3; ++i) {
        threads.emplace_back(reader, i);
    }

    // 启动写者
    for (int i = 0; i < 2; ++i) {
        threads.emplace_back(writer, i);
    }

    // 运行一段时间
    std::this_thread::sleep_for(std::chrono::seconds(2));
    running = false;

    // 等待所有线程完成
    for (auto& t : threads) {
        t.join();
    }

    std::cout << "\nResults:" << std::endl;
    std::cout << "  Total reads: " << read_count << std::endl;
    std::cout << "  Total writes: " << write_count << std::endl;
}

// ==================== 示例 3: 事务并发 ====================

void transactionConcurrencyExample() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Example 3: Transaction Concurrency" << std::endl;
    std::cout << "========================================" << std::endl;

    TransactionManager txn_mgr;
    LockManager lock_mgr;

    std::atomic<int> committed{0};
    std::atomic<int> aborted{0};

    // 模拟转账操作
    auto transfer = [&](int from, int to, int amount) {
        Transaction* txn = txn_mgr.begin();

        log("Transfer " + std::to_string(amount) + " from " +
            std::to_string(from) + " to " + std::to_string(to));

        // 获取两个账户的锁
        std::string account_from = "account_" + std::to_string(from);
        std::string account_to = "account_" + std::to_string(to);

        // 按顺序获取锁以避免死锁
        if (from < to) {
            if (!lock_mgr.lockExclusive(txn, account_from)) {
                txn_mgr.abort(txn);
                aborted++;
                return;
            }
            if (!lock_mgr.lockExclusive(txn, account_to)) {
                lock_mgr.unlock(txn, account_from);
                txn_mgr.abort(txn);
                aborted++;
                return;
            }
        } else {
            if (!lock_mgr.lockExclusive(txn, account_to)) {
                txn_mgr.abort(txn);
                aborted++;
                return;
            }
            if (!lock_mgr.lockExclusive(txn, account_from)) {
                lock_mgr.unlock(txn, account_to);
                txn_mgr.abort(txn);
                aborted++;
                return;
            }
        }

        // 执行转账
        std::this_thread::sleep_for(std::chrono::milliseconds(10));

        // 释放锁
        lock_mgr.unlock(txn, account_from);
        lock_mgr.unlock(txn, account_to);

        // 提交事务
        txn_mgr.commit(txn);
        committed++;
    };

    // 启动多个转账操作
    std::vector<std::thread> threads;
    std::vector<std::tuple<int, int, int>> transfers = {
        {1, 2, 100},
        {2, 3, 50},
        {3, 1, 75},
        {1, 3, 125},
        {2, 1, 60}
    };

    for (const auto& [from, to, amount] : transfers) {
        threads.emplace_back(transfer, from, to, amount);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << "\nResults:" << std::endl;
    std::cout << "  Committed: " << committed << std::endl;
    std::cout << "  Aborted: " << aborted << std::endl;
}

// ==================== 示例 4: 高并发压力测试 ====================

void stressTest() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Example 4: High Concurrency Stress Test" << std::endl;
    std::cout << "========================================" << std::endl;

    DiskManager dm("stress_test.db");
    BufferPoolManager bpm(1000, &dm);
    BPlusTree tree(&bpm, "stress_index");

    const int num_threads = 8;
    const int operations_per_thread = 10000;

    std::atomic<int> total_inserts{0};
    std::atomic<int> total_searches{0};
    std::atomic<int> total_deletes{0};

    auto startTime = std::chrono::high_resolution_clock::now();

    // 并发插入
    {
        std::vector<std::thread> threads;
        for (int t = 0; t < num_threads; ++t) {
            threads.emplace_back([&, t]() {
                for (int i = 0; i < operations_per_thread; ++i) {
                    int key = t * operations_per_thread + i;
                    ValueType value(INVALID_PAGE_ID, key);
                    if (tree.insert(key, value)) {
                        total_inserts++;
                    }
                }
            });
        }
        for (auto& t : threads) t.join();
    }

    auto midTime = std::chrono::high_resolution_clock::now();
    auto insertDuration = std::chrono::duration_cast<std::chrono::milliseconds>(
        midTime - startTime);

    std::cout << "Insert phase completed:" << std::endl;
    std::cout << "  Total inserts: " << total_inserts << std::endl;
    std::cout << "  Duration: " << insertDuration.count() << " ms" << std::endl;
    std::cout << "  Throughput: "
              << (total_inserts * 1000.0 / insertDuration.count())
              << " ops/sec" << std::endl;

    // 并发搜索
    {
        std::vector<std::thread> threads;
        for (int t = 0; t < num_threads; ++t) {
            threads.emplace_back([&, t]() {
                for (int i = 0; i < operations_per_thread; ++i) {
                    int key = t * operations_per_thread + i;
                    ValueType result;
                    if (tree.search(key, &result)) {
                        total_searches++;
                    }
                }
            });
        }
        for (auto& t : threads) t.join();
    }

    auto endTime = std::chrono::high_resolution_clock::now();
    auto searchDuration = std::chrono::duration_cast<std::chrono::milliseconds>(
        endTime - midTime);

    std::cout << "\nSearch phase completed:" << std::endl;
    std::cout << "  Total searches: " << total_searches << std::endl;
    std::cout << "  Duration: " << searchDuration.count() << " ms" << std::endl;
    std::cout << "  Throughput: "
              << (total_searches * 1000.0 / searchDuration.count())
              << " ops/sec" << std::endl;

    auto totalDuration = std::chrono::duration_cast<std::chrono::milliseconds>(
        endTime - startTime);
    std::cout << "\nTotal duration: " << totalDuration.count() << " ms" << std::endl;
    std::cout << "Tree size: " << tree.getSize() << std::endl;

    // 清理
    std::remove("stress_test.db");
}

// ==================== 主函数 ====================

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "MiniDB Concurrent Access Examples" << std::endl;
    std::cout << "========================================" << std::endl;

    // 示例 1: 并发 B+ 树操作
    concurrentBPlusTreeExample();

    // 示例 2: 读写锁并发
    readWriteLockExample();

    // 示例 3: 事务并发
    transactionConcurrencyExample();

    // 示例 4: 高并发压力测试
    stressTest();

    std::cout << "\n========================================" << std::endl;
    std::cout << "All examples completed!" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
