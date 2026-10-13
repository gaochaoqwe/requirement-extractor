/*
 * 缺少注释测试文件
 * 目的：触发 rule_008 (缺少注释)
 */

int add(int a, int b) {
    return a + b;
}

int multiply(int x, int y) {
    return x * y;
}

void complex_function(int data) {
    int temp = data * 2;
    temp += 10;
    temp = temp / 3;
}
