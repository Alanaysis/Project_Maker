# Protobuf 序列化示例
find_package(Protobuf REQUIRED)

# 生成 protobuf 代码
protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS proto/message.proto)

# 基础示例
add_executable(protobuf_basic basic_example.cpp ${PROTO_SRCS} ${PROTO_HDRS})
target_include_directories(protobuf_basic PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
target_link_libraries(protobuf_basic PRIVATE protobuf::libprotobuf)