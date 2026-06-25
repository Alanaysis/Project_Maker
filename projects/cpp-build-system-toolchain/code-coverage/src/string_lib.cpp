#include "string_lib.h"
#include <algorithm>
#include <sstream>
#include <cctype>

namespace str {

std::string reverse(const std::string& input) {
    std::string result = input;
    std::reverse(result.begin(), result.end());
    return result;
}

std::string to_upper(const std::string& input) {
    std::string result = input;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

std::string to_lower(const std::string& input) {
    std::string result = input;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

std::vector<std::string> split(const std::string& input, char delimiter) {
    std::vector<std::string> result;
    std::istringstream stream(input);
    std::string token;
    while (std::getline(stream, token, delimiter)) {
        result.push_back(token);
    }
    return result;
}

bool is_palindrome(const std::string& input) {
    std::string cleaned;
    for (char c : input) {
        if (std::isalnum(c)) {
            cleaned += std::tolower(c);
        }
    }
    std::string reversed = cleaned;
    std::reverse(reversed.begin(), reversed.end());
    return cleaned == reversed;
}

int count_words(const std::string& input) {
    if (input.empty()) return 0;
    std::istringstream stream(input);
    std::string word;
    int count = 0;
    while (stream >> word) {
        count++;
    }
    return count;
}

}  // namespace str
