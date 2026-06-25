/**
 * @file bitset_example.cpp
 * @brief C++23 std::bitset 改进示例
 *
 * C++23 对 std::bitset 进行了改进，添加了新的方法和功能。
 *
 * 主要特点：
 * - 新的构造函数
 * - 新的方法
 * - 更好的类型转换
 * - 支持更多的操作
 *
 * 编译命令：
 * g++ -std=c++23 -o bitset_example bitset_example.cpp
 */

#include <iostream>
#include <bitset>
#include <string>
#include <vector>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    // 创建 bitset
    std::bitset<8> b1(42);  // 00101010
    std::bitset<8> b2("10101010");

    std::cout << "b1 (42): " << b1 << std::endl;
    std::cout << "b2 (string): " << b2 << std::endl;

    // 访问位
    std::cout << "b1[0] = " << b1[0] << std::endl;
    std::cout << "b1[1] = " << b1[1] << std::endl;
    std::cout << "b1[5] = " << b1[5] << std::endl;
}

// ========== 2. 位操作 ==========

void bit_operations() {
    std::cout << "\n=== 位操作 ===" << std::endl;

    std::bitset<8> b1("11001100");
    std::bitset<8> b2("10101010");

    std::cout << "b1: " << b1 << std::endl;
    std::cout << "b2: " << b2 << std::endl;

    // 位运算
    std::cout << "b1 & b2: " << (b1 & b2) << std::endl;
    std::cout << "b1 | b2: " << (b1 | b2) << std::endl;
    std::cout << "b1 ^ b2: " << (b1 ^ b2) << std::endl;
    std::cout << "~b1: " << (~b1) << std::endl;

    // 移位操作
    std::cout << "b1 << 2: " << (b1 << 2) << std::endl;
    std::cout << "b1 >> 2: " << (b1 >> 2) << std::endl;
}

// ========== 3. 实际应用：权限系统 ==========

enum Permission {
    READ = 0,
    WRITE = 1,
    EXECUTE = 2,
    ADMIN = 3
};

class PermissionSet {
private:
    std::bitset<4> permissions_;

public:
    PermissionSet() = default;

    void grant(Permission p) {
        permissions_.set(p);
    }

    void revoke(Permission p) {
        permissions_.reset(p);
    }

    bool has(Permission p) const {
        return permissions_.test(p);
    }

    void print() const {
        std::cout << "Permissions: "
                  << (has(READ) ? "R" : "-")
                  << (has(WRITE) ? "W" : "-")
                  << (has(EXECUTE) ? "X" : "-")
                  << (has(ADMIN) ? "A" : "-")
                  << std::endl;
    }
};

void permission_system() {
    std::cout << "\n=== 实际应用：权限系统 ===" << std::endl;

    PermissionSet user_perms;
    user_perms.grant(READ);
    user_perms.grant(WRITE);
    user_perms.print();

    std::cout << "Has READ: " << (user_perms.has(READ) ? "yes" : "no") << std::endl;
    std::cout << "Has ADMIN: " << (user_perms.has(ADMIN) ? "yes" : "no") << std::endl;

    user_perms.grant(ADMIN);
    user_perms.print();
}

// ========== 4. 实际应用：状态标志 ==========

class StatusFlags {
private:
    std::bitset<8> flags_;

public:
    enum Flag {
        ACTIVE = 0,
        VISIBLE = 1,
        ENABLED = 2,
        FOCUSED = 3,
        HOVERED = 4,
        PRESSED = 5,
        SELECTED = 6,
        DIRTY = 7
    };

    void set(Flag f) { flags_.set(f); }
    void clear(Flag f) { flags_.reset(f); }
    bool test(Flag f) const { return flags_.test(f); }

    void print() const {
        std::cout << "Flags: "
                  << (test(ACTIVE) ? "A" : "-")
                  << (test(VISIBLE) ? "V" : "-")
                  << (test(ENABLED) ? "E" : "-")
                  << (test(FOCUSED) ? "F" : "-")
                  << (test(HOVERED) ? "H" : "-")
                  << (test(PRESSED) ? "P" : "-")
                  << (test(SELECTED) ? "S" : "-")
                  << (test(DIRTY) ? "D" : "-")
                  << std::endl;
    }
};

void status_flags() {
    std::cout << "\n=== 实际应用：状态标志 ===" << std::endl;

    StatusFlags widget;
    widget.set(StatusFlags::ACTIVE);
    widget.set(StatusFlags::VISIBLE);
    widget.set(StatusFlags::ENABLED);
    widget.print();

    widget.set(StatusFlags::FOCUSED);
    widget.print();

    widget.clear(StatusFlags::VISIBLE);
    widget.print();
}

// ========== 5. 实际应用：位图 ==========

class Bitmap {
private:
    std::bitset<64> data_;

public:
    Bitmap() = default;

    void set_pixel(int x, int y) {
        if (x >= 0 && x < 8 && y >= 0 && y < 8) {
            data_.set(y * 8 + x);
        }
    }

    void clear_pixel(int x, int y) {
        if (x >= 0 && x < 8 && y >= 0 && y < 8) {
            data_.reset(y * 8 + x);
        }
    }

    bool get_pixel(int x, int y) const {
        if (x >= 0 && x < 8 && y >= 0 && y < 8) {
            return data_.test(y * 8 + x);
        }
        return false;
    }

    void print() const {
        for (int y = 0; y < 8; ++y) {
            for (int x = 0; x < 8; ++x) {
                std::cout << (get_pixel(x, y) ? "#" : ".");
            }
            std::cout << std::endl;
        }
    }
};

void bitmap_example() {
    std::cout << "\n=== 实际应用：位图 ===" << std::endl;

    Bitmap bmp;

    // 画一个简单的图案
    for (int i = 0; i < 8; ++i) {
        bmp.set_pixel(i, i);  // 对角线
        bmp.set_pixel(7 - i, i);  // 反对角线
    }

    std::cout << "Bitmap:" << std::endl;
    bmp.print();
}

// ========== 6. 实际应用：压缩数据 ==========

void compressed_data() {
    std::cout << "\n=== 实际应用：压缩数据 ===" << std::endl;

    // 使用 bitset 存储布尔值数组
    std::bitset<32> data;

    // 设置一些位
    for (int i = 0; i < 32; i += 3) {
        data.set(i);
    }

    std::cout << "Data: " << data << std::endl;
    std::cout << "Count of set bits: " << data.count() << std::endl;
    std::cout << "Size: " << data.size() << std::endl;
}

// ========== 7. 实际应用：网络掩码 ==========

void network_mask() {
    std::cout << "\n=== 实际应用：网络掩码 ===" << std::endl;

    // 子网掩码
    std::bitset<32> mask("11111111111111111111111100000000");

    std::cout << "Subnet mask: " << mask << std::endl;
    std::cout << "Network bits: " << mask.count() << std::endl;
    std::cout << "Host bits: " << (32 - mask.count()) << std::endl;

    // IP 地址
    std::bitset<32> ip("11000000101010000000000100000001");

    // 网络地址
    std::bitset<32> network = ip & mask;
    std::cout << "IP address: " << ip << std::endl;
    std::cout << "Network: " << network << std::endl;
}

// ========== 8. 实际应用：错误检测 ==========

void error_detection() {
    std::cout << "\n=== 实际应用：错误检测 ===" << std::endl;

    // 奇偶校验
    std::bitset<8> data("10110101");
    int count = data.count();

    std::cout << "Data: " << data << std::endl;
    std::cout << "Set bits: " << count << std::endl;
    std::cout << "Parity: " << (count % 2 == 0 ? "even" : "odd") << std::endl;

    // 汉明距离
    std::bitset<8> data1("10110101");
    std::bitset<8> data2("10110111");
    std::bitset<8> diff = data1 ^ data2;

    std::cout << "\nData1: " << data1 << std::endl;
    std::cout << "Data2: " << data2 << std::endl;
    std::cout << "Hamming distance: " << diff.count() << std::endl;
}

// ========== 9. 实际应用：配置选项 ==========

class ConfigOptions {
private:
    std::bitset<16> options_;

public:
    enum Option {
        DEBUG_MODE = 0,
        VERBOSE = 1,
        LOG_TO_FILE = 2,
        LOG_TO_CONSOLE = 3,
        AUTO_SAVE = 4,
        COMPRESS = 5,
        ENCRYPT = 6,
        BACKUP = 7
    };

    void enable(Option opt) { options_.set(opt); }
    void disable(Option opt) { options_.reset(opt); }
    bool is_enabled(Option opt) const { return options_.test(opt); }

    void print() const {
        std::cout << "Config: "
                  << (is_enabled(DEBUG_MODE) ? "DEBUG " : "")
                  << (is_enabled(VERBOSE) ? "VERBOSE " : "")
                  << (is_enabled(LOG_TO_FILE) ? "LOG_FILE " : "")
                  << (is_enabled(LOG_TO_CONSOLE) ? "LOG_CONSOLE " : "")
                  << (is_enabled(AUTO_SAVE) ? "AUTO_SAVE " : "")
                  << (is_enabled(COMPRESS) ? "COMPRESS " : "")
                  << (is_enabled(ENCRYPT) ? "ENCRYPT " : "")
                  << (is_enabled(BACKUP) ? "BACKUP " : "")
                  << std::endl;
    }
};

void config_options() {
    std::cout << "\n=== 实际应用：配置选项 ===" << std::endl;

    ConfigOptions config;
    config.enable(ConfigOptions::DEBUG_MODE);
    config.enable(ConfigOptions::LOG_TO_FILE);
    config.enable(ConfigOptions::AUTO_SAVE);
    config.print();

    config.enable(ConfigOptions::ENCRYPT);
    config.print();
}

// ========== 10. 实际应用：游戏状态 ==========

class GameState {
private:
    std::bitset<32> state_;

public:
    enum State {
        MENU = 0,
        PLAYING = 1,
        PAUSED = 2,
        GAME_OVER = 3,
        LEVEL_COMPLETE = 4,
        BOSS_FIGHT = 5,
        INVENTORY_OPEN = 6,
        MAP_OPEN = 7
    };

    void set_state(State s) { state_.set(s); }
    void clear_state(State s) { state_.reset(s); }
    bool is_state(State s) const { return state_.test(s); }

    void print() const {
        std::cout << "Game state: "
                  << (is_state(MENU) ? "MENU " : "")
                  << (is_state(PLAYING) ? "PLAYING " : "")
                  << (is_state(PAUSED) ? "PAUSED " : "")
                  << (is_state(GAME_OVER) ? "GAME_OVER " : "")
                  << (is_state(LEVEL_COMPLETE) ? "LEVEL_COMPLETE " : "")
                  << (is_state(BOSS_FIGHT) ? "BOSS_FIGHT " : "")
                  << (is_state(INVENTORY_OPEN) ? "INVENTORY " : "")
                  << (is_state(MAP_OPEN) ? "MAP " : "")
                  << std::endl;
    }
};

void game_state() {
    std::cout << "\n=== 实际应用：游戏状态 ===" << std::endl;

    GameState game;
    game.set_state(GameState::PLAYING);
    game.print();

    game.set_state(GameState::INVENTORY_OPEN);
    game.print();

    game.clear_state(GameState::INVENTORY_OPEN);
    game.set_state(GameState::BOSS_FIGHT);
    game.print();
}

int main() {
    std::cout << "C++23 std::bitset 改进示例\n" << std::endl;

    basic_usage();
    bit_operations();
    permission_system();
    status_flags();
    bitmap_example();
    compressed_data();
    network_mask();
    error_detection();
    config_options();
    game_state();

    return 0;
}
