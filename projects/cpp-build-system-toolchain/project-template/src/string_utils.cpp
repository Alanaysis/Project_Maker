#include "mylib/core.h"
#include <algorithm>
#include <sstream>

namespace mylib {

std::string StringUtils::to_upper(const std::string& input) {
    std::string result = input;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

std::string StringUtils::to_lower(const std::string& input) {
    std::string result = input;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

std::string StringUtils::trim(const std::string& input) {
    auto start = input.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    auto end = input.find_last_not_of(" \t\n\r");
    return input.substr(start, end - start + 1);
}

std::vector<std::string> StringUtils::split(const std::string& input, char delimiter) {
    std::vector<std::string> result;
    std::istringstream stream(input);
    std::string token;
    while (std::getline(stream, token, delimiter)) {
        result.push_back(token);
    }
    return result;
}

std::string StringUtils::join(const std::vector<std::string>& parts, const std::string& separator) {
    if (parts.empty()) return "";
    std::string result = parts[0];
    for (size_t i = 1; i < parts.size(); ++i) {
        result += separator + parts[i];
    }
    return result;
}

}  // namespace mylib
