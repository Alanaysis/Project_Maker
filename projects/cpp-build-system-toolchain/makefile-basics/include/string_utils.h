#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <string>
#include <vector>

/**
 * @file string_utils.h
 * @brief 字符串工具库头文件
 *
 * 提供常用的字符串处理函数，用于演示 CMake 动态库的创建和使用。
 */

namespace str {

/**
 * @brief 转换为大写
 * @param input 输入字符串
 * @return 大写字符串
 */
std::string to_upper(const std::string& input);

/**
 * @brief 转换为小写
 * @param input 输入字符串
 * @return 小写字符串
 */
std::string to_lower(const std::string& input);

/**
 * @brief 去除首尾空白字符
 * @param input 输入字符串
 * @return 去除空白后的字符串
 */
std::string trim(const std::string& input);

/**
 * @brief 按分隔符分割字符串
 * @param input 输入字符串
 * @param delimiter 分隔符
 * @return 分割后的字符串向量
 */
std::vector<std::string> split(const std::string& input, char delimiter);

/**
 * @brief 连接字符串
 * @param parts 字符串向量
 * @param separator 分隔符
 * @return 连接后的字符串
 */
std::string join(const std::vector<std::string>& parts, const std::string& separator);

/**
 * @brief 判断字符串是否以指定前缀开头
 * @param str 输入字符串
 * @param prefix 前缀
 * @return 如果以指定前缀开头返回 true
 */
bool starts_with(const std::string& str, const std::string& prefix);

/**
 * @brief 判断字符串是否以指定后缀结尾
 * @param str 输入字符串
 * @param suffix 后缀
 * @return 如果以指定后缀结尾返回 true
 */
bool ends_with(const std::string& str, const std::string& suffix);

}  // namespace str

#endif  // STRING_UTILS_H
