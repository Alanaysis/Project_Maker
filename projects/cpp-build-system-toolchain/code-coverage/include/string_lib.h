#ifndef STRING_LIB_H
#define STRING_LIB_H

#include <string>
#include <vector>

namespace str {
    std::string reverse(const std::string& input);
    std::string to_upper(const std::string& input);
    std::string to_lower(const std::string& input);
    std::vector<std::string> split(const std::string& input, char delimiter);
    bool is_palindrome(const std::string& input);
    int count_words(const std::string& input);
}

#endif
