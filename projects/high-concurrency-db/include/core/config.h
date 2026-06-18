#pragma once

#include "core/common.h"
#include <cstddef>
#include <cstdint>
#include <iostream>

namespace minidb {

// 注意: PAGE_SIZE 和 INVALID_PAGE_ID 已在 common.h 中定义

// ==================== 页面配置 ====================

// 默认缓冲池大小 (页面数量)
constexpr size_t DEFAULT_BUFFER_POOL_SIZE = 100;

// ==================== B+ 树配置 ====================

// B+ 树的阶 (每个节点的最大子节点数)
// 叶子节点最多存储 ORDER - 1 个 key
// 内部节点最多存储 ORDER - 1 个 key 和 ORDER 个 child
constexpr int BPLUS_TREE_ORDER = 50;

// 叶子节点最多存储的 key 数量
constexpr int LEAF_MAX_SIZE = BPLUS_TREE_ORDER - 1;

// 内部节点最多存储的 key 数量
constexpr int INTERNAL_MAX_SIZE = BPLUS_TREE_ORDER - 1;

// ==================== 表配置 ====================

// 表名最大长度
constexpr size_t MAX_TABLE_NAME_LENGTH = 64;

// 列名最大长度
constexpr size_t MAX_COLUMN_NAME_LENGTH = 64;

// VARCHAR 最大长度
constexpr size_t MAX_VARCHAR_LENGTH = 65535;

// 单表最大列数
constexpr size_t MAX_COLUMNS = 128;

// ==================== 缓冲池配置 ====================

// 替换策略
enum class ReplacementPolicy {
    LRU,
    LRU_K,
    CLOCK
};

// 默认替换策略
constexpr ReplacementPolicy DEFAULT_REPLACEMENT_POLICY = ReplacementPolicy::LRU;

// ==================== 事务配置 ====================

// 事务隔离级别
enum class IsolationLevel {
    READ_UNCOMMITTED,
    READ_COMMITTED,
    REPEATABLE_READ,
    SERIALIZABLE
};

// 默认隔离级别
constexpr IsolationLevel DEFAULT_ISOLATION_LEVEL = IsolationLevel::READ_COMMITTED;

// 锁超时时间 (毫秒)
constexpr int64_t LOCK_TIMEOUT_MS = 1000;

// ==================== SQL 配置 ====================

// SQL 最大长度
constexpr size_t MAX_SQL_LENGTH = 65536;

// 最大列数 in SELECT
constexpr size_t MAX_SELECT_COLUMNS = 128;

// ==================== 并发配置 ====================

// 最大并发事务数
constexpr size_t MAX_CONCURRENT_TRANSACTIONS = 1024;

// 死锁检测间隔 (毫秒)
constexpr int64_t DEADLOCK_DETECTION_INTERVAL_MS = 100;

// ==================== 存储配置 ====================

// 数据库文件扩展名
constexpr const char* DB_FILE_EXTENSION = ".minidb";

// 临时文件扩展名
constexpr const char* TEMP_FILE_EXTENSION = ".tmp";

// 日志文件扩展名
constexpr const char* LOG_FILE_EXTENSION = ".log";

// ==================== 调试配置 ====================

// 是否启用调试日志
#ifdef DEBUG
constexpr bool ENABLE_DEBUG_LOG = true;
#else
constexpr bool ENABLE_DEBUG_LOG = false;
#endif

// 调试日志宏
#define MINIDB_LOG(msg) \
    if constexpr (ENABLE_DEBUG_LOG) { \
        std::cout << "[DEBUG] " << msg << std::endl; \
    }

#define MINIDB_ERROR(msg) \
    std::cerr << "[ERROR] " << msg << std::endl;

}  // namespace minidb
