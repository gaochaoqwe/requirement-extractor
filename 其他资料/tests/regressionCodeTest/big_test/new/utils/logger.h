#ifndef LOGGER_H
#define LOGGER_H

#include <string>
#include <fstream>
#include <vector>

enum LogLevel {
    LOG_DEBUG = 0,
    LOG_INFO = 1,
    LOG_WARNING = 2,
    LOG_ERROR = 3,
    LOG_CRITICAL = 4  // New log level
};

struct LogEntry {  // New struct
    LogLevel level;
    std::string message;
    std::string timestamp;
};

class Logger {
private:
    static std::ofstream logFile;
    static LogLevel currentLevel;
    static bool initialized;
    static std::vector<LogEntry> logHistory;  // New field
    static size_t maxHistorySize;             // New field
    
public:
    static void init(const std::string& filename = "app.log");
    static void shutdown();
    
    static void setLevel(LogLevel level);
    static LogLevel getLevel();
    
    static void setMaxHistorySize(size_t size);  // New method
    static size_t getMaxHistorySize();           // New method
    
    static void debug(const std::string& message);
    static void info(const std::string& message);
    static void warning(const std::string& message);
    static void error(const std::string& message);
    static void critical(const std::string& message);  // New method
    
    // New methods for log history
    static std::vector<LogEntry> getLogHistory();
    static void clearHistory();
    static void exportHistory(const std::string& filename);
    
private:
    static void log(LogLevel level, const std::string& message);
    static std::string levelToString(LogLevel level);
    static std::string getCurrentTime();
    static void addToHistory(LogLevel level, const std::string& message, const std::string& timestamp);  // New method
};

#endif // LOGGER_H 