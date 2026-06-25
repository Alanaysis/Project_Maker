-- ============================================================================
-- xmake 构建系统基础示例
-- 本文件展示 xmake 的基本用法，包括：
-- - 项目声明
-- - 可执行文件创建
-- - 静态库/动态库创建
-- - 依赖管理
-- - 测试配置
-- ============================================================================

-- 设置项目信息
set_project("xmake_basics")
set_version("1.0.0")

-- 设置 C++ 标准
set_languages("c++17")

-- 设置编译警告
set_warnings("all", "extra")

-- ============================================================================
-- 1. 静态库
-- ============================================================================
target("math_utils")
    set_kind("static")
    add_files("src/math_utils.cpp")
    add_headerfiles("include/math_utils.h")
    add_includedirs("include", {public = true})
target_end()

-- ============================================================================
-- 2. 动态库
-- ============================================================================
target("string_utils")
    set_kind("shared")
    add_files("src/string_utils.cpp")
    add_headerfiles("include/string_utils.h")
    add_includedirs("include", {public = true})
    set_version("1.0.0")
    set_soversion("1")
target_end()

-- ============================================================================
-- 3. 可执行文件
-- ============================================================================
target("hello_world")
    set_kind("binary")
    add_files("src/hello.cpp")
    add_deps("math_utils", "string_utils")
    add_includedirs("include")
target_end()

-- ============================================================================
-- 4. 测试
-- ============================================================================
target("test_math")
    set_kind("binary")
    add_files("tests/test_math.cpp")
    add_deps("math_utils")
    add_includedirs("include")
    set_group("tests")

    -- 添加测试
    after_build(function (target)
        -- 可以在这里添加测试逻辑
    end)
target_end()

-- ============================================================================
-- 5. 依赖管理（示例）
-- ============================================================================
-- add_requires("fmt 10.1.1")
-- add_requires("spdlog 1.12.0")
--
-- target("deps_example")
--     set_kind("binary")
--     add_files("src/deps_example.cpp")
--     add_packages("fmt", "spdlog")
-- target_end()
