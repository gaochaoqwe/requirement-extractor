#ifndef CONFIG_H
#define CONFIG_H

#include <string>
#include <map>

class Config {
private:
    static std::map<std::string, std::string> settings;
    static bool loaded;
    
public:
    static bool load(const std::string& filename);
    static bool save(const std::string& filename);
    
    static void set(const std::string& key, const std::string& value);
    static std::string get(const std::string& key, const std::string& defaultValue = "");
    
    static bool getBool(const std::string& key, bool defaultValue = false);
    static int getInt(const std::string& key, int defaultValue = 0);
    static double getDouble(const std::string& key, double defaultValue = 0.0);
    
    static void setBool(const std::string& key, bool value);
    static void setInt(const std::string& key, int value);
    static void setDouble(const std::string& key, double value);
    
    static bool hasKey(const std::string& key);
    static void remove(const std::string& key);
    static void clear();
    
    static std::map<std::string, std::string> getAllSettings();
    
private:
    static std::string trim(const std::string& str);
    static bool parseBool(const std::string& str);
};

#endif // CONFIG_H 