/**
 * reflection.cpp - 基础反射机制
 *
 * 本文件演示 C++ 中实现反射的技术，包括：
 *   1. 使用宏实现结构体字段反射
 *   2. 成员枚举（遍历结构体所有字段）
 *   3. 编译期反射的概念
 *   4. 实际应用场景（序列化、打印、比较）
 *
 * C++ 没有原生的运行时反射，需要通过宏和模板技巧来实现。
 * C++26 正在讨论引入编译期反射（P2996）。
 *
 * 编译命令:
 *   g++ -std=c++17 -o reflection reflection.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <sstream>
#include <vector>
#include <map>
#include <tuple>
#include <type_traits>
#include <functional>
#include <cstring>
#include <iomanip>
#include <algorithm>
#include <optional>
#include <typeinfo>

// ============================================================================
// 第一部分: 基础结构体反射宏
// ============================================================================
// 核心思想：通过宏记录每个字段的名称和偏移量，
// 从而在运行时遍历结构体的所有字段。

// 辅助宏：字段信息存储
// 每个字段记录：名称（字符串）、类型（字符串）、偏移量
struct FieldInfo {
    const char* name;       // 字段名
    const char* type_name;  // 类型名
    size_t offset;          // 在结构体中的偏移量
    size_t size;            // 字段大小

    // 获取字段在实例中的地址
    template <typename T>
    void* get_ptr(T* obj) const {
        return reinterpret_cast<char*>(obj) + offset;
    }

    // 获取字段值（以字符串形式）
    // 使用字段大小来推断类型并格式化输出
    template <typename T>
    std::string get_value_str(const T* obj) const {
        const void* ptr = get_ptr(const_cast<T*>(obj));

        // 根据字段大小推断类型
        if (size == sizeof(int)) {
            return std::to_string(*static_cast<const int*>(ptr));
        }
        if (size == sizeof(double)) {
            std::ostringstream oss;
            oss << std::fixed << std::setprecision(2)
                << *static_cast<const double*>(ptr);
            return oss.str();
        }
        if (size == sizeof(float)) {
            std::ostringstream oss;
            oss << std::fixed << std::setprecision(2)
                << *static_cast<const float*>(ptr);
            return oss.str();
        }
        if (size == sizeof(bool)) {
            return *static_cast<const bool*>(ptr) ? "true" : "false";
        }
        if (size == sizeof(std::string)) {
            return "\"" + *static_cast<const std::string*>(ptr) + "\"";
        }

        return "<?>";
    }
};

// 类型名获取的辅助模板
// 使用 constexpr 函数在编译期获取类型名
template <typename T>
constexpr const char* type_name_impl() {
#if defined(__GNUC__) || defined(__clang__)
    return __PRETTY_FUNCTION__;
#elif defined(_MSC_VER)
    return __FUNCSIG__;
#endif
}

// 简化的类型名提取（用于演示）
#define TYPE_NAME(Type) #Type

// ============================================================================
// 第二部分: REFLECT 宏实现
// ============================================================================
// 这是本文件的核心宏，用于为结构体添加反射能力
//
// 使用方式:
//   struct Person {
//       int age;
//       std::string name;
//       REFLECT(Person, age, name)
//   };
//
// REFLECT 宏会为结构体添加:
//   - fields(): 返回字段信息的静态方法
//   - field_count(): 返回字段数量
//   - for_each_field(visitor): 遍历所有字段

// 辅助函数：根据类型大小和结构体信息推断类型名
inline const char* infer_type_name(size_t size, bool is_signed) {
    if (size == 1) return "bool/char";
    if (size == 4) return "int/float";
    if (size == 8) return "double/int64";
    if (size > 8) return "std::string/complex";
    return "unknown";
}

// 辅助宏：为单个字段生成 FieldInfo
// 使用 typeid 在运行时获取类型名（更准确）
#define FIELD_INFO(StructType, field) \
    FieldInfo{#field, typeid(decltype(StructType::field)).name(), \
              offsetof(StructType, field), sizeof(StructType::field)}

// 可变参数展开辅助宏（支持最多 20 个字段）
#define FE_1(Struct, f)   FIELD_INFO(Struct, f)
#define FE_2(Struct, f, ...)  FIELD_INFO(Struct, f), FE_1(Struct, __VA_ARGS__)
#define FE_3(Struct, f, ...)  FIELD_INFO(Struct, f), FE_2(Struct, __VA_ARGS__)
#define FE_4(Struct, f, ...)  FIELD_INFO(Struct, f), FE_3(Struct, __VA_ARGS__)
#define FE_5(Struct, f, ...)  FIELD_INFO(Struct, f), FE_4(Struct, __VA_ARGS__)
#define FE_6(Struct, f, ...)  FIELD_INFO(Struct, f), FE_5(Struct, __VA_ARGS__)
#define FE_7(Struct, f, ...)  FIELD_INFO(Struct, f), FE_6(Struct, __VA_ARGS__)
#define FE_8(Struct, f, ...)  FIELD_INFO(Struct, f), FE_7(Struct, __VA_ARGS__)
#define FE_9(Struct, f, ...)  FIELD_INFO(Struct, f), FE_8(Struct, __VA_ARGS__)
#define FE_10(Struct, f, ...) FIELD_INFO(Struct, f), FE_9(Struct, __VA_ARGS__)

// 计数宏
#define GET_MACRO(_1,_2,_3,_4,_5,_6,_7,_8,_9,_10,NAME,...) NAME
#define EXPAND(x) x
#define FOR_EACH_FIELD(Struct, ...) \
    EXPAND(GET_MACRO(__VA_ARGS__, \
        FE_10, FE_9, FE_8, FE_7, FE_6, \
        FE_5, FE_4, FE_3, FE_2, FE_1)(Struct, __VA_ARGS__))

// 主 REFLECT 宏
// 注意: field_count() 使用运行时调用 fields().size()，因为宏内无法展开参数包
#define REFLECT(StructType, ...) \
    static std::vector<FieldInfo>& fields() { \
        static std::vector<FieldInfo> _fields = { \
            FOR_EACH_FIELD(StructType, __VA_ARGS__) \
        }; \
        return _fields; \
    } \
    static size_t field_count() { \
        return fields().size(); \
    } \
    template <typename Visitor> \
    void for_each_field(Visitor&& visitor) { \
        for (const auto& fi : fields()) { \
            visitor(fi.name, fi.get_ptr(this), fi.size); \
        } \
    }

// ============================================================================
// 第三部分: 基于反射的实用工具
// ============================================================================
// 利用反射实现的通用工具函数

namespace reflect_utils {

    // 通用打印函数 - 自动打印结构体所有字段
    template <typename T>
    void print(const T& obj, const std::string& name = "") {
        if (!name.empty()) {
            std::cout << name << " {" << std::endl;
        } else {
            std::cout << typeid(T).name() << " {" << std::endl;
        }

        for (const auto& field : T::fields()) {
            std::cout << "  " << field.name << ": "
                      << field.get_value_str(&obj)
                      << " [" << field.type_name << "]" << std::endl;
        }
        std::cout << "}" << std::endl;
    }

    // 通用转 JSON 函数
    template <typename T>
    std::string to_json(const T& obj, int indent = 2) {
        std::ostringstream oss;
        oss << "{\n";
        const auto& flds = T::fields();
        for (size_t i = 0; i < flds.size(); ++i) {
            oss << std::string(indent, ' ')
                << "\"" << flds[i].name << "\": "
                << flds[i].get_value_str(&obj);
            if (i + 1 < flds.size()) oss << ",";
            oss << "\n";
        }
        oss << "}";
        return oss.str();
    }

    // 通用相等比较
    template <typename T>
    bool equal(const T& a, const T& b) {
        for (const auto& field : T::fields()) {
            const void* pa = field.get_ptr(const_cast<T*>(&a));
            const void* pb = field.get_ptr(const_cast<T*>(&b));
            if (std::memcmp(pa, pb, field.size) != 0) {
                return false;
            }
        }
        return true;
    }

    // 通用拷贝
    template <typename T>
    void copy(T& dst, const T& src) {
        for (const auto& field : T::fields()) {
            void* pd = field.get_ptr(&dst);
            const void* ps = field.get_ptr(const_cast<T*>(&src));
            std::memcpy(pd, ps, field.size);
        }
    }

    // 获取字段名列表
    template <typename T>
    std::vector<std::string> field_names() {
        std::vector<std::string> names;
        for (const auto& field : T::fields()) {
            names.push_back(field.name);
        }
        return names;
    }

}  // namespace reflect_utils

// ============================================================================
// 第四部分: 定义可反射的结构体
// ============================================================================

// 示例 1: 人物信息
struct Person {
    int id;
    std::string name;
    int age;
    double height;

    // 添加反射支持 - 只需列出所有需要反射的字段
    REFLECT(Person, id, name, age, height)
};

// 示例 2: 游戏配置
struct GameConfig {
    int screen_width;
    int screen_height;
    bool fullscreen;
    float volume;
    std::string player_name;

    REFLECT(GameConfig, screen_width, screen_height, fullscreen, volume, player_name)
};

// 示例 3: 数据库记录
struct UserRecord {
    int64_t user_id;
    std::string username;
    std::string email;
    bool active;

    REFLECT(UserRecord, user_id, username, email, active)
};

// ============================================================================
// 第五部分: 编译期反射概念演示
// ============================================================================
// 展示 C++17/20 中可用于实现编译期元编程的技术

namespace compile_time {

    // 编译期字符串（简化版）
    // C++20 可以使用 constexpr std::string，这里展示 C++17 的技巧
    template <size_t N>
    struct FixedString {
        char data[N]{};
        constexpr FixedString(const char (&str)[N]) {
            for (size_t i = 0; i < N; ++i) data[i] = str[i];
        }
        constexpr operator std::string_view() const {
            return std::string_view(data, N - 1);
        }
    };

    // 编译期类型列表
    template <typename... Ts>
    struct TypeList {
        static constexpr size_t size = sizeof...(Ts);
    };

    // 获取类型列表中的第 N 个类型
    template <size_t N, typename... Ts>
    struct TypeAt;

    template <typename T, typename... Ts>
    struct TypeAt<0, T, Ts...> {
        using type = T;
    };

    template <size_t N, typename T, typename... Ts>
    struct TypeAt<N, T, Ts...> {
        using type = typename TypeAt<N - 1, Ts...>::type;
    };

    // 编译期字段描述符
    template <FixedString Name, typename T, size_t Offset>
    struct FieldDescriptor {
        static constexpr auto name = Name;
        using type = T;
        static constexpr size_t offset = Offset;
    };

    // 类型特征检测 - 检查类型是否有 fields() 方法
    // 这是 SFINAE 的经典应用
    template <typename T, typename = void>
    struct has_reflection : std::false_type {};

    template <typename T>
    struct has_reflection<T, std::void_t<decltype(T::fields())>> : std::true_type {};

    // 便捷变量模板
    template <typename T>
    constexpr bool has_reflection_v = has_reflection<T>::value;

    // 检查类型是否可反射
    template <typename T>
    constexpr bool is_reflectable() {
        return has_reflection_v<T>;
    }

}  // namespace compile_time

// ============================================================================
// 第六部分: 高级反射应用 - 类型安全的属性访问器
// ============================================================================

// 属性访问器 - 通过名称字符串访问结构体字段
// 使用字段大小来推断类型（因为 typeid 名称是 mangled 的）
class PropertyAccessor {
public:
    // 设置整型属性
    template <typename T>
    static bool set_int(T& obj, const std::string& field_name, int value) {
        for (const auto& field : T::fields()) {
            if (field.name == field_name) {
                if (field.size == sizeof(int)) {
                    *static_cast<int*>(field.get_ptr(&obj)) = value;
                    return true;
                }
                if (field.size == sizeof(double)) {
                    *static_cast<double*>(field.get_ptr(&obj)) = static_cast<double>(value);
                    return true;
                }
            }
        }
        return false;
    }

    // 设置字符串属性
    template <typename T>
    static bool set_string(T& obj, const std::string& field_name,
                           const std::string& value) {
        for (const auto& field : T::fields()) {
            if (field.name == field_name) {
                if (field.size == sizeof(std::string)) {
                    *static_cast<std::string*>(field.get_ptr(&obj)) = value;
                    return true;
                }
            }
        }
        return false;
    }

    // 获取整型属性
    template <typename T>
    static std::optional<int> get_int(const T& obj, const std::string& field_name) {
        for (const auto& field : T::fields()) {
            if (field.name == field_name) {
                if (field.size == sizeof(int)) {
                    return *static_cast<const int*>(
                        field.get_ptr(const_cast<T*>(&obj)));
                }
            }
        }
        return std::nullopt;
    }
};

// ============================================================================
// 演示代码
// ============================================================================

void demo_basic_reflection() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. 基础结构体反射" << std::endl;
    std::cout << "========================================" << std::endl;

    Person person{1, "张三", 28, 175.5};

    // 使用 reflect_utils 打印
    std::cout << "打印 Person:" << std::endl;
    reflect_utils::print(person, "person");

    // 输出为 JSON
    std::cout << "\nJSON 格式:" << std::endl;
    std::cout << reflect_utils::to_json(person) << std::endl;

    // 获取字段名列表
    std::cout << "\n字段名列表: ";
    for (const auto& name : reflect_utils::field_names<Person>()) {
        std::cout << "[" << name << "] ";
    }
    std::cout << std::endl;

    // 遍历字段信息
    std::cout << "\n字段详情:" << std::endl;
    for (const auto& field : Person::fields()) {
        std::cout << "  " << field.name
                  << " (类型: " << field.type_name
                  << ", 偏移: " << field.offset
                  << ", 大小: " << field.size << ")" << std::endl;
    }
}

void demo_game_config() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "2. 游戏配置反射" << std::endl;
    std::cout << "========================================" << std::endl;

    GameConfig config{1920, 1080, true, 0.8f, "玩家一号"};

    std::cout << "游戏配置:" << std::endl;
    reflect_utils::print(config, "config");

    std::cout << "\nJSON:" << std::endl;
    std::cout << reflect_utils::to_json(config) << std::endl;
}

void demo_property_access() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "3. 属性访问器" << std::endl;
    std::cout << "========================================" << std::endl;

    Person person{1, "张三", 28, 175.5};

    // 通过字符串名称访问字段
    std::cout << "原始值:" << std::endl;
    reflect_utils::print(person);

    // 修改字段
    PropertyAccessor::set_int(person, "age", 30);
    PropertyAccessor::set_string(person, "name", "李四");

    std::cout << "\n修改后:" << std::endl;
    reflect_utils::print(person);

    // 读取字段
    auto age = PropertyAccessor::get_int(person, "age");
    if (age) {
        std::cout << "\n通过属性访问器读取 age = " << *age << std::endl;
    }
}

void demo_compile_time() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "4. 编译期反射概念" << std::endl;
    std::cout << "========================================" << std::endl;

    // 类型特征检测
    std::cout << "Person 可反射: "
              << (compile_time::is_reflectable<Person>() ? "是" : "否") << std::endl;
    std::cout << "int 可反射: "
              << (compile_time::is_reflectable<int>() ? "是" : "否") << std::endl;

    // 编译期类型列表
    using Types = compile_time::TypeList<int, double, std::string>;
    std::cout << "\nTypeList 包含 " << Types::size << " 个类型" << std::endl;

    // 获取第 N 个类型
    using T0 = compile_time::TypeAt<0, int, double, std::string>::type;
    using T1 = compile_time::TypeAt<1, int, double, std::string>::type;
    static_assert(std::is_same_v<T0, int>, "第0个类型应该是 int");
    static_assert(std::is_same_v<T1, double>, "第1个类型应该是 double");
    std::cout << "TypeAt<0> = int: 验证通过" << std::endl;
    std::cout << "TypeAt<1> = double: 验证通过" << std::endl;
}

void demo_comparison() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "5. 反射比较与拷贝" << std::endl;
    std::cout << "========================================" << std::endl;

    Person p1{1, "张三", 28, 175.5};
    Person p2{1, "张三", 28, 175.5};
    Person p3{2, "李四", 30, 180.0};

    // 通用比较
    std::cout << "p1 == p2: "
              << (reflect_utils::equal(p1, p2) ? "相等" : "不等") << std::endl;
    std::cout << "p1 == p3: "
              << (reflect_utils::equal(p1, p3) ? "相等" : "不等") << std::endl;

    // 通用拷贝
    Person p4{};
    reflect_utils::copy(p4, p1);
    std::cout << "\n拷贝 p1 到 p4:" << std::endl;
    reflect_utils::print(p4, "p4");

    // 使用 for_each_field 遍历
    std::cout << "\n使用 for_each_field 遍历 p1:" << std::endl;
    p1.for_each_field([&](const char* name, void* ptr, size_t size) {
        std::cout << "  " << name << " (大小: " << size << " 字节)" << std::endl;
    });
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║    C++ 反射机制 (reflection)         ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_basic_reflection();
    demo_game_config();
    demo_property_access();
    demo_compile_time();
    demo_comparison();

    std::cout << "\n反射机制演示完成。" << std::endl;
    return 0;
}
