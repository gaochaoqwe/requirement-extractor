#include "string_utils.h"
#include <string>
#include <algorithm>
#include <cctype>

// === 完全不变的函数（保持原样）===

// 函数1: 转大写 - 完全相同
std::string to_upper(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

// === 轻微逻辑变化的函数 ===

// 函数13: 转小写 - 添加了空字符串检查
std::string to_lower(const std::string& str) {
    std::string result = str;
    // 添加了空字符串检查
    if (str.empty()) return result;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

// === 新增的函数 ===

// 新增函数: 去除首尾空格
std::string trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

// 新增函数: 检查是否以指定字符串开头
bool starts_with(const std::string& str, const std::string& prefix) {
    if (prefix.length() > str.length()) return false;
    return str.substr(0, prefix.length()) == prefix;
}

// 注意：reverse_string函数被删除了，不再包含在v1.1中 