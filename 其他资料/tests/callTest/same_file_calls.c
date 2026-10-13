// Functions defined and called within the same C file

int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

int operate(int x, int y) {
    int sum = add(x, y);      // call to function in the same file
    int diff = subtract(x, y);// call to function in the same file
    return sum * diff;
} 