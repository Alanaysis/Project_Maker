// Table 单元测试
// 当没有 Google Test 时，使用 simple_test.cpp 中的测试

#include <iostream>
#include <cassert>
#include <cstdio>

#include "storage/disk_manager.h"
#include "storage/buffer_pool.h"
#include "storage/table.h"

using namespace minidb;

// 如果使用 Google Test，取消注释以下代码
// #include <gtest/gtest.h>
//
// TEST(TableTest, InsertRow) {
//     const char* test_file = "test_table.db";
//     {
//         DiskManager dm(test_file);
//         BufferPoolManager bpm(10, &dm);
//
//         TableDef table_def;
//         table_def.name = "test";
//         table_def.columns = {
//             {"id", TypeId::INTEGER, 0, true, false},
//             {"name", TypeId::VARCHAR, 50, false, true}
//         };
//
//         auto table = Table::create(&bpm, table_def);
//
//         Row row;
//         row.addValue(1);
//         row.addValue(std::string("test"));
//
//         Status status = table->insertRow(row);
//         ASSERT_TRUE(status.ok());
//     }
//     std::remove(test_file);
// }
