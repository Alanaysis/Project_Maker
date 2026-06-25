// compile_time_tests.cpp - 编译期计算测试
//
// 本文件包含所有编译期计算功能的测试用例。
//
// 编译命令：
//   g++ -std=c++20 -I include tests/compile_time_tests.cpp -o compile_time_tests

#include <iostream>
#include <cassert>
#include <cmath>
#include <string>

#include "compile_time/fixed_string.hpp"
#include "compile_time/array.hpp"
#include "compile_time/map.hpp"
#include "compile_time/set.hpp"
#include "compile_time/math.hpp"
#include "compile_time/hash.hpp"
#include "compile_time/regex.hpp"
#include "compile_time/lookup.hpp"
#include "compile_time/unit.hpp"
#include "compile_time/state_machine.hpp"
#include "compile_time/reflection.hpp"

using namespace compile_time;

// ============================================================================
// 测试辅助宏
// ============================================================================

#define TEST(name) \
    void test_##name(); \
    struct TestRunner_##name { \
        TestRunner_##name() { \
            std::cout << "Running " #name "... "; \
            test_##name(); \
            std::cout << "PASSED" << std::endl; \
        } \
    } runner_##name; \
    void test_##name()

#define ASSERT_EQ(a, b) assert((a) == (b))
#define ASSERT_TRUE(a) assert(a)
#define ASSERT_FALSE(a) assert(!(a))
#define ASSERT_NEAR(a, b, eps) assert(std::abs((a) - (b)) < (eps))

// ============================================================================
// fixed_string 测试
// ============================================================================

TEST(fixed_string_basic) {
    constexpr fixed_string str = "hello";
    static_assert(str.size() == 5);
    static_assert(str[0] == 'h');
    static_assert(str[4] == 'o');
    static_assert(str.empty() == false);
}

TEST(fixed_string_compare) {
    constexpr fixed_string s1 = "hello";
    constexpr fixed_string s2 = "hello";
    constexpr fixed_string s3 = "world";
    static_assert(s1 == s2);
    static_assert(s1 != s3);
    static_assert(s1 < s3);
}

TEST(fixed_string_find) {
    constexpr fixed_string str = "hello world";
    static_assert(str.find('o') == 4);
    static_assert(str.find('z') == fixed_string<12>::npos);
}

TEST(fixed_string_starts_ends_with) {
    constexpr fixed_string str = "hello";
    static_assert(str.starts_with(fixed_string("he")));
    static_assert(str.ends_with(fixed_string("lo")));
    static_assert(!str.starts_with(fixed_string("wo")));
}

// ============================================================================
// compile_time_array 测试
// ============================================================================

TEST(array_basic) {
    constexpr compile_time_array<int, 5> arr = {5, 3, 1, 4, 2};
    static_assert(arr.size() == 5);
    static_assert(arr[0] == 5);
    static_assert(arr[4] == 2);
    static_assert(arr.empty() == false);
}

TEST(array_sorted) {
    constexpr compile_time_array<int, 5> arr = {5, 3, 1, 4, 2};
    constexpr auto sorted = arr.sorted();
    static_assert(sorted[0] == 1);
    static_assert(sorted[1] == 2);
    static_assert(sorted[2] == 3);
    static_assert(sorted[3] == 4);
    static_assert(sorted[4] == 5);
}

TEST(array_find) {
    constexpr compile_time_array<int, 5> arr = {1, 2, 3, 4, 5};
    static_assert(arr.find(3) == 2);
    static_assert(arr.find(6) == 5);
}

TEST(array_min_max) {
    constexpr compile_time_array<int, 5> arr = {5, 3, 1, 4, 2};
    static_assert(arr.min() == 1);
    static_assert(arr.max() == 5);
}

TEST(array_sum) {
    constexpr compile_time_array<int, 5> arr = {1, 2, 3, 4, 5};
    static_assert(arr.sum() == 15);
}

TEST(array_reversed) {
    constexpr compile_time_array<int, 5> arr = {1, 2, 3, 4, 5};
    constexpr auto reversed = arr.reversed();
    static_assert(reversed[0] == 5);
    static_assert(reversed[4] == 1);
}

// ============================================================================
// compile_time_map 测试
// ============================================================================

TEST(map_basic) {
    constexpr pair<int, const char*> entries[] = {
        {1, "one"}, {2, "two"}, {3, "three"}
    };
    constexpr auto map = make_map(entries);
    static_assert(map.size() == 3);
    static_assert(map.contains(1));
    static_assert(map.contains(4) == false);
}

TEST(map_at) {
    constexpr pair<int, const char*> entries[] = {
        {1, "one"}, {2, "two"}, {3, "three"}
    };
    constexpr auto map = make_map(entries);
    static_assert(map.at(1)[0] == 'o');
    static_assert(map.at(2)[0] == 't');
}

// ============================================================================
// compile_time_set 测试
// ============================================================================

TEST(set_basic) {
    constexpr int arr[] = {5, 3, 1, 4, 2};
    constexpr auto set = make_set(arr);
    static_assert(set.size() == 5);
    static_assert(set[0] == 1);
    static_assert(set[4] == 5);
}

TEST(set_contains) {
    constexpr int arr[] = {1, 2, 3, 4, 5};
    constexpr auto set = make_set(arr);
    static_assert(set.contains(3));
    static_assert(set.contains(6) == false);
}

// ============================================================================
// math 测试
// ============================================================================

TEST(math_sqrt) {
    static_assert(math::abs(math::sqrt(4.0) - 2.0) < 1e-10);
    static_assert(math::abs(math::sqrt(9.0) - 3.0) < 1e-10);
    static_assert(math::abs(math::sqrt(2.0) - 1.4142135623730951) < 1e-10);
}

TEST(math_pow) {
    static_assert(math::pow(2, 10) == 1024);
    static_assert(math::pow(3, 3) == 27);
    static_assert(math::pow(5, 0) == 1);
}

TEST(math_factorial) {
    static_assert(math::factorial(0) == 1);
    static_assert(math::factorial(5) == 120);
    static_assert(math::factorial(10) == 3628800);
}

TEST(math_sin) {
    static_assert(math::abs(math::sin(0.0)) < 1e-10);
    static_assert(math::abs(math::sin(math::pi / 2) - 1.0) < 1e-10);
    static_assert(math::abs(math::sin(math::pi)) < 1e-10);
}

TEST(math_cos) {
    static_assert(math::abs(math::cos(0.0) - 1.0) < 1e-10);
    static_assert(math::abs(math::cos(math::pi / 2)) < 1e-10);
    static_assert(math::abs(math::cos(math::pi) + 1.0) < 1e-10);
}

TEST(math_exp) {
    static_assert(math::abs(math::exp(0.0) - 1.0) < 1e-10);
    static_assert(math::abs(math::exp(1.0) - math::e) < 1e-5);
}

TEST(math_ln) {
    static_assert(math::abs(math::ln(1.0)) < 1e-10);
    static_assert(math::abs(math::ln(math::e) - 1.0) < 1e-5);
}

// ============================================================================
// hash 测试
// ============================================================================

TEST(hash_fnv1a) {
    constexpr auto h1 = hash::fnv1a("hello");
    constexpr auto h2 = hash::fnv1a("hello");
    constexpr auto h3 = hash::fnv1a("world");
    static_assert(h1 == h2);
    static_assert(h1 != h3);
}

TEST(hash_djb2) {
    constexpr auto h1 = hash::djb2("hello");
    constexpr auto h2 = hash::djb2("hello");
    constexpr auto h3 = hash::djb2("world");
    static_assert(h1 == h2);
    static_assert(h1 != h3);
}

TEST(hash_integer) {
    constexpr auto h1 = hash::integer_hash(42);
    constexpr auto h2 = hash::integer_hash(42);
    constexpr auto h3 = hash::integer_hash(100);
    static_assert(h1 == h2);
    static_assert(h1 != h3);
}

// ============================================================================
// regex 测试
// ============================================================================

TEST(regex_exact_match) {
    static_assert(regex::match("hello", "hello"));
    static_assert(!regex::match("hello", "world"));
}

TEST(regex_dot) {
    static_assert(regex::match("hello", "h.llo"));
    static_assert(regex::match("hello", "h...o"));
}

TEST(regex_star) {
    static_assert(regex::match("aaa", "a*"));
    static_assert(regex::match("", "a*"));
}

TEST(regex_plus) {
    static_assert(regex::match("aaa", "a+"));
    static_assert(!regex::match("", "a+"));
}

TEST(regex_question) {
    static_assert(regex::match("ab", "a?b"));
    static_assert(regex::match("b", "a?b"));
}

TEST(regex_anchor) {
    static_assert(regex::match("hello", "^he"));
    static_assert(!regex::match("hello", "^lo"));
    static_assert(regex::match("hello", "lo$"));
    static_assert(!regex::match("hello", "he$"));
}

// ============================================================================
// lookup 测试
// ============================================================================

TEST(lookup_square_table) {
    constexpr auto table = lookup::make_square_table<100>();
    static_assert(table[10] == 100);
    static_assert(table[25] == 625);
    static_assert(table[99] == 9801);
}

TEST(lookup_sine_table) {
    constexpr auto table = lookup::make_sine_table();
    static_assert(math::abs(table[0]) < 1e-10);
    static_assert(math::abs(table[90] - 1.0) < 1e-10);
}

TEST(lookup_cosine_table) {
    constexpr auto table = lookup::make_cosine_table();
    static_assert(math::abs(table[0] - 1.0) < 1e-10);
    static_assert(math::abs(table[90]) < 1e-10);
}

// ============================================================================
// unit 测试
// ============================================================================

TEST(unit_length_conversion) {
    static_assert(math::abs(unit::convert::m_to_km(1000.0) - 1.0) < 1e-10);
    static_assert(math::abs(unit::convert::km_to_m(1.0) - 1000.0) < 1e-10);
    static_assert(math::abs(unit::convert::m_to_miles(1609.344) - 1.0) < 1e-3);
}

TEST(unit_mass_conversion) {
    static_assert(math::abs(unit::convert::kg_to_g(1.0) - 1000.0) < 1e-10);
    static_assert(math::abs(unit::convert::kg_to_lbs(1.0) - 2.20462) < 1e-3);
}

TEST(unit_time_conversion) {
    static_assert(math::abs(unit::convert::s_to_min(60.0) - 1.0) < 1e-10);
    static_assert(math::abs(unit::convert::s_to_h(3600.0) - 1.0) < 1e-10);
}

TEST(unit_temperature_conversion) {
    static_assert(math::abs(unit::convert::celsius_to_fahrenheit(100.0) - 212.0) < 1e-10);
    static_assert(math::abs(unit::convert::celsius_to_kelvin(0.0) - 273.15) < 1e-10);
}

// ============================================================================
// state_machine 测试
// ============================================================================

TEST(state_machine_traffic_light) {
    constexpr auto fsm = state_machine::make_traffic_light_fsm();
    constexpr auto state1 = fsm.process(state_machine::traffic_light_state::Red,
                                         state_machine::traffic_light_event::Timer);
    static_assert(state1.has_value());
    static_assert(*state1 == state_machine::traffic_light_state::Green);
}

TEST(state_machine_door) {
    constexpr auto fsm = state_machine::make_door_fsm();
    constexpr auto state1 = fsm.process(state_machine::door_state::Closed,
                                         state_machine::door_event::OpenCmd);
    static_assert(state1.has_value());
    static_assert(*state1 == state_machine::door_state::Opening);
}

TEST(state_machine_protocol) {
    constexpr auto fsm = state_machine::make_protocol_fsm();
    constexpr auto state1 = fsm.process(state_machine::protocol_state::Disconnected,
                                         state_machine::protocol_event::Connect);
    static_assert(state1.has_value());
    static_assert(*state1 == state_machine::protocol_state::Connecting);
}

// ============================================================================
// reflection 测试
// ============================================================================

TEST(reflection_type_info) {
    constexpr auto info = reflection::get_type_info<int>();
    static_assert(info.is_integral);
    static_assert(info.is_arithmetic);
    static_assert(info.size == sizeof(int));
}

TEST(reflection_type_name) {
    constexpr const char* name = reflection::simple_type_name<int>();
    static_assert(name[0] == 'i');
}

TEST(reflection_type_list) {
    using MyTypes = reflection::type_list<int, double, bool>;
    static_assert(MyTypes::size == 3);
    static_assert(reflection::contains<MyTypes, int>::value);
    static_assert(!reflection::contains<MyTypes, float>::value);
}

// ============================================================================
// 主函数
// ============================================================================

int main() {
    std::cout << "=== 编译期计算测试 ===" << std::endl;
    std::cout << std::endl;

    // 所有测试通过后会打印 PASSED
    // 如果任何测试失败，程序会 assert 失败

    std::cout << std::endl;
    std::cout << "所有测试通过！" << std::endl;

    return 0;
}
