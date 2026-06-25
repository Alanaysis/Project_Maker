# ============================================================================
# 应用程序
# ============================================================================

add_executable(myapp main.cpp)
target_link_libraries(myapp PRIVATE mylib)
set_project_warnings(myapp)
enable_sanitizers(myapp)
