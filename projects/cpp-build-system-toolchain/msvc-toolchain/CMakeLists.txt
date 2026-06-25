cmake_minimum_required(VERSION 3.16)

# ============================================================================
# MSVC 工具链示例
# 本文件展示 MSVC 编译器的选项和配置
# ============================================================================

project(MsvcToolchain
    VERSION 1.0.0
    DESCRIPTION "MSVC 工具链示例"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ============================================================================
# 1. MSVC 特定编译选项
# ============================================================================
add_executable(msvc_demo src/msvc_demo.cpp)

if(MSVC)
    target_compile_options(msvc_demo PRIVATE
        /W4             # 警告级别 4
        /WX             # 将警告视为错误
        /permissive-    # 严格标准符合性
        /Zc:__cplusplus # 正确报告 __cplusplus 宏
        /Zc:externConstexpr  # 支持 extern constexpr
        /Zc:inline      # 移除未使用的内联函数
        /Zc:throwingNew # 支持 noexcept new
        /utf-8          # 源文件使用 UTF-8 编码
        /EHsc           # 启用 C++ 异常处理
    )

    # Debug 特定选项
    target_compile_options(msvc_demo PRIVATE
        $<$<CONFIG:Debug>:/MDd /Zi /Ob0 /Od /RTC1>
    )

    # Release 特定选项
    target_compile_options(msvc_demo PRIVATE
        $<$<CONFIG:Release>:/MD /O2 /Ob2 /DNDEBUG>
    )

    # 链接选项
    target_link_options(msvc_demo PRIVATE
        /INCREMENTAL:NO  # 禁用增量链接
        /OPT:REF         # 优化引用
        /OPT:ICF         # 折叠相同函数
    )
else()
    # 非 MSVC 编译器的通用选项
    target_compile_options(msvc_demo PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

# ============================================================================
# 2. Windows 特定定义
# ============================================================================
target_compile_definitions(msvc_demo PRIVATE
    # Windows 版本
    $<$<PLATFORM_ID:Windows>:_WIN32_WINNT=0x0A00>
    $<$<PLATFORM_ID:Windows>:WINVER=0x0A00>

    # Unicode 支持
    $<$<PLATFORM_ID:Windows>:UNICODE>
    $<$<PLATFORM_ID:Windows>:_UNICODE>
)

# ============================================================================
# 3. MSVC 运行时库配置
# ============================================================================
if(MSVC)
    # 使用动态运行时库
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL")
endif()
