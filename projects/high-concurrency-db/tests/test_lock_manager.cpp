// LockManager 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>

#include "concurrency/lock_manager.h"
#include "concurrency/transaction.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(LockManagerTest, SharedLock) {
//     LockManager lock_mgr;
//     TransactionManager txn_mgr;
//
//     Transaction* txn1 = txn_mgr.begin();
//     Transaction* txn2 = txn_mgr.begin();
//
//     ASSERT_TRUE(lock_mgr.lockShared(txn1, "table1"));
//     ASSERT_TRUE(lock_mgr.lockShared(txn2, "table1"));
//
//     lock_mgr.unlock(txn1, "table1");
//     lock_mgr.unlock(txn2, "table1");
//
//     txn_mgr.commit(txn1);
//     txn_mgr.commit(txn2);
// }
