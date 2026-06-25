# SFML 多媒体库示例
find_package(SFML COMPONENTS system window graphics REQUIRED)

# 基础示例
add_executable(sfml_basic basic_window.cpp)
target_link_libraries(sfml_basic PRIVATE sfml-system sfml-window sfml-graphics)