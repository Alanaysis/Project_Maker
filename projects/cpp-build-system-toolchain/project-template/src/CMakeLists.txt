# ============================================================================
# 库源文件
# ============================================================================

add_library(mylib STATIC
    core.cpp
    string_utils.cpp
    math_utils.cpp
)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(mylib PUBLIC cxx_std_17)

set_project_warnings(mylib)
enable_sanitizers(mylib)

# 设置库属性
set_target_properties(mylib PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)
