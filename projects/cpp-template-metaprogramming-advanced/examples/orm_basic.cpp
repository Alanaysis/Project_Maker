/**
 * @file orm_basic.cpp
 * @brief ORM 框架基础示例
 */

#include <iostream>
#include <string>
#include "../include/applications/orm_basic.hpp"

// 定义表名
struct UsersTableName {
    static constexpr char value[] = "users";
};

struct OrdersTableName {
    static constexpr char value[] = "orders";
};

// 定义列
struct IdColumn : tmp::Column<tmp::StringLiteral<'i','d'>, tmp::IntegerType> {};
struct NameColumn : tmp::Column<tmp::StringLiteral<'n','a','m','e'>, tmp::TextType> {};
struct AgeColumn : tmp::Column<tmp::StringLiteral<'a','g','e'>, tmp::IntegerType> {};
struct EmailColumn : tmp::Column<tmp::StringLiteral<'e','m','a','i','l'>, tmp::TextType, true> {};

struct OrderIdColumn : tmp::Column<tmp::StringLiteral<'i','d'>, tmp::IntegerType> {};
struct UserIdColumn : tmp::Column<tmp::StringLiteral<'u','s','e','r','_','i','d'>, tmp::IntegerType> {};
struct AmountColumn : tmp::Column<tmp::StringLiteral<'a','m','o','u','n','t'>, tmp::RealType> {};

// 定义表
using UsersTable = tmp::Table<UsersTableName, IdColumn, NameColumn, AgeColumn, EmailColumn>;
using OrdersTable = tmp::Table<OrdersTableName, OrderIdColumn, UserIdColumn, AmountColumn>;

int main() {
    using namespace tmp;

    std::cout << "=== ORM Framework Basics ===" << std::endl;
    std::cout << std::endl;

    // 1. CREATE TABLE
    std::cout << "--- 1. CREATE TABLE ---" << std::endl;
    std::cout << CreateTableBuilder<UsersTable>::to_sql() << std::endl;
    std::cout << CreateTableBuilder<OrdersTable>::to_sql() << std::endl;
    std::cout << std::endl;

    // 2. SELECT 查询
    std::cout << "--- 2. SELECT Query ---" << std::endl;
    auto q1 = select_from<UsersTable>();
    std::cout << q1.to_sql() << std::endl;

    auto q2 = select_from<UsersTable>()
        .select({"name", "age"})
        .where("age > 18")
        .where("active = 1")
        .order_by("name")
        .limit(10);
    std::cout << q2.to_sql() << std::endl;
    std::cout << std::endl;

    // 3. INSERT 查询
    std::cout << "--- 3. INSERT Query ---" << std::endl;
    auto insert = insert_into<UsersTable>()
        .value("name", "Alice")
        .value("age", 30)
        .value("email", "alice@example.com");
    std::cout << insert.to_sql() << std::endl;
    std::cout << std::endl;

    // 4. UPDATE 查询
    std::cout << "--- 4. UPDATE Query ---" << std::endl;
    auto update = update_table<UsersTable>()
        .set("name", "Bob")
        .set("age", 25)
        .where("id = 1");
    std::cout << update.to_sql() << std::endl;
    std::cout << std::endl;

    // 5. DELETE 查询
    std::cout << "--- 5. DELETE Query ---" << std::endl;
    auto del = delete_from<UsersTable>()
        .where("id = 1")
        .where("active = 0");
    std::cout << del.to_sql() << std::endl;
    std::cout << std::endl;

    // 6. 复杂查询
    std::cout << "--- 6. Complex Queries ---" << std::endl;
    auto complex = select_from<OrdersTable>()
        .select({"user_id", "SUM(amount)"})
        .where("amount > 100")
        .order_by("amount", false)
        .limit(5)
        .offset(10);
    std::cout << complex.to_sql() << std::endl;

    return 0;
}
