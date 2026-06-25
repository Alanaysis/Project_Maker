/**
 * @file filesystem_example.cpp
 * @brief Boost.Filesystem 文件系统示例
 * @details 展示 Boost.Filesystem 的基本用法
 *          提供跨平台的文件系统操作
 */

#include <iostream>
#include <string>
#include <vector>
#include <boost/filesystem.hpp>

namespace fs = boost::filesystem;

/**
 * @brief 路径操作示例
 * @details 展示路径的基本操作
 */
void path_operations() {
    std::cout << "=== 路径操作 ===" << std::endl;

    // 创建路径
    fs::path p("/home/user/documents/file.txt");

    std::cout << "Full path: " << p << std::endl;
    std::cout << "Filename: " << p.filename() << std::endl;
    std::cout << "Stem: " << p.stem() << std::endl;
    std::cout << "Extension: " << p.extension() << std::endl;
    std::cout << "Parent path: " << p.parent_path() << std::endl;

    // 路径组合
    fs::path base("/home/user");
    fs::path relative("documents/file.txt");
    fs::path full = base / relative;

    std::cout << "Combined path: " << full << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 文件操作示例
 * @details 展示文件的基本操作
 */
void file_operations() {
    std::cout << "=== 文件操作 ===" << std::endl;

    fs::path test_file("test.txt");

    // 检查文件是否存在
    if (fs::exists(test_file)) {
        std::cout << "File exists" << std::endl;
        std::cout << "Size: " << fs::file_size(test_file) << " bytes" << std::endl;
    } else {
        std::cout << "File does not exist" << std::endl;
    }

    // 检查路径类型
    fs::path dir("/tmp");
    if (fs::is_directory(dir)) {
        std::cout << dir << " is a directory" << std::endl;
    }

    fs::path file("/etc/hostname");
    if (fs::is_regular_file(file)) {
        std::cout << file << " is a regular file" << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 目录操作示例
 * @details 展示目录的基本操作
 */
void directory_operations() {
    std::cout << "=== 目录操作 ===" << std::endl;

    // 创建目录
    fs::path test_dir("test_directory");
    if (!fs::exists(test_dir)) {
        fs::create_directory(test_dir);
        std::cout << "Created directory: " << test_dir << std::endl;
    }

    // 遍历目录
    fs::path current_dir(".");
    std::cout << "Current directory contents:" << std::endl;
    for (const auto& entry : fs::directory_iterator(current_dir)) {
        std::cout << "  " << entry.path().filename() << std::endl;
    }

    // 递归遍历
    // fs::path root_dir("/tmp");
    // for (const auto& entry : fs::recursive_directory_iterator(root_dir)) {
    //     std::cout << "  " << entry.path() << std::endl;
    // }

    // 删除目录
    if (fs::exists(test_dir)) {
        fs::remove(test_dir);
        std::cout << "Removed directory: " << test_dir << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 文件复制和移动示例
 * @details 展示文件的复制和移动操作
 */
void file_copy_move() {
    std::cout << "=== 文件复制和移动 ===" << std::endl;

    // 创建测试文件
    fs::path source("source.txt");
    fs::path destination("destination.txt");
    fs::path moved("moved.txt");

    // 注意：这里只是示例代码，实际使用时需要确保文件存在

    // 复制文件
    // fs::copy_file(source, destination);

    // 移动文件
    // fs::rename(destination, moved);

    // 删除文件
    // fs::remove(moved);

    std::cout << "File operations completed" << std::endl;

    std::cout << std::endl;
}

/**
 * @brief 文件属性示例
 * @details 展示如何获取文件属性
 */
void file_attributes() {
    std::cout << "=== 文件属性 ===" << std::endl;

    fs::path p("/etc/hostname");

    if (fs::exists(p)) {
        std::cout << "Path: " << p << std::endl;

        // 获取文件大小
        if (fs::is_regular_file(p)) {
            std::cout << "Size: " << fs::file_size(p) << " bytes" << std::endl;
        }

        // 获取最后修改时间
        auto time = fs::last_write_time(p);
        std::cout << "Last modified: " << time << std::endl;
    }

    std::cout << std::endl;
}

/**
 * @brief 实际应用场景
 * @details 展示 Boost.Filesystem 在实际项目中的应用
 */
void real_world_example() {
    std::cout << "=== 实际应用场景 ===" << std::endl;

    // 场景：查找特定扩展名的文件
    fs::path directory(".");
    std::vector<std::string> extensions = {".cpp", ".h", ".hpp"};

    std::cout << "Source files in current directory:" << std::endl;
    for (const auto& entry : fs::directory_iterator(directory)) {
        if (fs::is_regular_file(entry)) {
            std::string ext = entry.path().extension().string();
            for (const auto& target_ext : extensions) {
                if (ext == target_ext) {
                    std::cout << "  " << entry.path().filename() << std::endl;
                    break;
                }
            }
        }
    }

    // 场景：创建目录结构
    fs::path project_dir("my_project");
    fs::path src_dir = project_dir / "src";
    fs::path include_dir = project_dir / "include";
    fs::path build_dir = project_dir / "build";

    // fs::create_directories(src_dir);
    // fs::create_directories(include_dir);
    // fs::create_directories(build_dir);

    std::cout << "\nProject structure created" << std::endl;

    std::cout << std::endl;
}

int main() {
    std::cout << "=== Boost.Filesystem 文件系统示例 ===" << std::endl;
    std::cout << std::endl;

    path_operations();
    file_operations();
    directory_operations();
    file_copy_move();
    file_attributes();
    real_world_example();

    std::cout << "=== 示例结束 ===" << std::endl;
    return 0;
}