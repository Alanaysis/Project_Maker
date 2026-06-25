#pragma once
/**
 * @file orm_basic.hpp
 * @brief ORM 框架基础
 *
 * 使用模板元编程实现基础的 ORM (Object-Relational Mapping) 框架。
 * 在编译期生成 SQL 查询语句。
 *
 * 核心特性：
 *   - 编译期 SQL 生成
 *   - 类型安全的查询
 *   - 字段映射
 *   - 查询构建器
 */

#include <string>
#include <vector>
#include <sstream>
#include <type_traits>
#include <functional>
#include <iostream>
#include <optional>
#include <tuple>

namespace tmp {

// ============================================================================
// 1. 字段类型定义
// ============================================================================

/**
 * @brief 数据库字段类型标签
 */
struct IntegerType {
    static constexpr const char* sql_type = "INTEGER";
};

struct TextType {
    static constexpr const char* sql_type = "TEXT";
};

struct RealType {
    static constexpr const char* sql_type = "REAL";
};

struct BoolType {
    static constexpr const char* sql_type = "BOOLEAN";
};

struct TimestampType {
    static constexpr const char* sql_type = "TIMESTAMP";
};

/**
 * @brief 字段描述符
 * @tparam Name 字段名（编译期字符串）
 * @tparam Type 字段类型
 * @tparam Nullable 是否可空
 */
template <typename Name, typename Type, bool Nullable = false>
struct Column {
    using name = Name;
    using type = Type;
    static constexpr bool nullable = Nullable;
};

/**
 * @brief 编译期字符串
 */
template <char... Chars>
struct StringLiteral {
    static constexpr char value[] = {Chars..., '\0'};
    static constexpr std::size_t size = sizeof...(Chars);
};

// ============================================================================
// 2. 表定义
// ============================================================================

/**
 * @brief 表定义
 * @tparam TableName 表名
 * @tparam Columns 列定义列表
 */
template <typename TableName, typename... Columns>
struct Table {
    using table_name = TableName;
    using columns = std::tuple<Columns...>;
    static constexpr std::size_t column_count = sizeof...(Columns);
};

// ============================================================================
// 3. 查询条件
// ============================================================================

/**
 * @brief 条件运算符
 */
struct Eq {
    static constexpr const char* op = "=";
};

struct Ne {
    static constexpr const char* op = "!=";
};

struct Lt {
    static constexpr const char* op = "<";
};

struct Gt {
    static constexpr const char* op = ">";
};

struct Le {
    static constexpr const char* op = "<=";
};

struct Ge {
    static constexpr const char* op = ">=";
};

struct Like {
    static constexpr const char* op = "LIKE";
};

/**
 * @brief 查询条件
 */
template <typename ColumnName, typename Op, typename ValueType>
struct Condition {
    std::string column;
    std::string value;

    std::string to_sql() const {
        return column + " " + Op::op + " " + value;
    }
};

// ============================================================================
// 4. 查询构建器
// ============================================================================

/**
 * @brief SELECT 查询构建器
 */
template <typename Table>
class SelectQuery {
    std::vector<std::string> columns_;
    std::vector<std::string> conditions_;
    std::vector<std::string> order_by_;
    std::optional<int> limit_;
    std::optional<int> offset_;

public:
    SelectQuery() = default;

    /// @brief 选择特定列
    SelectQuery& select(const std::vector<std::string>& cols) {
        columns_ = cols;
        return *this;
    }

    /// @brief 添加 WHERE 条件
    SelectQuery& where(const std::string& condition) {
        conditions_.push_back(condition);
        return *this;
    }

    /// @brief 添加 ORDER BY
    SelectQuery& order_by(const std::string& column, bool asc = true) {
        order_by_.push_back(column + (asc ? " ASC" : " DESC"));
        return *this;
    }

    /// @brief 设置 LIMIT
    SelectQuery& limit(int n) {
        limit_ = n;
        return *this;
    }

    /// @brief 设置 OFFSET
    SelectQuery& offset(int n) {
        offset_ = n;
        return *this;
    }

    /// @brief 生成 SQL
    std::string to_sql() const {
        std::ostringstream ss;

        // SELECT
        ss << "SELECT ";
        if (columns_.empty()) {
            ss << "*";
        } else {
            for (std::size_t i = 0; i < columns_.size(); ++i) {
                if (i > 0) ss << ", ";
                ss << columns_[i];
            }
        }

        // FROM
        ss << " FROM " << Table::table_name::value;

        // WHERE
        if (!conditions_.empty()) {
            ss << " WHERE ";
            for (std::size_t i = 0; i < conditions_.size(); ++i) {
                if (i > 0) ss << " AND ";
                ss << conditions_[i];
            }
        }

        // ORDER BY
        if (!order_by_.empty()) {
            ss << " ORDER BY ";
            for (std::size_t i = 0; i < order_by_.size(); ++i) {
                if (i > 0) ss << ", ";
                ss << order_by_[i];
            }
        }

        // LIMIT
        if (limit_) {
            ss << " LIMIT " << *limit_;
        }

        // OFFSET
        if (offset_) {
            ss << " OFFSET " << *offset_;
        }

        return ss.str();
    }
};

/**
 * @brief INSERT 查询构建器
 */
template <typename Table>
class InsertQuery {
    std::vector<std::pair<std::string, std::string>> values_;

public:
    InsertQuery& value(const std::string& column, const std::string& val) {
        values_.emplace_back(column, "'" + val + "'");
        return *this;
    }

    InsertQuery& value(const std::string& column, const char* val) {
        values_.emplace_back(column, "'" + std::string(val) + "'");
        return *this;
    }

    template <typename T>
    std::enable_if_t<std::is_arithmetic_v<T>, InsertQuery&>
    value(const std::string& column, const T& val) {
        values_.emplace_back(column, std::to_string(val));
        return *this;
    }

    std::string to_sql() const {
        std::ostringstream ss;
        ss << "INSERT INTO " << Table::table_name::value << " (";
        for (std::size_t i = 0; i < values_.size(); ++i) {
            if (i > 0) ss << ", ";
            ss << values_[i].first;
        }
        ss << ") VALUES (";
        for (std::size_t i = 0; i < values_.size(); ++i) {
            if (i > 0) ss << ", ";
            ss << values_[i].second;
        }
        ss << ")";
        return ss.str();
    }
};

/**
 * @brief UPDATE 查询构建器
 */
template <typename Table>
class UpdateQuery {
    std::vector<std::pair<std::string, std::string>> sets_;
    std::vector<std::string> conditions_;

public:
    UpdateQuery& set(const std::string& column, const std::string& value) {
        sets_.emplace_back(column, "'" + value + "'");
        return *this;
    }

    UpdateQuery& set(const std::string& column, const char* value) {
        sets_.emplace_back(column, "'" + std::string(value) + "'");
        return *this;
    }

    template <typename T>
    std::enable_if_t<std::is_arithmetic_v<T>, UpdateQuery&>
    set(const std::string& column, const T& value) {
        sets_.emplace_back(column, std::to_string(value));
        return *this;
    }

    UpdateQuery& where(const std::string& condition) {
        conditions_.push_back(condition);
        return *this;
    }

    std::string to_sql() const {
        std::ostringstream ss;
        ss << "UPDATE " << Table::table_name::value << " SET ";
        for (std::size_t i = 0; i < sets_.size(); ++i) {
            if (i > 0) ss << ", ";
            ss << sets_[i].first << " = " << sets_[i].second;
        }
        if (!conditions_.empty()) {
            ss << " WHERE ";
            for (std::size_t i = 0; i < conditions_.size(); ++i) {
                if (i > 0) ss << " AND ";
                ss << conditions_[i];
            }
        }
        return ss.str();
    }
};

/**
 * @brief DELETE 查询构建器
 */
template <typename Table>
class DeleteQuery {
    std::vector<std::string> conditions_;

public:
    DeleteQuery& where(const std::string& condition) {
        conditions_.push_back(condition);
        return *this;
    }

    std::string to_sql() const {
        std::ostringstream ss;
        ss << "DELETE FROM " << Table::table_name::value;
        if (!conditions_.empty()) {
            ss << " WHERE ";
            for (std::size_t i = 0; i < conditions_.size(); ++i) {
                if (i > 0) ss << " AND ";
                ss << conditions_[i];
            }
        }
        return ss.str();
    }
};

// ============================================================================
// 5. 建表语句生成
// ============================================================================

/**
 * @brief 生成 CREATE TABLE 语句
 */
template <typename Table>
class CreateTableBuilder {
public:
    static std::string to_sql() {
        std::ostringstream ss;
        ss << "CREATE TABLE IF NOT EXISTS " << Table::table_name::value << " (";

        bool first = true;
        std::apply([&](const auto&... col) {
            auto add_column = [&](const auto& c) {
                if (!first) ss << ", ";
                first = false;
                // 使用 decltype 获取类型信息
                using ColType = std::decay_t<decltype(c)>;
                ss << ColType::name::value << " " << ColType::type::sql_type;
                if (!ColType::nullable) ss << " NOT NULL";
            };
            (add_column(col), ...);
        }, typename Table::columns{});

        ss << ")";
        return ss.str();
    }
};

// ============================================================================
// 6. 便捷函数
// ============================================================================

/// @brief 创建 SELECT 查询
template <typename Table>
auto select_from() {
    return SelectQuery<Table>{};
}

/// @brief 创建 INSERT 查询
template <typename Table>
auto insert_into() {
    return InsertQuery<Table>{};
}

/// @brief 创建 UPDATE 查询
template <typename Table>
auto update_table() {
    return UpdateQuery<Table>{};
}

/// @brief 创建 DELETE 查询
template <typename Table>
auto delete_from() {
    return DeleteQuery<Table>{};
}

}  // namespace tmp
