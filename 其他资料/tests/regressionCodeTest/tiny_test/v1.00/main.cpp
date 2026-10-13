#include "calculator.h"
#include <iostream>

int main() {
    Calculator calc;
    
    std::cout << "Simple Calculator v1.00" << std::endl;
    std::cout << "------------------------" << std::endl;
    
    // Test basic operations
    double a = 10.0;
    double b = 5.0;
    
    std::cout << a << " + " << b << " = " << calc.add(a, b) << std::endl;
    std::cout << a << " - " << b << " = " << calc.subtract(a, b) << std::endl;
    std::cout << a << " * " << b << " = " << calc.multiply(a, b) << std::endl;
    
    try {
        std::cout << a << " / " << b << " = " << calc.divide(a, b) << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
    
    // Test memory function
    calc.setMemory(42.0);
    std::cout << "Memory value: " << calc.getMemory() << std::endl;
    
    return 0;
}
