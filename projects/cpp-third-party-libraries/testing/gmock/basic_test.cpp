/**
 * @file basic_test.cpp
 * @brief Google Mock 模拟框架基础示例
 * @details 展示 Google Mock 的基本用法
 *          Google Mock 是一个模拟框架
 *          配合 Google Test 使用
 */

#include <gmock/gmock.h>
#include <gtest/gtest.h>
#include <string>
#include <vector>

/**
 * @brief 接口定义
 * @details 定义要模拟的接口
 */
class Database {
public:
    virtual ~Database() = default;
    virtual bool connect(const std::string& host, int port) = 0;
    virtual std::string query(const std::string& sql) = 0;
    virtual void disconnect() = 0;
};

/**
 * @brief Mock 类
 * @details 使用 Google Mock 创建模拟对象
 */
class MockDatabase : public Database {
public:
    MOCK_METHOD(bool, connect, (const std::string& host, int port), (override));
    MOCK_METHOD(std::string, query, (const std::string& sql), (override));
    MOCK_METHOD(void, disconnect, (), (override));
};

/**
 * @brief 使用 Mock 的类
 * @details 展示如何在测试中使用 Mock 对象
 */
class UserService {
public:
    UserService(Database* db) : db_(db) {}

    bool login(const std::string& username, const std::string& password) {
        if (!db_->connect("localhost", 3306)) {
            return false;
        }

        std::string result = db_->query("SELECT * FROM users WHERE username='" + username + "'");
        db_->disconnect();

        return !result.empty();
    }

private:
    Database* db_;
};

/**
 * @brief 基础 Mock 测试
 * @details 展示如何设置 Mock 期望
 */
TEST(UserServiceTest, LoginSuccess) {
    MockDatabase mock_db;
    UserService service(&mock_db);

    // 设置期望
    EXPECT_CALL(mock_db, connect("localhost", 3306))
        .WillOnce(testing::Return(true));

    EXPECT_CALL(mock_db, query("SELECT * FROM users WHERE username='alice'"))
        .WillOnce(testing::Return("alice|123"));

    EXPECT_CALL(mock_db, disconnect())
        .Times(1);

    // 执行测试
    bool result = service.login("alice", "password");

    // 验证结果
    EXPECT_TRUE(result);
}

TEST(UserServiceTest, LoginFailure) {
    MockDatabase mock_db;
    UserService service(&mock_db);

    // 设置期望
    EXPECT_CALL(mock_db, connect("localhost", 3306))
        .WillOnce(testing::Return(false));

    // 执行测试
    bool result = service.login("alice", "password");

    // 验证结果
    EXPECT_FALSE(result);
}

/**
 * @brief 参数匹配示例
 * @details 展示如何使用参数匹配器
 */
TEST(UserServiceTest, ParameterMatchers) {
    MockDatabase mock_db;
    UserService service(&mock_db);

    // 使用任意参数匹配器
    EXPECT_CALL(mock_db, connect(testing::_, testing::_))
        .WillOnce(testing::Return(true));

    EXPECT_CALL(mock_db, query(testing::HasSubstr("alice")))
        .WillOnce(testing::Return("alice|123"));

    EXPECT_CALL(mock_db, disconnect())
        .Times(1);

    // 执行测试
    bool result = service.login("alice", "password");
    EXPECT_TRUE(result);
}

/**
 * @brief 动作示例
 * @details 展示如何定义自定义动作
 */
TEST(UserServiceTest, CustomActions) {
    MockDatabase mock_db;
    UserService service(&mock_db);

    // 使用自定义动作
    EXPECT_CALL(mock_db, connect(testing::_, testing::_))
        .WillOnce([](const std::string& host, int port) {
            std::cout << "Connecting to " << host << ":" << port << std::endl;
            return true;
        });

    EXPECT_CALL(mock_db, query(testing::_))
        .WillOnce([](const std::string& sql) {
            std::cout << "Executing: " << sql << std::endl;
            return "result";
        });

    EXPECT_CALL(mock_db, disconnect())
        .Times(1);

    // 执行测试
    bool result = service.login("alice", "password");
    EXPECT_TRUE(result);
}

/**
 * @brief Google Mock 概念说明
 * @details 介绍 Google Mock 的核心概念
 */
TEST(MockConcepts, BasicConcepts) {
    // Mock 类
    // MOCK_METHOD(返回类型, 方法名, (参数类型), (修饰符))

    // 期望设置
    // EXPECT_CALL(mock, method(args))
    //     .Times(n)
    //     .WillOnce(action)
    //     .WillRepeatedly(action);

    // 参数匹配器
    // testing::_ - 任意参数
    // testing::Eq(value) - 等于
    // testing::Ne(value) - 不等于
    // testing::Lt(value) - 小于
    // testing::Gt(value) - 大于
    // testing::HasSubstr(str) - 包含子串

    // 动作
    // testing::Return(value) - 返回值
    // testing::Throw(exception) - 抛出异常
    // testing::Invoke(function) - 调用函数

    EXPECT_TRUE(true);
}