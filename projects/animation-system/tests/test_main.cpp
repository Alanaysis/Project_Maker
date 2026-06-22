#include <iostream>
#include <cmath>
#include <cassert>
#include <vector>
#include <memory>

// Include all headers
#include "MathTypes.h"
#include "Bone.h"
#include "Skeleton.h"
#include "Animation.h"
#include "Animator.h"
#include "Skinning.h"

using namespace anim;

// Test helper
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) void test_##name()
#define RUN_TEST(name) do { \
    std::cout << "Running " #name "... "; \
    try { test_##name(); std::cout << "PASSED" << std::endl; tests_passed++; } \
    catch (const std::exception& e) { std::cout << "FAILED: " << e.what() << std::endl; tests_failed++; } \
} while(0)

#define ASSERT_FLOAT_EQ(a, b) assert(std::abs((a) - (b)) < 1e-4f)
#define ASSERT_VEC3_EQ(a, b) do { ASSERT_FLOAT_EQ(a.x, b.x); ASSERT_FLOAT_EQ(a.y, b.y); ASSERT_FLOAT_EQ(a.z, b.z); } while(0)
#define ASSERT_TRUE(x) assert(x)

// Forward declarations of test functions
TEST(math_types);
TEST(quaternion);
TEST(skeleton_basic);
TEST(skeleton_hierarchy);
TEST(animation_sampling);
TEST(animation_blending);
TEST(skinning_basic);
TEST(full_pipeline);

// Include test implementations
#include "test_skeleton.cpp"
#include "test_animation.cpp"
#include "test_skinning.cpp"

int main() {
    std::cout << "=== Animation System Tests ===" << std::endl << std::endl;

    RUN_TEST(math_types);
    RUN_TEST(quaternion);
    RUN_TEST(skeleton_basic);
    RUN_TEST(skeleton_hierarchy);
    RUN_TEST(animation_sampling);
    RUN_TEST(animation_blending);
    RUN_TEST(skinning_basic);
    RUN_TEST(full_pipeline);

    std::cout << std::endl;
    std::cout << "Results: " << tests_passed << " passed, " << tests_failed << " failed" << std::endl;
    return tests_failed > 0 ? 1 : 0;
}
