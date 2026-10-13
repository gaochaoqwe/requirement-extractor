#include "config.h"
#include <fstream>
#include <sstream>
#include <algorithm>

// Static member definitions
std::map<std::string, std::string> Config::settings;
bool Config::loaded = false;

bool Config::load(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        return false;
    }
    
    settings.clear();
    std::string line;
    
    while (std::getline(file, line)) {
        line = trim(line);
        
        // Skip empty lines and comments
        if (line.empty() || line[0] == '#' || line[0] == ';') {
            continue;
        }
        
        // Find the '=' separator
        size_t pos = line.find('=');
        if (pos != std::string::npos) {
            std::string key = trim(line.substr(0, pos));
            std::string value = trim(line.substr(pos + 1));
            
            // Remove quotes if present
            if (value.size() >= 2 && value[0] == '"' && value.back() == '"') {
                value = value.substr(1, value.size() - 2);
            }
            
            settings[key] = value;
        }
    }
    
    file.close();
    loaded = true;
    return true;
}

bool Config::save(const std::string& filename) {
    std::ofstream file(filename);
    if (!file.is_open()) {
        return false;
    }
    
    file << "# Configuration file" << std::endl;
    file << "# Generated automatically" << std::endl;
    file << std::endl;
    
    for (const auto& pair : settings) {
        file << pair.first << "=" << pair.second << std::endl;
    }
    
    file.close();
    return true;
}

void Config::set(const std::string& key, const std::string& value) {
    settings[key] = value;
}

std::string Config::get(const std::string& key, const std::string& defaultValue) {
    auto it = settings.find(key);
    return (it != settings.end()) ? it->second : defaultValue;
}

bool Config::getBool(const std::string& key, bool defaultValue) {
    auto it = settings.find(key);
    if (it != settings.end()) {
        return parseBool(it->second);
    }
    return defaultValue;
}

int Config::getInt(const std::string& key, int defaultValue) {
    auto it = settings.find(key);
    if (it != settings.end()) {
        try {
            return std::stoi(it->second);
        } catch (...) {
            return defaultValue;
        }
    }
    return defaultValue;
}

double Config::getDouble(const std::string& key, double defaultValue) {
    auto it = settings.find(key);
    if (it != settings.end()) {
        try {
            return std::stod(it->second);
        } catch (...) {
            return defaultValue;
        }
    }
    return defaultValue;
}

void Config::setBool(const std::string& key, bool value) {
    settings[key] = value ? "true" : "false";
}

void Config::setInt(const std::string& key, int value) {
    settings[key] = std::to_string(value);
}

void Config::setDouble(const std::string& key, double value) {
    settings[key] = std::to_string(value);
}

bool Config::hasKey(const std::string& key) {
    return settings.find(key) != settings.end();
}

void Config::remove(const std::string& key) {
    settings.erase(key);
}

void Config::clear() {
    settings.clear();
    loaded = false;
}

std::map<std::string, std::string> Config::getAllSettings() {
    return settings;
}

std::string Config::trim(const std::string& str) {
    size_t start = str.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return "";
    }
    
    size_t end = str.find_last_not_of(" \t\r\n");
    return str.substr(start, end - start + 1);
}

bool Config::parseBool(const std::string& str) {
    std::string lower = str;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    
    return (lower == "true" || lower == "1" || lower == "yes" || lower == "on");
} 