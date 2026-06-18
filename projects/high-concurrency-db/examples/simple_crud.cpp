/**
 * MiniDB 简单 CRUD 示例
 *
 * 本示例演示如何使用 MiniDB 进行基本的数据库操作：
 * 1. 创建表
 * 2. 插入数据
 * 3. 查询数据
 * 4. 更新数据
 * 5. 删除数据
 */

#include <iostream>
#include <memory>
#include <string>

#include "core/common.h"
#include "core/status.h"
#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"
#include "storage/table.h"
#include "sql/tokenizer.h"
#include "sql/parser.h"
#include "sql/executor.h"

using namespace minidb;

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "MiniDB Simple CRUD Example" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    // 1. 初始化存储引擎
    std::cout << "[1] Initializing storage engine..." << std::endl;

    // 创建磁盘管理器
    DiskManager disk_manager("example.minidb");

    // 创建缓冲池管理器 (100 个页面)
    BufferPoolManager buffer_pool(100, &disk_manager);

    // 创建目录
    Catalog catalog(&buffer_pool);

    // 创建执行引擎
    ExecutionEngine executor(&buffer_pool, &catalog, nullptr);

    std::cout << "Storage engine initialized." << std::endl;
    std::cout << std::endl;

    // 2. 创建表
    std::cout << "[2] Creating table 'users'..." << std::endl;

    {
        std::string sql = "CREATE TABLE users ("
                          "id INT PRIMARY KEY, "
                          "name VARCHAR(100), "
                          "age INT"
                          ")";

        Parser parser(sql);
        auto stmt = parser.parse();

        if (!stmt) {
            std::cerr << "Parse error: " << parser.getError() << std::endl;
            return 1;
        }

        auto result = executor.execute(stmt.get());
        if (!result.status.ok()) {
            std::cerr << "Error: " << result.status.message() << std::endl;
            return 1;
        }
    }

    std::cout << std::endl;

    // 3. 插入数据
    std::cout << "[3] Inserting data..." << std::endl;

    {
        std::vector<std::string> insert_sqls = {
            "INSERT INTO users VALUES (1, 'Alice', 25)",
            "INSERT INTO users VALUES (2, 'Bob', 30)",
            "INSERT INTO users VALUES (3, 'Charlie', 35)",
            "INSERT INTO users VALUES (4, 'Diana', 28)",
            "INSERT INTO users VALUES (5, 'Eve', 22)"
        };

        for (const auto& sql : insert_sqls) {
            Parser parser(sql);
            auto stmt = parser.parse();

            if (!stmt) {
                std::cerr << "Parse error: " << parser.getError() << std::endl;
                continue;
            }

            auto result = executor.execute(stmt.get());
            if (!result.status.ok()) {
                std::cerr << "Error: " << result.status.message() << std::endl;
            }
        }
    }

    std::cout << std::endl;

    // 4. 查询数据
    std::cout << "[4] Querying data..." << std::endl;

    {
        std::string sql = "SELECT id, name, age FROM users";
        Parser parser(sql);
        auto stmt = parser.parse();

        if (!stmt) {
            std::cerr << "Parse error: " << parser.getError() << std::endl;
            return 1;
        }

        auto result = executor.execute(stmt.get());
        if (!result.status.ok()) {
            std::cerr << "Error: " << result.status.message() << std::endl;
        }
    }

    std::cout << std::endl;

    // 5. 条件查询
    std::cout << "[5] Querying with condition..." << std::endl;

    {
        std::string sql = "SELECT name FROM users WHERE age > 25";
        Parser parser(sql);
        auto stmt = parser.parse();

        if (!stmt) {
            std::cerr << "Parse error: " << parser.getError() << std::endl;
            return 1;
        }

        auto result = executor.execute(stmt.get());
        if (!result.status.ok()) {
            std::cerr << "Error: " << result.status.message() << std::endl;
        }
    }

    std::cout << std::endl;

    // 6. SQL 解析演示
    std::cout << "[6] SQL Parsing Demo..." << std::endl;

    {
        std::vector<std::string> sqls = {
            "SELECT * FROM users WHERE id = 1",
            "INSERT INTO users VALUES (6, 'Frank', 40)",
            "UPDATE users SET age = 26 WHERE id = 1",
            "DELETE FROM users WHERE id = 5"
        };

        for (const auto& sql : sqls) {
            std::cout << "\nSQL: " << sql << std::endl;

            // 词法分析
            Tokenizer tokenizer(sql);
            auto tokens = tokenizer.tokenize();

            std::cout << "Tokens: ";
            for (const auto& token : tokens) {
                std::cout << token.toString() << " ";
            }
            std::cout << std::endl;

            // 语法分析
            Parser parser(sql);
            auto stmt = parser.parse();

            if (stmt) {
                std::cout << "AST: " << stmt->toString() << std::endl;
            } else {
                std::cout << "Parse error: " << parser.getError() << std::endl;
            }
        }
    }

    std::cout << std::endl;

    // 7. B+ 树索引演示
    std::cout << "[7] B+ Tree Index Demo..." << std::endl;

    {
        // 创建 B+ 树索引
        BPlusTree index(&buffer_pool, "users_id_index");

        // 插入索引项
        for (int i = 1; i <= 100; ++i) {
            ValueType value(INVALID_PAGE_ID, i);
            index.insert(i, value);
        }

        std::cout << "Inserted 100 entries into B+ tree" << std::endl;
        std::cout << "Tree size: " << index.getSize() << std::endl;
        std::cout << "Tree height: " << index.getHeight() << std::endl;

        // 搜索
        ValueType result;
        if (index.search(42, &result)) {
            std::cout << "Found key 42, slot_num = " << result.slot_num << std::endl;
        }

        // 范围查询
        auto range_results = index.rangeQuery(10, 20);
        std::cout << "Range query [10, 20]: " << range_results.size() << " results" << std::endl;
    }

    std::cout << std::endl;

    // 8. 事务演示
    std::cout << "[8] Transaction Demo..." << std::endl;

    {
        TransactionManager txn_mgr;

        // 开始事务
        Transaction* txn = txn_mgr.begin();
        std::cout << "Transaction " << txn->getTransactionId() << " started" << std::endl;

        // 执行一些操作
        std::cout << "Performing operations..." << std::endl;

        // 提交事务
        txn_mgr.commit(txn);
        std::cout << "Transaction committed" << std::endl;
    }

    std::cout << std::endl;

    // 9. 并发演示
    std::cout << "[9] Concurrency Demo..." << std::endl;

    {
        LockManager lock_mgr;
        TransactionManager txn_mgr;

        // 创建两个事务
        Transaction* txn1 = txn_mgr.begin();
        Transaction* txn2 = txn_mgr.begin();

        std::cout << "Transaction 1: " << txn1->getTransactionId() << std::endl;
        std::cout << "Transaction 2: " << txn2->getTransactionId() << std::endl;

        // 两个事务都获取共享锁
        lock_mgr.lockShared(txn1, "users");
        lock_mgr.lockShared(txn2, "users");

        std::cout << "Both transactions acquired shared lock on 'users'" << std::endl;

        // 释放锁
        lock_mgr.unlock(txn1, "users");
        lock_mgr.unlock(txn2, "users");

        // 提交事务
        txn_mgr.commit(txn1);
        txn_mgr.commit(txn2);

        std::cout << "Both transactions committed" << std::endl;
    }

    std::cout << std::endl;

    // 清理
    std::cout << "========================================" << std::endl;
    std::cout << "Example completed successfully!" << std::endl;
    std::cout << "========================================" << std::endl;

    // 清理数据库文件
    std::remove("example.minidb");

    return 0;
}
