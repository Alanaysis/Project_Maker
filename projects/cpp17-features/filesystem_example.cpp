/**
 * @file filesystem_example.cpp
 * @brief C++17 std::filesystem 示例
 *
 * std::filesystem 提供了跨平台的文件系统操作接口。
 * 它封装了目录遍历、文件操作、路径处理等功能。
 *
 * 主要优势：
 * 1. 跨平台 - 统一的 API，无需关心平台差异
 * 2. 功能完整 - 涵盖大部分文件系统操作
 * 3. 异常安全 - 提供异常安全保证
 */

#include <iostream>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>

// 命名空间别名
namespace fs = std::filesystem;

// 1. 路径操作
void path_example() {
    std::cout << "\n[路径操作]" << std::endl;

    // 创建路径
    fs::path p1("/home/user/documents/file.txt");
    fs::path p2("relative/path/to/file.cpp");
    fs::path p3 = fs::current_path() / "test.txt";

    // 路径组件
    std::cout << "p1: " << p1 << std::endl;
    std::cout << "p1 root_name(): " << p1.root_name() << std::endl;
    std::cout << "p1 root_directory(): " << p1.root_directory() << std::endl;
    std::cout << "p1 root_path(): " << p1.root_path() << std::endl;
    std::cout << "p1 relative_path(): " << p1.relative_path() << std::endl;
    std::cout << "p1 parent_path(): " << p1.parent_path() << std::endl;
    std::cout << "p1 filename(): " << p1.filename() << std::endl;
    std::cout << "p1 stem(): " << p1.stem() << std::endl;
    std::cout << "p1 extension(): " << p1.extension() << std::endl;

    // 路径修改
    fs::path p4 = p1;
    p4.replace_extension(".cpp");
    std::cout << "p4 (replace_extension): " << p4 << std::endl;

    p4.replace_filename("new_file.txt");
    std::cout << "p4 (replace_filename): " << p4 << std::endl;

    // 路径连接
    fs::path base = "/home/user";
    fs::path relative = "documents/file.txt";
    fs::path full = base / relative;
    std::cout << "full path: " << full << std::endl;

    // 路径分解
    std::cout << "\nPath decomposition of " << p1 << ":" << std::endl;
    for (const auto& part : p1) {
        std::cout << "  " << part << std::endl;
    }
}

// 2. 文件属性查询
void file_status_example() {
    std::cout << "\n[文件属性查询]" << std::endl;

    // 创建测试文件
    fs::path test_file = "test_file.txt";
    std::ofstream(test_file) << "Hello, World!";

    // 查询文件状态
    fs::file_status status = fs::status(test_file);

    std::cout << "File: " << test_file << std::endl;
    std::cout << "Exists: " << fs::exists(status) << std::endl;
    std::cout << "Is regular file: " << fs::is_regular_file(status) << std::endl;
    std::cout << "Is directory: " << fs::is_directory(status) << std::endl;
    std::cout << "Is symlink: " << fs::is_symlink(status) << std::endl;

    // 文件大小
    if (fs::exists(test_file)) {
        std::cout << "File size: " << fs::file_size(test_file) << " bytes" << std::endl;
    }

    // 文件时间
    auto last_write = fs::last_write_time(test_file);
    auto sctp = std::chrono::time_point_cast<std::chrono::system_clock::duration>(
        last_write - fs::file_time_type::clock::now() + std::chrono::system_clock::now());
    std::time_t cftime = std::chrono::system_clock::to_time_t(sctp);
    std::cout << "Last write time: " << std::asctime(std::localtime(&cftime));

    // 清理
    fs::remove(test_file);
}

// 3. 目录操作
void directory_example() {
    std::cout << "\n[目录操作]" << std::endl;

    // 创建目录
    fs::path test_dir = "test_directory";
    fs::create_directory(test_dir);

    // 创建嵌套目录
    fs::path nested_dir = test_dir / "subdir1" / "subdir2";
    fs::create_directories(nested_dir);

    // 检查目录
    std::cout << "Directory exists: " << fs::exists(test_dir) << std::endl;
    std::cout << "Is directory: " << fs::is_directory(test_dir) << std::endl;

    // 创建测试文件
    for (int i = 0; i < 5; ++i) {
        fs::path file = test_dir / ("file" + std::to_string(i) + ".txt");
        std::ofstream(file) << "Content " << i;
    }

    // 遍历目录
    std::cout << "\nDirectory contents:" << std::endl;
    for (const auto& entry : fs::directory_iterator(test_dir)) {
        std::cout << "  " << entry.path().filename();
        if (entry.is_directory()) {
            std::cout << " [DIR]";
        }
        std::cout << std::endl;
    }

    // 递归遍历
    std::cout << "\nRecursive directory contents:" << std::endl;
    for (const auto& entry : fs::recursive_directory_iterator(test_dir)) {
        std::cout << "  " << entry.path() << std::endl;
    }

    // 清理
    fs::remove_all(test_dir);
}

// 4. 文件操作
void file_operations_example() {
    std::cout << "\n[文件操作]" << std::endl;

    // 创建文件
    fs::path file1 = "source.txt";
    fs::path file2 = "destination.txt";
    fs::path file3 = "renamed.txt";

    std::ofstream(file1) << "Hello, World!";

    // 拷贝文件
    fs::copy_file(file1, file2, fs::copy_options::overwrite_existing);
    std::cout << "Copied " << file1 << " to " << file2 << std::endl;

    // 重命名文件
    fs::rename(file2, file3);
    std::cout << "Renamed " << file2 << " to " << file3 << std::endl;

    // 删除文件
    fs::remove(file1);
    fs::remove(file3);
    std::cout << "Deleted files" << std::endl;

    // 创建临时目录
    fs::path temp_dir = fs::temp_directory_path() / "cpp17_test";
    fs::create_directories(temp_dir);
    std::cout << "Created temp directory: " << temp_dir << std::endl;

    // 清理
    fs::remove_all(temp_dir);
}

// 5. 文件内容操作
void file_content_example() {
    std::cout << "\n[文件内容操作]" << std::endl;

    fs::path test_file = "test_content.txt";

    // 写入文件
    {
        std::ofstream file(test_file);
        file << "Line 1" << std::endl;
        file << "Line 2" << std::endl;
        file << "Line 3" << std::endl;
    }

    // 读取文件
    {
        std::ifstream file(test_file);
        std::string line;
        std::cout << "File contents:" << std::endl;
        while (std::getline(file, line)) {
            std::cout << "  " << line << std::endl;
        }
    }

    // 文件大小
    std::cout << "File size: " << fs::file_size(test_file) << " bytes" << std::endl;

    // 清理
    fs::remove(test_file);
}

// 6. 符号链接
void symlink_example() {
    std::cout << "\n[符号链接]" << std::endl;

    // 创建测试文件
    fs::path target = "target.txt";
    fs::path link = "link.txt";

    std::ofstream(target) << "Target content";

    // 创建符号链接
    try {
        fs::create_symlink(target, link);
        std::cout << "Created symlink: " << link << " -> " << target << std::endl;

        // 检查是否为符号链接
        std::cout << "Is symlink: " << fs::is_symlink(link) << std::endl;

        // 读取符号链接目标
        std::cout << "Symlink target: " << fs::read_symlink(link) << std::endl;

        // 通过符号链接读取文件
        std::ifstream file(link);
        std::string content;
        std::getline(file, content);
        std::cout << "Content through symlink: " << content << std::endl;
    } catch (const fs::filesystem_error& e) {
        std::cout << "Error: " << e.what() << std::endl;
    }

    // 清理
    fs::remove(target);
    fs::remove(link);
}

// 7. 空间信息
void space_example() {
    std::cout << "\n[空间信息]" << std::endl;

    // 获取当前目录的空间信息
    fs::path current = fs::current_path();
    fs::space_info space = fs::space(current);

    std::cout << "Path: " << current << std::endl;
    std::cout << "Capacity: " << space.capacity / (1024 * 1024 * 1024) << " GB" << std::endl;
    std::cout << "Free: " << space.free / (1024 * 1024 * 1024) << " GB" << std::endl;
    std::cout << "Available: " << space.available / (1024 * 1024 * 1024) << " GB" << std::endl;
}

// 8. 路径规范化
void path_normalization_example() {
    std::cout << "\n[路径规范化]" << std::endl;

    // 规范化路径
    fs::path p1 = "/home/user/../user/./documents/./file.txt";
    std::cout << "Original: " << p1 << std::endl;
    std::cout << "Normalized: " << p1.lexically_normal() << std::endl;

    // 相对路径
    fs::path base = "/home/user/documents";
    fs::path target = "/home/user/documents/subdir/file.txt";
    fs::path relative = fs::relative(target, base);
    std::cout << "Relative: " << relative << std::endl;

    // 绝对路径
    fs::path relative_path = "relative/path/file.txt";
    fs::path absolute_path = fs::absolute(relative_path);
    std::cout << "Absolute: " << absolute_path << std::endl;

    // 规范化
    fs::path canonical_path = fs::canonical(".");
    std::cout << "Canonical: " << canonical_path << std::endl;
}

// 9. 文件系统操作
void filesystem_operations_example() {
    std::cout << "\n[文件系统操作]" << std::endl;

    // 创建测试目录
    fs::path test_dir = "fs_test";
    fs::create_directories(test_dir);

    // 创建测试文件
    for (int i = 0; i < 3; ++i) {
        fs::path file = test_dir / ("file" + std::to_string(i) + ".txt");
        std::ofstream(file) << "Content " << i;
    }

    // 拷贝目录
    fs::path copy_dir = "fs_test_copy";
    fs::copy(test_dir, copy_dir, fs::copy_options::recursive);
    std::cout << "Copied directory" << std::endl;

    // 验证拷贝
    std::cout << "Original files:" << std::endl;
    for (const auto& entry : fs::directory_iterator(test_dir)) {
        std::cout << "  " << entry.path().filename() << std::endl;
    }

    std::cout << "Copied files:" << std::endl;
    for (const auto& entry : fs::directory_iterator(copy_dir)) {
        std::cout << "  " << entry.path().filename() << std::endl;
    }

    // 清理
    fs::remove_all(test_dir);
    fs::remove_all(copy_dir);
}

// 10. 错误处理
void error_handling_example() {
    std::cout << "\n[错误处理]" << std::endl;

    // 方法1：使用异常
    try {
        [[maybe_unused]] auto size = fs::file_size("nonexistent_file.txt");
    } catch (const fs::filesystem_error& e) {
        std::cout << "Exception caught: " << e.what() << std::endl;
    }

    // 方法2：使用错误码
    std::error_code ec;
    auto size = fs::file_size("nonexistent_file.txt", ec);
    if (ec) {
        std::cout << "Error code: " << ec.message() << std::endl;
    } else {
        std::cout << "File size: " << size << std::endl;
    }

    // 方法3：检查存在性
    fs::path path = "nonexistent_file.txt";
    if (fs::exists(path)) {
        std::cout << "File exists" << std::endl;
    } else {
        std::cout << "File does not exist" << std::endl;
    }
}

// 11. 实际应用：文件查找
std::vector<fs::path> find_files(const fs::path& dir, const std::string& extension) {
    std::vector<fs::path> result;

    for (const auto& entry : fs::recursive_directory_iterator(dir)) {
        if (entry.is_regular_file() && entry.path().extension() == extension) {
            result.push_back(entry.path());
        }
    }

    return result;
}

void file_search_example() {
    std::cout << "\n[文件查找]" << std::endl;

    // 创建测试目录结构
    fs::path test_dir = "search_test";
    fs::create_directories(test_dir / "subdir1");
    fs::create_directories(test_dir / "subdir2");

    // 创建测试文件
    std::ofstream(test_dir / "file1.cpp") << "// C++ file";
    std::ofstream(test_dir / "file2.cpp") << "// C++ file";
    std::ofstream(test_dir / "file3.txt") << "// Text file";
    std::ofstream(test_dir / "subdir1" / "file4.cpp") << "// C++ file";
    std::ofstream(test_dir / "subdir2" / "file5.txt") << "// Text file";

    // 查找所有 .cpp 文件
    auto cpp_files = find_files(test_dir, ".cpp");
    std::cout << "Found " << cpp_files.size() << " .cpp files:" << std::endl;
    for (const auto& file : cpp_files) {
        std::cout << "  " << file << std::endl;
    }

    // 清理
    fs::remove_all(test_dir);
}

// 12. 实际应用：目录大小计算
uintmax_t directory_size(const fs::path& dir) {
    uintmax_t size = 0;

    for (const auto& entry : fs::recursive_directory_iterator(dir)) {
        if (entry.is_regular_file()) {
            size += entry.file_size();
        }
    }

    return size;
}

void directory_size_example() {
    std::cout << "\n[目录大小计算]" << std::endl;

    // 创建测试目录
    fs::path test_dir = "size_test";
    fs::create_directories(test_dir);

    // 创建测试文件
    std::ofstream(test_dir / "file1.txt") << "Hello, World!";
    std::ofstream(test_dir / "file2.txt") << "This is a test file with more content.";

    // 计算目录大小
    auto size = directory_size(test_dir);
    std::cout << "Directory size: " << size << " bytes" << std::endl;

    // 清理
    fs::remove_all(test_dir);
}

// 主示例函数
void filesystem_example() {
    std::cout << "=== std::filesystem ===" << std::endl;

    path_example();
    file_status_example();
    directory_example();
    file_operations_example();
    file_content_example();
    symlink_example();
    space_example();
    path_normalization_example();
    filesystem_operations_example();
    error_handling_example();
    file_search_example();
    directory_size_example();

    std::cout << std::endl;
}

#ifndef COMBINED_BUILD
int main() {
    filesystem_example();
    return 0;
}
#endif
