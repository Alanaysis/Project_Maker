# Cap'n Proto 序列化示例
find_package(CapnProto REQUIRED)

# 生成 capnp 代码
# capnp compile -oc++ schemas/message.capnp

# 基础示例（需要先生成代码）
# add_executable(capnproto_basic basic_example.cpp)
# target_link_libraries(capnproto_basic PRIVATE CapnProto::capnp)