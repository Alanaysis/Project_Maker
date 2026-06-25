# Armadillo 线性代数库示例
find_package(Armadillo REQUIRED)

# 基础示例
add_executable(armadillo_basic basic_example.cpp)
target_link_libraries(armadillo_basic PRIVATE Armadillo::Armadillo)