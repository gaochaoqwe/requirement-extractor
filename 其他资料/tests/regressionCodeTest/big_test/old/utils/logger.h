#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <fstream>

enum LogLevel {
    LOG_DEBUG = 0,
    LOG_INFO = 1,
    LOG_WARNING = 2,
    LOG_ERROR = 3
};

class Logger {
private:
    static std::ofstream logFile;
    static LogLevel currentLevel;
    static bool initialized;
    
public:
    static void init(const std::string& filename = "app.log");
    static void shutdown();
    
    static void setLevel(LogLevel level);
    static LogLevel getLevel();
    
    static void debug(const std::string& message);
    static void info(const std::string& message);
    static void warning(const std::string& message);
    static void error(const std::string& message);
    
private:
    static void log(LogLevel level, const std::string& message);
    static std::string levelToString(LogLevel level);
    static std::string getCurrentTime();
};

#endif // LOGGER_H 