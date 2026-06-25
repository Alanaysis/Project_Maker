# SDL 多媒体库示例
find_package(SDL2 REQUIRED)

# 基础示例
add_executable(sdl_basic basic_window.cpp)
target_link_libraries(sdl_basic PRIVATE SDL2::SDL2)