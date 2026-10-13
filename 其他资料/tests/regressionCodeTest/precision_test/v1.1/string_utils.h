#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <string>

// 保持不变的函数
std::string to_upper(const std::string& str);

// 修改的函数
std::string to_lower(const std::string& str);

// 新增的函数
std::string trim(const std::string& str);
bool starts_with(const std::string& str, const std::string& prefix);

// 注意：reverse_string函数被删除了

#endif // STRING_UTILS_H 