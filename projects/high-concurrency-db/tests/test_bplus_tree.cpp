// BPlusTree 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <cstdio>

#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"
#include "storage/bplus_tree.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(BPlusTreeTest, InsertAndSearch) {
//     const char* test_file = "test_btree.db";
//     {
//         DiskManager dm(test_file);
//         BufferPoolManager bpm(100, &dm);
//         BPlusTree tree(&bpm, "test");
//
//         for (int i = 0; i < 100; ++i) {
//             ValueType value(INVALID_PAGE_ID, i);
//             ASSERT_TRUE(tree.insert(i, value));
//         }
//
//         for (int i = 0; i < 100; ++i) {
//             ValueType result;
//             ASSERT_TRUE(tree.search(i, &result));
//             EXPECT_EQ(result.slot_num, i);
//         }
//     }
//     std::remove(test_file);
// }
