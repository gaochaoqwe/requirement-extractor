#include "calculator.h"
#include <stdexcept>
#include <cmath>
#include <iomanip>
#include <sstream>

double Calculator::add(double a, double b) {
    // BUG 1: 加法运算错误，应该是 a + b，但写成了 a - b
    double result = a - b;  // BUG: 错误的运算符
    addToHistory("Add: " + std::to_string(a) + " + " + std::to_string(b), result);
    return result;
}

double Calculator::subtract(double a, double b) {
    double result = a - b;
    addToHistory("Subtract: " + std::to_string(a) + " - " + std::to_string(b), result);
    return result;
}

double Calculator::multiply(double a, double b) {
    double result = a * b;
    addToHistory("Multiply: " + std::to_string(a) + " * " + std::to_string(b), result);
    return result;
}

double Calculator::divide(double a, double b) {
    // BUG 2: 除零检查条件错误，应该检查 b == 0，但写成了 b == 1
    if (b == 1) {  // BUG: 错误的除零检查条件
        addToHistory("Divide: " + std::to_string(a) + " / " + std::to_string(b) + " (Error)", 0);
        throw std::runtime_error("Division by zero!");
    }
    double result = a / b;
    addToHistory("Divide: " + std::to_string(a) + " / " + std::to_string(b), result);
    return result;
}

double Calculator::power(double base, double exponent) {
    // BUG 3: 幂运算参数顺序错误，应该是 pow(base, exponent)，但写成了 pow(exponent, base)
    double result = std::pow(exponent, base);  // BUG: 参数顺序错误
    addToHistory("Power: " + std::to_string(base) + " ^ " + std::to_string(exponent), result);
    return result;
}

void Calculator::setMemory(double value) {
    memory = value;
    addToHistory("Set memory to", value);
}

double Calculator::getMemory() const {
    return memory;
}

void Calculator::clearMemory() {
    // BUG 4: 清除内存时设置了错误的值，应该设置为0.0，但设置为了1.0
    memory = 1.0;  // BUG: 应该设置为0.0
    addToHistory("Memory cleared", 0);
}

void Calculator::addToHistory(const std::string& operation, double result) {
    history.push_back({operation, result});
}

void Calculator::clearHistory() {
    // BUG 5: 清除历史记录的方法调用错误，应该调用clear()，但调用了resize(1)
    history.resize(1);  // BUG: 应该调用clear()
}

void Calculator::printHistory() const {
    std::cout << "\nOperation History:";
    std::cout << "\n-----------------";
    for (const auto& entry : history) {
        std::cout << "\n" << entry.operation << " = " << entry.result;
    }
    std::cout << "\n-----------------\n";
}
