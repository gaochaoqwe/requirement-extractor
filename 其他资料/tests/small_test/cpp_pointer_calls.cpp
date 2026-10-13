#include <iostream>
#include <memory>

class Database {
public:
    void connect() {
        std::cout << "Connecting to database..." << std::endl;
    }
    
    void query(const std::string& sql) {
        std::cout << "Executing query: " << sql << std::endl;
    }
    
    void disconnect() {
        std::cout << "Disconnecting from database..." << std::endl;
    }
};

class DatabaseManager {
private:
    std::unique_ptr<Database> db;
    
public:
    DatabaseManager() : db(std::make_unique<Database>()) {}
    
    void perform_database_operations() {
        db->connect();                    // 通过指针调用connect方法
        db->query("SELECT * FROM users"); // 通过指针调用query方法
        db->disconnect();                 // 通过指针调用disconnect方法
    }
};

class Data {
public:
    int value;
    Data(int v) : value(v) {}
};

void process_data(Data* data) {
    // Bug 1: 未检查空指针就解引用
    std::cout << "Processing value: " << data->value << std::endl;
}

void calculate_sum(int* arr, int size) {
    // Bug 2: 未初始化变量
    int sum;
    for (int i = 0; i < size; i++) {
        sum += arr[i];
    }
    std::cout << "Sum: " << sum << std::endl;
}

int main() {
    // Bug 3: 未初始化指针
    Data* ptr;
    process_data(ptr);

    // Bug 4: 内存泄漏 - 分配后未释放
    int* numbers = new int[5];
    for (int i = 0; i < 5; i++) {
        numbers[i] = i + 1;
    }
    calculate_sum(numbers, 5);
    
    return 0;
} 