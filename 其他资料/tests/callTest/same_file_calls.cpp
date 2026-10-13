// Functions defined and called within the same C++ file

int multiply(int a, int b) {
    return a * b;
}

int divide(int a, int b) {
    return b != 0 ? a / b : 0;
}

int compute(int x, int y) {
    int m = multiply(x, y);  // call inside same file
    int d = divide(x, y);    // call inside same file
    return m - d;
} 