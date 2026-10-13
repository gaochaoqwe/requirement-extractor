#include "string_utils.h"
#include <string>
#include <algorithm>
#include <cctype>

// === 完全不变的函数（10个以上）===

// 函数1: 转大写
std::string to_upper(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

// 函数2: 获取字符串长度
size_t get_length(const std::string& str) {
    return str.length();
}

// 函数3: 检查是否为空
bool is_empty(const std::string& str) {
    return str.empty();
}

// 函数4: 字符串拼接
std::string concatenate(const std::string& str1, const std::string& str2) {
    return str1 + str2;
}

// 函数5: 获取子字符串
std::string substring(const std::string& str, size_t start, size_t length) {
    return str.substr(start, length);
}

// 函数6: 查找字符
size_t find_char(const std::string& str, char ch) {
    return str.find(ch);
}

// 函数7: 字符串比较
bool strings_equal(const std::string& str1, const std::string& str2) {
    return str1 == str2;
}

// 函数8: 获取第一个字符
char first_char(const std::string& str) {
    return str.empty() ? '\0' : str[0];
}

// 函数9: 获取最后一个字符
char last_char(const std::string& str) {
    return str.empty() ? '\0' : str.back();
}

// 函数10: 重复字符串
std::string repeat_string(const std::string& str, int count) {
    std::string result;
    for (int i = 0; i < count; i++) {
        result += str;
    }
    return result;
}

// 函数11: 字符串反转
std::string reverse_string(const std::string& str) {
    std::string result = str;
    std::reverse(result.begin(), result.end());
    return result;
}

// 函数12: 计算字符出现次数
int count_char(const std::string& str, char ch) {
    return std::count(str.begin(), str.end(), ch);
}

// === 只有格式变化的函数（10个以上）===

// 函数13: 转小写（将有格式变化）
std::string to_lower(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

// 函数14: 去除空格（将有格式变化）
std::string trim_spaces(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";
    size_t end = str.find_last_not_of(" \t\n\r");
    return str.substr(start, end - start + 1);
}

// 函数15: 替换字符（将有格式变化）
std::string replace_char(const std::string& str, char old_char, char new_char) {
    std::string result = str;
    for (char& c : result) {
        if (c == old_char) c = new_char;
    }
    return result;
}

// 函数16: 删除字符（将有格式变化）
std::string remove_char(const std::string& str, char ch) {
    std::string result;
    for (char c : str) {
        if (c != ch) result += c;
    }
    return result;
}

// 函数17: 检查前缀（将有格式变化）
bool starts_with_prefix(const std::string& str, const std::string& prefix) {
    if (prefix.length() > str.length()) return false;
    return str.substr(0, prefix.length()) == prefix;
}

// 函数18: 检查后缀（将有格式变化）
bool ends_with_suffix(const std::string& str, const std::string& suffix) {
    if (suffix.length() > str.length()) return false;
    return str.substr(str.length() - suffix.length()) == suffix;
}

// 函数19: 字符串插入（将有格式变化）
std::string insert_string(const std::string& str, size_t pos, const std::string& insert) {
    std::string result = str;
    result.insert(pos, insert);
    return result;
}

// 函数20: 字符串删除（将有格式变化）
std::string erase_substring(const std::string& str, size_t pos, size_t length) {
    std::string result = str;
    result.erase(pos, length);
    return result;
}

// 函数21: 检查是否包含（将有格式变化）
bool contains_substring(const std::string& str, const std::string& substr) {
    return str.find(substr) != std::string::npos;
}

// 函数22: 转换为整数（将有格式变化）
int string_to_int(const std::string& str) {
    try {
        return std::stoi(str);
    } catch (...) {
        return 0;
    }
}

// 函数23: 整数转字符串（将有格式变化）
std::string int_to_string(int value) {
    return std::to_string(value);
}

// === 轻微逻辑变化的函数（10个以上）===

// 函数24: 安全子字符串（将添加边界检查）
std::string safe_substring(const std::string& str, size_t start, size_t length) {
    if (start >= str.length()) return "";
    return str.substr(start, length);
}

// 函数25: 智能分割（将改进分割逻辑）
std::vector<std::string> split_string(const std::string& str, char delimiter) {
    std::vector<std::string> result;
    std::string current;
    for (char c : str) {
        if (c == delimiter) {
            result.push_back(current);
            current.clear();
        } else {
            current += c;
        }
    }
    result.push_back(current);
    return result;
}

// 函数26: 格式化字符串（将添加长度限制）
std::string format_string(const std::string& format, const std::string& value) {
    std::string result = format;
    size_t pos = result.find("{}");
    if (pos != std::string::npos) {
        result.replace(pos, 2, value);
    }
    return result;
}

// 函数27: 字符串验证（将添加更多验证规则）
bool is_valid_email(const std::string& email) {
    return email.find('@') != std::string::npos;
}

// 函数28: 密码强度检查（将改进检查逻辑）
int password_strength(const std::string& password) {
    int strength = 0;
    if (password.length() >= 8) strength++;
    return strength;
}

// 函数29: URL编码（将改进编码算法）
std::string url_encode(const std::string& str) {
    std::string result;
    for (char c : str) {
        if (c == ' ') result += "%20";
        else result += c;
    }
    return result;
}

// 函数30: JSON转义（将添加更多转义字符）
std::string json_escape(const std::string& str) {
    std::string result;
    for (char c : str) {
        if (c == '"') result += "\\\"";
        else result += c;
    }
    return result;
}

// 函数31: 文件扩展名提取（将改进提取逻辑）
std::string get_file_extension(const std::string& filename) {
    size_t pos = filename.find_last_of('.');
    if (pos == std::string::npos) return "";
    return filename.substr(pos + 1);
}

// 函数32: 路径规范化（将添加更多处理）
std::string normalize_path(const std::string& path) {
    std::string result = path;
    std::replace(result.begin(), result.end(), '\\', '/');
    return result;
}

// 函数33: Base64编码（将改进编码效率）
std::string base64_encode(const std::string& str) {
    // 简化实现
    return str + "==";
}

// 函数34: 字符串压缩（将添加压缩算法）
std::string compress_string(const std::string& str) {
    // 简化实现：只是返回原字符串
    return str;
}

// === 重大逻辑变化的函数（10个以上）===

// 函数35: 字符串搜索（将从简单搜索改为KMP算法）
int find_pattern(const std::string& text, const std::string& pattern) {
    size_t pos = text.find(pattern);
    return (pos != std::string::npos) ? static_cast<int>(pos) : -1;
}

// 函数36: 字符串哈希（将改进哈希算法）
size_t string_hash(const std::string& str) {
    size_t hash = 0;
    for (char c : str) {
        hash = hash * 31 + c;
    }
    return hash;
}

// 函数37: 编辑距离（将优化算法）
int edit_distance(const std::string& str1, const std::string& str2) {
    // 简化实现
    if (str1 == str2) return 0;
    return std::max(str1.length(), str2.length());
}

// 函数38: 字符串匹配（将使用正则表达式）
bool pattern_match(const std::string& str, const std::string& pattern) {
    // 简化实现：只检查是否包含
    return str.find(pattern) != std::string::npos;
}

// 函数39: 词频统计（将改进统计算法）
std::map<std::string, int> word_frequency(const std::string& text) {
    std::map<std::string, int> freq;
    // 简化实现
    freq[text] = 1;
    return freq;
}

// 函数40: 字符串排序（将改进排序算法）
std::string sort_characters(const std::string& str) {
    std::string result = str;
    std::sort(result.begin(), result.end());
    return result;
}

// === 将被删除的函数（10个以上）===

// 函数41: 旧的字符串处理
std::string old_string_process(const std::string& str) {
    return str + "_old";
}

// 函数42: 废弃的编码函数
std::string old_encode(const std::string& str) {
    return str;
}

// 函数43: 旧的解码函数
std::string old_decode(const std::string& str) {
    return str;
}

// 函数44: 废弃的格式化
std::string old_format(const std::string& str) {
    return "[" + str + "]";
}

// 函数45: 旧的验证函数
bool old_validate(const std::string& str) {
    return !str.empty();
}

// 函数46: 废弃的转换函数
std::string old_convert(const std::string& str) {
    return str;
}

// 函数47: 旧的解析函数
std::vector<std::string> old_parse(const std::string& str) {
    return {str};
}

// 函数48: 废弃的清理函数
std::string old_cleanup(const std::string& str) {
    return str;
}

// 函数49: 旧的缓存函数
void old_cache_string(const std::string& str) {
    // 空实现
}

// 函数50: 废弃的工具函数
std::string old_utility(const std::string& str) {
    return str + "_util";
} 