#ifndef CALCULATOR_H
#define CALCULATOR_H

class Calculator {
public:
    // Basic arithmetic operations
    double add(double a, double b);
    double subtract(double a, double b);
    double multiply(double a, double b);
    double divide(double a, double b);
    
    // Simple memory function
    void setMemory(double value);
    double getMemory() const;
    
private:
    double memory = 0.0;
};

#endif // CALCULATOR_H
