# 示例 CMakeLists.txt

# 示例源文件
set(EXAMPLE_SOURCES
    example_basic.cpp
    example_collision.cpp
    example_constraints.cpp
    example_pendulum.cpp
)

# 创建示例可执行文件
foreach(example_source ${EXAMPLE_SOURCES})
    get_filename_component(example_name ${example_source} NAME_WE)
    add_executable(${example_name} ${example_source})
    target_link_libraries(${example_name} PRIVATE physics_engine)
endforeach()
