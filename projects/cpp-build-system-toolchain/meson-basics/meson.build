# ============================================================================
# Meson 构建系统基础示例
# 本文件展示 Meson 的基本用法，包括：
# - 项目声明
# - 可执行文件创建
# - 静态库/动态库创建
# - 依赖管理
# - 测试配置
# ============================================================================

project('meson_basics', 'cpp',
    version: '1.0.0',
    default_options: [
        'cpp_std=c++17',
        'warning_level=2',
        'buildtype=release',
    ]
)

# 获取编译器信息
compiler = meson.get_compiler('cpp')
message('编译器: @0@'.format(compiler.get_id()))
message('编译器版本: @0@'.format(compiler.version()))

# ============================================================================
# 1. 创建静态库
# ============================================================================
math_utils_lib = static_library('math_utils',
    'src/math_utils.cpp',
    include_directories: include_directories('include'),
    install: true,
)

# ============================================================================
# 2. 创建动态库
# ============================================================================
string_utils_lib = shared_library('string_utils',
    'src/string_utils.cpp',
    include_directories: include_directories('include'),
    version: '1.0.0',
    soversion: '1',
    install: true,
)

# ============================================================================
# 3. 创建可执行文件
# ============================================================================
executable('hello_world',
    'src/hello.cpp',
    include_directories: include_directories('include'),
    link_with: [math_utils_lib, string_utils_lib],
    install: true,
)

# ============================================================================
# 4. 测试配置
# ============================================================================
test_exe = executable('test_math',
    'tests/test_math.cpp',
    include_directories: include_directories('include'),
    link_with: [math_utils_lib],
)

test('math_tests', test_exe)

# ============================================================================
# 5. 依赖管理（示例：使用系统库）
# ============================================================================
# zlib_dep = dependency('zlib', required: true)
# executable('zlib_example',
#     'src/zlib_example.cpp',
#     dependencies: [zlib_dep],
# )
