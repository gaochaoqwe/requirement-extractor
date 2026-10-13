#ifndef STRING_UTILS_H
#define STRING_UTILS_H

#include <string>
#include <vector>
#include <map>

// === 完全不变的函数（12个）===
std::string to_upper(const std::string& str);
size_t get_length(const std::string& str);
bool is_empty(const std::string& str);
std::string concatenate(const std::string& str1, const std::string& str2);
std::string substring(const std::string& str, size_t start, size_t length);
size_t find_char(const std::string& str, char ch);
bool strings_equal(const std::string& str1, const std::string& str2);
char first_char(const std::string& str);
char last_char(const std::string& str);
std::string repeat_string(const std::string& str, int count);
std::string reverse_string(const std::string& str);
int count_char(const std::string& str, char ch);

// === 只有格式变化的函数（11个）===
std::string to_lower(const std::string& str);
std::string trim_spaces(const std::string& str);
std::string replace_char(const std::string& str, char old_char, char new_char);
std::string remove_char(const std::string& str, char ch);
bool starts_with_prefix(const std::string& str, const std::string& prefix);
bool ends_with_suffix(const std::string& str, const std::string& suffix);
std::string insert_string(const std::string& str, size_t pos, const std::string& insert);
std::string erase_substring(const std::string& str, size_t pos, size_t length);
bool contains_substring(const std::string& str, const std::string& substr);
int string_to_int(const std::string& str);
std::string int_to_string(int value);

// === 轻微逻辑变化的函数（11个）===
std::string safe_substring(const std::string& str, size_t start, size_t length);
std::vector<std::string> split_string(const std::string& str, char delimiter);
std::string format_string(const std::string& format, const std::string& value);
bool is_valid_email(const std::string& email);
int password_strength(const std::string& password);
std::string url_encode(const std::string& str);
std::string json_escape(const std::string& str);
std::string get_file_extension(const std::string& filename);
std::string normalize_path(const std::string& path);
std::string base64_encode(const std::string& str);
std::string compress_string(const std::string& str);

// === 重大逻辑变化的函数（6个）===
int find_pattern(const std::string& text, const std::string& pattern);
size_t string_hash(const std::string& str);
int edit_distance(const std::string& str1, const std::string& str2);
bool pattern_match(const std::string& str, const std::string& pattern);
std::map<std::string, int> word_frequency(const std::string& text);
std::string sort_characters(const std::string& str);

// === 将被删除的函数（10个）===
std::string old_string_process(const std::string& str);
std::string old_encode(const std::string& str);
std::string old_decode(const std::string& str);
std::string old_format(const std::string& str);
bool old_validate(const std::string& str);
std::string old_convert(const std::string& str);
std::vector<std::string> old_parse(const std::string& str);
std::string old_cleanup(const std::string& str);
void old_cache_string(const std::string& str);
std::string old_utility(const std::string& str);

#endif // STRING_UTILS_H 