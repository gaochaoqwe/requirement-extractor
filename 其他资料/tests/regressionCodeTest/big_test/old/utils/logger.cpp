#include "logger.h"
#include <iostream>
#include <ctime>
#include <iomanip>

// Static member definitions
std::ofstream Logger::logFile;
LogLevel Logger::currentLevel = LOG_INFO;
bool Logger::initialized = false;

void Logger::init(const std::string& filename) {
    if (!initialized) {
        logFile.open(filename, std::ios::app);
        initialized = true;
        info("Logger initialized");
    }
}

void Logger::shutdown() {
    if (initialized) {
        info("Logger shutting down");
        logFile.close();
        initialized = false;
    }
}

void Logger::setLevel(LogLevel level) {
    currentLevel = level;
}

LogLevel Logger::getLevel() {
    return currentLevel;
}

void Logger::debug(const std::string& message) {
    log(LOG_DEBUG, message);
}

void Logger::info(const std::string& message) {
    log(LOG_INFO, message);
}

void Logger::warning(const std::string& message) {
    log(LOG_WARNING, message);
}

void Logger::error(const std::string& message) {
    log(LOG_ERROR, message);
}

void Logger::log(LogLevel level, const std::string& message) {
    if (level >= currentLevel) {
        std::string timestamp = getCurrentTime();
        std::string levelStr = levelToString(level);
        
        std::string logMessage = "[" + timestamp + "] [" + levelStr + "] " + message;
        
        // Write to console
        std::cout << logMessage << std::endl;
        
        // Write to file if initialized
        if (initialized && logFile.is_open()) {
            logFile << logMessage << std::endl;
            logFile.flush();
        }
    }
}

std::string Logger::levelToString(LogLevel level) {
    switch (level) {
        case LOG_DEBUG: return "DEBUG";
        case LOG_INFO: return "INFO";
        case LOG_WARNING: return "WARNING";
        case LOG_ERROR: return "ERROR";
        default: return "UNKNOWN";
    }
}

std::string Logger::getCurrentTime() {
    std::time_t now = std::time(nullptr);
    std::tm* timeinfo = std::localtime(&now);
    
    std::ostringstream oss;
    oss << std::put_time(timeinfo, "%Y-%m-%d %H:%M:%S");
    return oss.str();
} 