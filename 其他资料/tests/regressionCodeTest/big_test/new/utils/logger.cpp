#include "logger.h"
#include <iostream>
#include <ctime>
#include <iomanip>
#include <sstream>

// Static member definitions
std::ofstream Logger::logFile;
LogLevel Logger::currentLevel = LOG_INFO;
bool Logger::initialized = false;
std::vector<LogEntry> Logger::logHistory;
size_t Logger::maxHistorySize = 1000;  // Default max history size

void Logger::init(const std::string& filename) {
    if (!initialized) {
        logFile.open(filename, std::ios::app);
        initialized = true;
        logHistory.clear();
        info("Logger initialized with enhanced features");
    }
}

void Logger::shutdown() {
    if (initialized) {
        info("Logger shutting down");
        logFile.close();
        initialized = false;
        // Don't clear history on shutdown, allow retrieval
    }
}

void Logger::setLevel(LogLevel level) {
    currentLevel = level;
    info("Log level changed to: " + levelToString(level));
}

LogLevel Logger::getLevel() {
    return currentLevel;
}

void Logger::setMaxHistorySize(size_t size) {
    maxHistorySize = size;
    
    // Trim history if it exceeds new size
    if (logHistory.size() > maxHistorySize) {
        logHistory.erase(logHistory.begin(), 
                        logHistory.begin() + (logHistory.size() - maxHistorySize));
    }
}

size_t Logger::getMaxHistorySize() {
    return maxHistorySize;
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

void Logger::critical(const std::string& message) {
    log(LOG_CRITICAL, message);
}

std::vector<LogEntry> Logger::getLogHistory() {
    return logHistory;
}

void Logger::clearHistory() {
    logHistory.clear();
    info("Log history cleared");
}

void Logger::exportHistory(const std::string& filename) {
    std::ofstream exportFile(filename);
    if (exportFile.is_open()) {
        exportFile << "=== Log History Export ===" << std::endl;
        exportFile << "Total entries: " << logHistory.size() << std::endl;
        exportFile << "============================" << std::endl;
        
        for (const auto& entry : logHistory) {
            exportFile << "[" << entry.timestamp << "] [" 
                      << levelToString(entry.level) << "] " 
                      << entry.message << std::endl;
        }
        
        exportFile.close();
        info("Log history exported to: " + filename);
    } else {
        error("Failed to export log history to: " + filename);
    }
}

void Logger::log(LogLevel level, const std::string& message) {
    if (level >= currentLevel) {
        std::string timestamp = getCurrentTime();
        std::string levelStr = levelToString(level);
        
        std::string logMessage = "[" + timestamp + "] [" + levelStr + "] " + message;
        
        // Write to console
        if (level >= LOG_ERROR) {
            std::cerr << logMessage << std::endl;  // Errors to stderr
        } else {
            std::cout << logMessage << std::endl;
        }
        
        // Write to file if initialized
        if (initialized && logFile.is_open()) {
            logFile << logMessage << std::endl;
            logFile.flush();
        }
        
        // Add to history
        addToHistory(level, message, timestamp);
    }
}

std::string Logger::levelToString(LogLevel level) {
    switch (level) {
        case LOG_DEBUG: return "DEBUG";
        case LOG_INFO: return "INFO";
        case LOG_WARNING: return "WARNING";
        case LOG_ERROR: return "ERROR";
        case LOG_CRITICAL: return "CRITICAL";
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

void Logger::addToHistory(LogLevel level, const std::string& message, const std::string& timestamp) {
    LogEntry entry;
    entry.level = level;
    entry.message = message;
    entry.timestamp = timestamp;
    
    logHistory.push_back(entry);
    
    // Maintain maximum history size
    if (logHistory.size() > maxHistorySize) {
        logHistory.erase(logHistory.begin());
    }
} 