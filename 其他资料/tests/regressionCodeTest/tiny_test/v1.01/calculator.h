#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <vector>
#include <string>

class Calculator {
public:
    // Basic arithmetic operations
    double add(double a, double b);
    double subtract(double a, double b);
    double multiply(double a, double b);
    double divide(double a, double b);
    
    // New in v1.01: Power function
    double power(double base, double exponent);
    
    // Enhanced memory functions
    void setMemory(double value);
    double getMemory() const;
    void clearMemory();  // New in v1.01
    
    // New in v1.01: History tracking
    void addToHistory(const std::string& operation, double result);
    void clearHistory();
    void printHistory() const;
    
private:
    double memory = 0.0;
    // New in v1.01: Operation history
    struct HistoryEntry {
        std::string operation;
        double result;
    };
    std::vector<HistoryEntry> history;
};

#endif // CALCULATOR_H
