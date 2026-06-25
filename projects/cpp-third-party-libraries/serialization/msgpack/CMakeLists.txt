# MessagePack 序列化示例
find_package(msgpack REQUIRED)

# 基础示例
add_executable(msgpack_basic basic_example.cpp)
target_link_libraries(msgpack_basic PRIVATE msgpack-cxx)