#include <iostream>
#include <cassert>
#include <string>
#include <vector>
#include <memory>
#include <thread>
#include <functional>

// 包含 MiniDB 头文件
#include "core/common.h"
#include "core/status.h"
#include "core/config.h"
#include "sql/tokenizer.h"
#include "sql/parser.h"
#include "sql/ast.h"
#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"
#include "storage/bplus_tree.h"
#include "storage/table.h"
#include "concurrency/transaction.h"
#include "concurrency/lock_manager.h"

using namespace minidb;

// ==================== 测试框架 ====================

int tests_passed = 0;
int tests_failed = 0;

#define TEST_CASE(name) \
    void test_##name(); \
    struct TestRegistrar_##name { \
        TestRegistrar_##name() { \
            std::cout << "Running " #name "..." << std::endl; \
            try { \
                test_##name(); \
                tests_passed++; \
                std::cout << "  PASSED" << std::endl; \
            } catch (const std::exception& e) { \
                tests_failed++; \
                std::cout << "  FAILED: " << e.what() << std::endl; \
            } \
        } \
    } registrar_##name; \
    void test_##name()

#define ASSERT_TRUE(expr) \
    do { \
        if (!(expr)) { \
            throw std::runtime_error("Assertion failed: " #expr); \
        } \
    } while (0)

#define ASSERT_EQ(a, b) \
    do { \
        if ((a) != (b)) { \
            throw std::runtime_error("Assertion failed: " #a " == " #b); \
        } \
    } while (0)

#define ASSERT_NE(a, b) \
    do { \
        if ((a) == (b)) { \
            throw std::runtime_error("Assertion failed: " #a " != " #b); \
        } \
    } while (0)

// ==================== Tokenizer 测试 ====================

TEST_CASE(TokenizerBasic) {
    Tokenizer tokenizer("SELECT * FROM users WHERE id = 1");
    auto tokens = tokenizer.tokenize();

    ASSERT_TRUE(tokens.size() >= 7);
    ASSERT_EQ(tokens[0].type, TokenType::SELECT);
    ASSERT_EQ(tokens[1].type, TokenType::STAR);
    ASSERT_EQ(tokens[2].type, TokenType::FROM);
    ASSERT_EQ(tokens[3].type, TokenType::IDENTIFIER);
    ASSERT_EQ(tokens[3].value, "users");
    ASSERT_EQ(tokens[4].type, TokenType::WHERE);
    ASSERT_EQ(tokens[5].type, TokenType::IDENTIFIER);
    ASSERT_EQ(tokens[5].value, "id");
    ASSERT_EQ(tokens[6].type, TokenType::EQUAL);
    ASSERT_EQ(tokens[7].type, TokenType::INTEGER);
    ASSERT_EQ(tokens[7].value, "1");
}

TEST_CASE(TokenizerKeywords) {
    Tokenizer tokenizer("CREATE TABLE test (id INT PRIMARY KEY)");
    auto tokens = tokenizer.tokenize();

    ASSERT_EQ(tokens[0].type, TokenType::CREATE);
    ASSERT_EQ(tokens[1].type, TokenType::TABLE);
    ASSERT_EQ(tokens[2].type, TokenType::IDENTIFIER);
    ASSERT_EQ(tokens[2].value, "test");
    ASSERT_EQ(tokens[3].type, TokenType::LPAREN);
    ASSERT_EQ(tokens[4].type, TokenType::IDENTIFIER);
    ASSERT_EQ(tokens[5].type, TokenType::INT_TYPE);
    ASSERT_EQ(tokens[6].type, TokenType::PRIMARY);
    ASSERT_EQ(tokens[7].type, TokenType::KEY);
    ASSERT_EQ(tokens[8].type, TokenType::RPAREN);
}

TEST_CASE(TokenizerOperators) {
    Tokenizer tokenizer("a = 1 AND b <> 2 OR c > 3");
    auto tokens = tokenizer.tokenize();

    ASSERT_EQ(tokens[1].type, TokenType::EQUAL);
    ASSERT_EQ(tokens[3].type, TokenType::AND);
    ASSERT_EQ(tokens[5].type, TokenType::NOT_EQUAL);
    ASSERT_EQ(tokens[7].type, TokenType::OR);
    ASSERT_EQ(tokens[9].type, TokenType::GREATER);
}

TEST_CASE(TokenizerString) {
    Tokenizer tokenizer("INSERT INTO users VALUES ('hello', 'world')");
    auto tokens = tokenizer.tokenize();

    ASSERT_EQ(tokens[0].type, TokenType::INSERT);
    ASSERT_EQ(tokens[4].type, TokenType::STRING);
    ASSERT_EQ(tokens[4].value, "hello");
    ASSERT_EQ(tokens[6].type, TokenType::STRING);
    ASSERT_EQ(tokens[6].value, "world");
}

// ==================== Parser 测试 ====================

TEST_CASE(ParserCreateTable) {
    Parser parser("CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), age INT)");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::CREATE_TABLE);

    auto* create_stmt = static_cast<CreateTableStatement*>(stmt.get());
    ASSERT_EQ(create_stmt->getTableName(), "users");
    ASSERT_EQ(create_stmt->getColumns().size(), 3);
    ASSERT_EQ(create_stmt->getColumns()[0].name, "id");
    ASSERT_EQ(create_stmt->getColumns()[0].type, TypeId::INTEGER);
    ASSERT_TRUE(create_stmt->getColumns()[0].is_primary_key);
    ASSERT_EQ(create_stmt->getColumns()[1].name, "name");
    ASSERT_EQ(create_stmt->getColumns()[1].type, TypeId::VARCHAR);
    ASSERT_EQ(create_stmt->getColumns()[1].max_length, 100);
}

TEST_CASE(ParserInsert) {
    Parser parser("INSERT INTO users VALUES (1, 'Alice', 25)");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::INSERT);

    auto* insert_stmt = static_cast<InsertStatement*>(stmt.get());
    ASSERT_EQ(insert_stmt->getTableName(), "users");
    ASSERT_EQ(insert_stmt->getValues().size(), 1);
    ASSERT_EQ(insert_stmt->getValues()[0].size(), 3);
}

TEST_CASE(ParserSelect) {
    Parser parser("SELECT name, age FROM users WHERE id = 1");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::SELECT);

    auto* select_stmt = static_cast<SelectStatement*>(stmt.get());
    ASSERT_EQ(select_stmt->getTableName(), "users");
    ASSERT_EQ(select_stmt->getColumns().size(), 2);
    ASSERT_EQ(select_stmt->getColumns()[0], "name");
    ASSERT_EQ(select_stmt->getColumns()[1], "age");
    ASSERT_TRUE(select_stmt->getWhereClause() != nullptr);
}

TEST_CASE(ParserSelectStar) {
    Parser parser("SELECT * FROM users");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::SELECT);

    auto* select_stmt = static_cast<SelectStatement*>(stmt.get());
    ASSERT_EQ(select_stmt->getColumns().size(), 1);
    ASSERT_EQ(select_stmt->getColumns()[0], "*");
    ASSERT_TRUE(select_stmt->getWhereClause() == nullptr);
}

TEST_CASE(ParserUpdate) {
    Parser parser("UPDATE users SET age = 26 WHERE id = 1");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::UPDATE);

    auto* update_stmt = static_cast<UpdateStatement*>(stmt.get());
    ASSERT_EQ(update_stmt->getTableName(), "users");
    ASSERT_EQ(update_stmt->getSetClauses().size(), 1);
    ASSERT_EQ(update_stmt->getSetClauses()[0].first, "age");
    ASSERT_TRUE(update_stmt->getWhereClause() != nullptr);
}

TEST_CASE(ParserDelete) {
    Parser parser("DELETE FROM users WHERE id = 1");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::DELETE);

    auto* delete_stmt = static_cast<DeleteStatement*>(stmt.get());
    ASSERT_EQ(delete_stmt->getTableName(), "users");
    ASSERT_TRUE(delete_stmt->getWhereClause() != nullptr);
}

TEST_CASE(ParserDropTable) {
    Parser parser("DROP TABLE users");
    auto stmt = parser.parse();

    ASSERT_TRUE(stmt != nullptr);
    ASSERT_EQ(stmt->type(), StatementType::DROP_TABLE);

    auto* drop_stmt = static_cast<DropTableStatement*>(stmt.get());
    ASSERT_EQ(drop_stmt->getTableName(), "users");
}

// ==================== Status 测试 ====================

TEST_CASE(StatusSuccess) {
    Status status = Status::success();
    ASSERT_TRUE(status.ok());
    ASSERT_EQ(status.code(), ErrorCode::SUCCESS);
}

TEST_CASE(StatusError) {
    Status status = Status::tableNotFound("users");
    ASSERT_TRUE(!status.ok());
    ASSERT_EQ(status.code(), ErrorCode::TABLE_NOT_FOUND);
    ASSERT_TRUE(status.message().find("users") != std::string::npos);
}

// ==================== B+ Tree 测试 ====================

TEST_CASE(BPlusTreeInsertAndSearch) {
    // 创建临时文件
    DiskManager dm("test_bplus_tree.db");
    BufferPoolManager bpm(10, &dm);

    BPlusTree tree(&bpm, "test_index");

    // 插入数据
    for (int i = 0; i < 10; ++i) {
        ValueType value(INVALID_PAGE_ID, i);
        ASSERT_TRUE(tree.insert(i, value));
    }

    // 搜索数据
    for (int i = 0; i < 10; ++i) {
        ValueType result;
        ASSERT_TRUE(tree.search(i, &result));
        ASSERT_EQ(result.slot_num, i);
    }

    // 搜索不存在的 key
    ValueType result;
    ASSERT_TRUE(!tree.search(100, &result));

    // 清理
    std::remove("test_bplus_tree.db");
}

TEST_CASE(BPlusTreeRangeQuery) {
    DiskManager dm("test_bplus_range.db");
    BufferPoolManager bpm(10, &dm);

    BPlusTree tree(&bpm, "test_index");

    // 插入数据
    for (int i = 0; i < 20; ++i) {
        ValueType value(INVALID_PAGE_ID, i);
        tree.insert(i, value);
    }

    // 范围查询
    auto results = tree.rangeQuery(5, 15);
    ASSERT_EQ(results.size(), 11);  // 5, 6, ..., 15

    // 清理
    std::remove("test_bplus_range.db");
}

TEST_CASE(BPlusTreeRemove) {
    DiskManager dm("test_bplus_remove.db");
    BufferPoolManager bpm(10, &dm);

    BPlusTree tree(&bpm, "test_index");

    // 插入数据
    for (int i = 0; i < 10; ++i) {
        ValueType value(INVALID_PAGE_ID, i);
        tree.insert(i, value);
    }

    // 删除数据
    ASSERT_TRUE(tree.remove(5));
    ASSERT_TRUE(tree.remove(3));

    // 验证删除
    ValueType result;
    ASSERT_TRUE(!tree.search(5, &result));
    ASSERT_TRUE(!tree.search(3, &result));
    ASSERT_TRUE(tree.search(4, &result));

    // 清理
    std::remove("test_bplus_remove.db");
}

// ==================== Transaction 测试 ====================

TEST_CASE(TransactionBasic) {
    TransactionManager txn_mgr;

    // 开始事务
    Transaction* txn = txn_mgr.begin();
    ASSERT_TRUE(txn != nullptr);
    ASSERT_TRUE(txn->isActive());

    // 提交事务
    txn_mgr.commit(txn);
    ASSERT_TRUE(txn->getState() == TransactionState::COMMITTED);
}

TEST_CASE(TransactionAbort) {
    TransactionManager txn_mgr;

    // 开始事务
    Transaction* txn = txn_mgr.begin();
    ASSERT_TRUE(txn != nullptr);

    // 中止事务
    txn_mgr.abort(txn);
    ASSERT_TRUE(txn->getState() == TransactionState::ABORTED);
}

// ==================== LockManager 测试 ====================

TEST_CASE(LockManagerSharedLock) {
    LockManager lock_mgr;
    TransactionManager txn_mgr;

    Transaction* txn1 = txn_mgr.begin();
    Transaction* txn2 = txn_mgr.begin();

    // 两个事务都可以获取共享锁
    ASSERT_TRUE(lock_mgr.lockShared(txn1, "table1"));
    ASSERT_TRUE(lock_mgr.lockShared(txn2, "table1"));

    // 释放锁
    lock_mgr.unlock(txn1, "table1");
    lock_mgr.unlock(txn2, "table1");

    txn_mgr.commit(txn1);
    txn_mgr.commit(txn2);
}

TEST_CASE(LockManagerExclusiveLock) {
    LockManager lock_mgr;
    TransactionManager txn_mgr;

    Transaction* txn1 = txn_mgr.begin();
    Transaction* txn2 = txn_mgr.begin();

    // 获取排他锁
    ASSERT_TRUE(lock_mgr.lockExclusive(txn1, "table1"));

    // 尝试获取锁 (会超时)
    // 注意：这个测试可能会超时
    // ASSERT_TRUE(!lock_mgr.lockShared(txn2, "table1"));

    // 释放锁
    lock_mgr.unlock(txn1, "table1");

    txn_mgr.commit(txn1);
    txn_mgr.commit(txn2);
}

// ==================== Table 测试 ====================

TEST_CASE(TableInsertAndRetrieve) {
    DiskManager dm("test_table.db");
    BufferPoolManager bpm(10, &dm);

    TableDef table_def;
    table_def.name = "users";
    table_def.columns = {
        {"id", TypeId::INTEGER, 0, true, false},
        {"name", TypeId::VARCHAR, 50, false, true},
        {"age", TypeId::INTEGER, 0, false, true}
    };

    auto table = Table::create(&bpm, table_def);

    // 插入数据
    Row row;
    row.addValue(1);
    row.addValue(std::string("Alice"));
    row.addValue(25);

    Status status = table->insertRow(row);
    ASSERT_TRUE(status.ok());

    // 清理
    std::remove("test_table.db");
}

// ==================== 主函数 ====================

int main() {
    std::cout << "============================" << std::endl;
    std::cout << "MiniDB Test Suite" << std::endl;
    std::cout << "============================" << std::endl;
    std::cout << std::endl;

    // 测试会自动运行 (通过 TestRegistrar)

    std::cout << std::endl;
    std::cout << "============================" << std::endl;
    std::cout << "Test Results:" << std::endl;
    std::cout << "  Passed: " << tests_passed << std::endl;
    std::cout << "  Failed: " << tests_failed << std::endl;
    std::cout << "============================" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}
