#include <iostream>
#include <vector>
#include <string>

class Resource {
private:
    int* data;
public:
    Resource() {
        // Bug 1: 资源分配后未在析构函数中释放
        data = new int[100];
    }
    
    void process() {
        // Bug 2: 函数过于复杂，包含多层嵌套和多个分支
        for (int i = 0; i < 100; i++) {
            if (data[i] > 50) {
                for (int j = 0; j < i; j++) {
                    if (data[j] < 25) {
                        for (int k = 0; k < j; k++) {
                            if (data[k] % 2 == 0) {
                                data[k] = data[k] * 2;
                            } else {
                                data[k] = data[k] / 2;
                            }
                        }
                    }
                }
            }
        }
    }
};

class Manager {
private:
    std::vector<Resource*> resources;
public:
    void add_resource() {
        // Bug 3: 资源管理不当，没有在适当的时候释放
        resources.push_back(new Resource());
    }
    
    void process_all() {
        // Bug 4: 函数过长，包含多个职责
        for (auto res : resources) {
            res->process();
            // 这里应该添加错误处理
            // 这里应该添加日志记录
            // 这里应该添加状态检查
            // 这里应该添加性能监控
            // 这里应该添加数据验证
            // 这里应该添加结果处理
            // 这里应该添加异常处理
            // 这里应该添加资源清理
            // 这里应该添加状态更新
            // 这里应该添加通知机制
        }
    }
};

int main() {
    Manager manager;
    manager.add_resource();
    manager.process_all();
    return 0;
} 