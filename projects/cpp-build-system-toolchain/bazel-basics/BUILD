# ============================================================================
# Bazel BUILD 文件
# 定义项目的构建规则
# ============================================================================

# 默认 C++ 标准设置
package(default_visibility = ["//visibility:public"])

# 静态库
cc_library(
    name = "math_utils",
    srcs = ["src/math_utils.cpp"],
    hdrs = ["include/math_utils.h"],
    includes = ["include"],
)

# 动态库
cc_library(
    name = "string_utils",
    srcs = ["src/string_utils.cpp"],
    hdrs = ["include/string_utils.h"],
    includes = ["include"],
)

# 可执行文件
cc_binary(
    name = "hello_world",
    srcs = ["src/hello.cpp"],
    deps = [
        ":math_utils",
        ":string_utils",
    ],
)

# 测试
cc_test(
    name = "math_test",
    srcs = ["tests/test_math.cpp"],
    deps = [":math_utils"],
)
