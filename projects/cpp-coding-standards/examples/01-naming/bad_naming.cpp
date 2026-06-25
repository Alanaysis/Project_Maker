/**
 * @file bad_naming.cpp
 * @brief 糟糕命名规范示例
 *
 * 本文件展示不符合 C++ 命名规范的糟糕代码示例。
 * 这些代码展示了常见的命名错误和反模式。
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */

#include <iostream>
#include <string>
#include <vector>

// ============================================================================
// 糟糕的常量命名 - 使用模糊的名称
// ============================================================================

/// 糟糕：使用缩写和模糊名称
const int MAX = 100;           // 什么的最大值？
const int N = 3;               // N 是什么？
const double PI = 3.14;        // 应该使用 k 前缀
const int cnt = 10;            // 应该使用描述性名称

// ============================================================================
// 糟糕的变量命名 - 使用模糊的名称
// ============================================================================

/**
 * @brief 糟糕的变量命名示例
 */
void badVariableNaming() {
    // 糟糕：使用单字母变量名
    int a = 25;
    int b = 30;
    int c = a + b;

    // 糟糕：使用无意义的名称
    int temp = 100;
    int data = 200;
    int val = 300;

    // 糟糕：使用缩写
    int usr_id = 1;
    std::string usr_nm = "Alice";
    int retry_cnt = 3;

    // 糟糕：使用匈牙利命名法（在现代 C++ 中不推荐）
    int iAge = 25;
    std::string strName = "Bob";
    bool bIsActive = true;

    // 糟糕：使用下划线开头（可能与系统保留名称冲突）
    int _count = 10;
    std::string _name = "Charlie";

    // 糟糕：使用全大写（应该保留给宏）
    int COUNT = 10;
    std::string NAME = "David";
}

// ============================================================================
// 糟糕的函数命名 - 使用模糊的名称
// ============================================================================

/// 糟糕：函数名不清晰
void process() {
    std::cout << "Processing..." << std::endl;
}

/// 糟糕：函数名不清晰
void handle() {
    std::cout << "Handling..." << std::endl;
}

/// 糟糕：函数名不清晰
void doSomething() {
    std::cout << "Doing something..." << std::endl;
}

/// 糟糕：使用缩写
void calc() {
    std::cout << "Calculating..." << std::endl;
}

/// 糟糕：函数名不清晰
void check() {
    std::cout << "Checking..." << std::endl;
}

/// 糟糕：使用数字后缀
void process2() {
    std::cout << "Processing 2..." << std::endl;
}

/// 糟糕：使用下划线开头
void _internalProcess() {
    std::cout << "Internal processing..." << std::endl;
}

// ============================================================================
// 糟糕的类命名 - 使用模糊的名称
// ============================================================================

/// 糟糕：类名不清晰
class Manager {
public:
    void manage() {
        std::cout << "Managing..." << std::endl;
    }
};

/// 糟糕：类名不清晰
class Handler {
public:
    void handle() {
        std::cout << "Handling..." << std::endl;
    }
};

/// 糟糕：类名不清晰
class Processor {
public:
    void process() {
        std::cout << "Processing..." << std::endl;
    }
};

/// 糟糕：类名不清晰
class Data {
public:
    void process() {
        std::cout << "Processing data..." << std::endl;
    }
};

/// 糟糕：使用全小写
class usermanager {
public:
    void adduser() {
        std::cout << "Adding user..." << std::endl;
    }
};

/// 糟糕：使用下划线
class User_Manager {
public:
    void add_user() {
        std::cout << "Adding user..." << std::endl;
    }
};

// ============================================================================
// 糟糕的枚举命名
// ============================================================================

/// 糟糕：枚举值不清晰
enum Status {
    ACTIVE,      // 应该使用 kActive
    INACTIVE,    // 应该使用 kInactive
    SUSPENDED    // 应该使用 kSuspended
};

/// 糟糕：枚举值不清晰
enum Level {
    DEBUG,       // 应该使用 kDebug
    INFO,        // 应该使用 kInfo
    WARNING,     // 应该使用 kWarning
    ERROR        // 应该使用 kError
};

// ============================================================================
// 糟糕的命名空间命名
// ============================================================================

/// 糟糕：命名空间使用 PascalCase
namespace UserUtils {
    void validate() {
        std::cout << "Validating..." << std::endl;
    }
}

/// 糟糕：命名空间使用全小写
namespace stringutils {
    void trim() {
        std::cout << "Trimming..." << std::endl;
    }
}

/// 糟糕：命名空间使用下划线开头
namespace _internal {
    void process() {
        std::cout << "Processing..." << std::endl;
    }
}

// ============================================================================
// 糟糕的参数命名
// ============================================================================

/// 糟糕：参数名不清晰
void createUser(int a, std::string b, std::string c) {
    std::cout << "Creating user: " << b << std::endl;
}

/// 糟糕：参数名使用缩写
void updateUser(int id, std::string nm, std::string em) {
    std::cout << "Updating user: " << nm << std::endl;
}

/// 糟糕：参数名使用单字母
void processData(int a, int b, int c) {
    std::cout << "Processing: " << a << ", " << b << ", " << c << std::endl;
}

// ============================================================================
// 糟糕的成员变量命名
// ============================================================================

/// 糟糕：成员变量命名不清晰
class BadUser {
public:
    BadUser(int i, std::string n, std::string e)
        : id(i), name(n), email(e), s(0) {}

    void setStatus(int new_s) {
        s = new_s;
    }

private:
    int id;           // 应该使用 id_
    std::string name; // 应该使用 name_
    std::string email;// 应该使用 email_
    int s;            // 应该使用 status_
};

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示糟糕命名规范
 *
 * 注意：这些代码仅用于教学目的，实际项目中应避免使用。
 */
void demonstrateBadNaming() {
    std::cout << "=== 糟糕命名规范示例 ===" << std::endl;
    std::cout << "注意：这些代码仅用于教学目的，实际项目中应避免使用。" << std::endl;

    // 糟糕的变量命名
    std::cout << "\n1. 糟糕的变量命名:" << std::endl;
    int a = 25;
    int b = 30;
    int c = a + b;
    std::cout << "   a = " << a << ", b = " << b << ", c = " << c << std::endl;

    // 糟糕的函数命名
    std::cout << "\n2. 糟糕的函数命名:" << std::endl;
    process();
    handle();
    doSomething();

    // 糟糕的类命名
    std::cout << "\n3. 糟糕的类命名:" << std::endl;
    Manager m;
    m.manage();

    Handler h;
    h.handle();

    Processor p;
    p.process();

    // 糟糕的参数命名
    std::cout << "\n4. 糟糕的参数命名:" << std::endl;
    createUser(1, "Alice", "alice@example.com");
    updateUser(1, "Bob", "bob@example.com");
    processData(1, 2, 3);
}
