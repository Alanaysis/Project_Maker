// BufferPool 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <cstdio>

#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(BufferPoolTest, FetchAndUnpin) {
//     const char* test_file = "test_buffer.db";
//     {
//         DiskManager dm(test_file);
//         BufferPoolManager bpm(10, &dm);
//
//         page_id_t page_id;
//         Page* page = bpm.newPage(&page_id);
//         ASSERT_NE(page, nullptr);
//
//         page->getData()[0] = 'X';
//         page->setDirty(true);
//         bpm.unpinPage(page_id, true);
//
//         Page* fetched = bpm.fetchPage(page_id);
//         ASSERT_NE(fetched, nullptr);
//         EXPECT_EQ(fetched->getData()[0], 'X');
//         bpm.unpinPage(page_id, false);
//     }
//     std::remove(test_file);
// }
