/**
 * @file test_room.cpp
 * @brief WebSocket 房间系统测试
 *
 * 测试房间管理功能。
 */

#include "websocket/room.h"
#include <iostream>
#include <cassert>

using namespace ws;

/**
 * @brief 测试工具
 */
void assert_true(bool condition, const std::string& msg) {
    if (!condition) {
        std::cerr << "FAIL: " << msg << std::endl;
        exit(1);
    }
}

void assert_eq(size_t expected, size_t actual, const std::string& msg) {
    if (expected != actual) {
        std::cerr << "FAIL: " << msg << " (expected " << expected
                  << ", got " << actual << ")" << std::endl;
        exit(1);
    }
}

/**
 * @brief 创建测试用的连接指针（模拟）
 *
 * 注意：这些测试使用模拟的连接，实际的连接需要网络。
 */
class MockConnection : public std::enable_shared_from_this<MockConnection> {
public:
    uint64_t id() const { return id_; }
    void set_id(uint64_t id) { id_ = id; }

    void send_text(const std::string& text) {
        messages_.push_back(text);
    }

    const std::vector<std::string>& messages() const { return messages_; }

private:
    uint64_t id_ = 0;
    std::vector<std::string> messages_;
};

/**
 * @brief 测试房间创建
 */
void test_room_creation() {
    std::cout << "Testing room creation..." << std::endl;

    Room room("test_room");

    assert_true(room.name() == "test_room", "Room name should match");
    assert_eq(0, room.member_count(), "New room should have 0 members");
    assert_true(room.empty(), "New room should be empty");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试房间属性
 */
void test_room_properties() {
    std::cout << "Testing room properties..." << std::endl;

    Room room("test_room");

    // 设置属性
    room.set_property("max_players", "4");
    room.set_property("game_mode", "deathmatch");

    // 获取属性
    auto max_players = room.get_property("max_players");
    assert_true(max_players.has_value(), "Should have max_players property");
    assert_true(*max_players == "4", "max_players should be '4'");

    auto game_mode = room.get_property("game_mode");
    assert_true(game_mode.has_value(), "Should have game_mode property");
    assert_true(*game_mode == "deathmatch", "game_mode should be 'deathmatch'");

    // 获取不存在的属性
    auto missing = room.get_property("missing");
    assert_true(!missing.has_value(), "Missing property should return nullopt");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试房间管理器
 */
void test_room_manager() {
    std::cout << "Testing room manager..." << std::endl;

    RoomManager manager;

    // 创建房间
    auto room1 = manager.create_room("room1");
    assert_true(room1 != nullptr, "Room1 should be created");
    assert_true(manager.has_room("room1"), "Room1 should exist");

    auto room2 = manager.create_room("room2");
    assert_true(room2 != nullptr, "Room2 should be created");

    // 重复创建应该返回同一个房间
    auto room1_again = manager.create_room("room1");
    assert_true(room1 == room1_again, "Duplicate creation should return same room");

    // 房间数量
    assert_eq(2, manager.room_count(), "Should have 2 rooms");

    // 房间列表
    auto names = manager.room_names();
    assert_eq(2, names.size(), "Should have 2 room names");

    // 获取房间
    auto fetched = manager.get_room("room1");
    assert_true(fetched != nullptr, "Should be able to fetch room1");

    auto missing = manager.get_room("nonexistent");
    assert_true(missing == nullptr, "Nonexistent room should return nullptr");

    // 销毁房间
    manager.destroy_room("room1");
    assert_true(!manager.has_room("room1"), "Room1 should be destroyed");
    assert_eq(1, manager.room_count(), "Should have 1 room");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试自动创建房间
 */
void test_auto_create_room() {
    std::cout << "Testing auto-create room..." << std::endl;

    RoomManager manager;

    // join_room 应该自动创建房间
    // 注意：这里无法创建真实的 Connection，只测试 RoomManager 的逻辑

    // 直接创建房间测试
    auto room = manager.create_room("auto_room");
    assert_true(room != nullptr, "Room should be created");
    assert_true(manager.has_room("auto_room"), "Auto-created room should exist");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 测试房间销毁时清理
 */
void test_room_cleanup() {
    std::cout << "Testing room cleanup..." << std::endl;

    RoomManager manager;

    // 创建多个房间
    manager.create_room("room_a");
    manager.create_room("room_b");
    manager.create_room("room_c");

    assert_eq(3, manager.room_count(), "Should have 3 rooms");

    // 销毁一个房间
    manager.destroy_room("room_b");
    assert_eq(2, manager.room_count(), "Should have 2 rooms");
    assert_true(!manager.has_room("room_b"), "Room B should be destroyed");

    // 验证其他房间仍然存在
    assert_true(manager.has_room("room_a"), "Room A should still exist");
    assert_true(manager.has_room("room_c"), "Room C should still exist");

    std::cout << "  PASSED" << std::endl;
}

/**
 * @brief 主函数
 */
int main() {
    std::cout << "=== WebSocket Room Tests ===" << std::endl;

    test_room_creation();
    test_room_properties();
    test_room_manager();
    test_auto_create_room();
    test_room_cleanup();

    std::cout << "\nAll room tests passed!" << std::endl;
    return 0;
}
