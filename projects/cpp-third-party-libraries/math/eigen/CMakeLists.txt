# Eigen 线性代数库示例
find_package(Eigen3 REQUIRED)

# 矩阵运算示例
add_executable(eigen_matrix matrix_example.cpp)
target_link_libraries(eigen_matrix PRIVATE Eigen3::Eigen)

# 线性代数示例
add_executable(eigen_linear_algebra linear_algebra_example.cpp)
target_link_libraries(eigen_linear_algebra PRIVATE Eigen3::Eigen)