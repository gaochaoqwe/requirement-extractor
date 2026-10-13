#include "calculator.h"
#include <iostream>

void displayMenu() {
    std::cout << "\nCalculator v1.01 - Enhanced Edition" << std::endl;
    std::cout << "--------------------------------" << std::endl;
    std::cout << "1. Add" << std::endl;
    std::cout << "2. Subtract" << std::endl;
    std::cout << "3. Multiply" << std::endl;
    std::cout << "4. Divide" << std::endl;
    std::cout << "5. Power" << std::endl;
    std::cout << "6. Set Memory" << std::endl;
    std::cout << "7. Get Memory" << std::endl;
    std::cout << "8. Clear Memory" << std::endl;
    std::cout << "9. Show History" << std::endl;
    std::cout << "0. Exit" << std::endl;
    std::cout << "--------------------------------" << std::endl;
    std::cout << "Enter your choice: ";
}

double getNumber(const std::string& prompt) {
    double num;
    std::cout << prompt;
    while (!(std::cin >> num)) {
        std::cin.clear();
        std::cin.ignore(1000, '\n');
        std::cout << "Invalid input. Please enter a number: ";
    }
    return num;
}

int main() {
    Calculator calc;
    int choice = 0;
    
    do {
        displayMenu();
        std::cin >> choice;
        
        if (std::cin.fail()) {
            std::cin.clear();
            std::cin.ignore(1000, '\n');
            choice = -1;
        }
        
        switch (choice) {
            case 1: {
                double a = getNumber("Enter first number: ");
                double b = getNumber("Enter second number: ");
                std::cout << a << " + " << b << " = " << calc.add(a, b) << std::endl;
                break;
            }
            case 2: {
                double a = getNumber("Enter first number: ");
                double b = getNumber("Enter second number: ");
                std::cout << a << " - " << b << " = " << calc.subtract(a, b) << std::endl;
                break;
            }
            case 3: {
                double a = getNumber("Enter first number: ");
                double b = getNumber("Enter second number: ");
                std::cout << a << " * " << b << " = " << calc.multiply(a, b) << std::endl;
                break;
            }
            case 4: {
                double a = getNumber("Enter numerator: ");
                double b = getNumber("Enter denominator: ");
                try {
                    std::cout << a << " / " << b << " = " << calc.divide(a, b) << std::endl;
                } catch (const std::exception& e) {
                    std::cerr << "Error: " << e.what() << std::endl;
                }
                break;
            }
            case 5: {
                double base = getNumber("Enter base: ");
                double exponent = getNumber("Enter exponent: ");
                std::cout << base << " ^ " << exponent << " = " << calc.power(base, exponent) << std::endl;
                break;
            }
            case 6: {
                double value = getNumber("Enter value to store in memory: ");
                calc.setMemory(value);
                std::cout << "Memory set to " << value << std::endl;
                break;
            }
            case 7:
                std::cout << "Current memory value: " << calc.getMemory() << std::endl;
                break;
            case 8:
                calc.clearMemory();
                std::cout << "Memory cleared" << std::endl;
                break;
            case 9:
                calc.printHistory();
                break;
            case 0:
                std::cout << "Thank you for using Calculator v1.01!" << std::endl;
                break;
            default:
                std::cout << "Invalid choice. Please try again." << std::endl;
        }
        
        std::cin.ignore(1000, '\n');
        
    } while (choice != 0);
    
    return 0;
}
