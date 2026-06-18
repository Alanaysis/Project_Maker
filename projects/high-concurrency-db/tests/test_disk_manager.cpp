// DiskManager 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <cstdio>

#include "storage/disk_manager.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(DiskManagerTest, ReadWrite) {
//     const char* test_file = "test_disk.db";
//     {
//         DiskManager dm(test_file);
//         char data[PAGE_SIZE] = {0};
//         data[0] = 'A';
//         dm.writePage(0, data);
//
//         char read_data[PAGE_SIZE] = {0};
//         dm.readPage(0, read_data);
//         EXPECT_EQ(read_data[0], 'A');
//     }
//     std::remove(test_file);
// }
