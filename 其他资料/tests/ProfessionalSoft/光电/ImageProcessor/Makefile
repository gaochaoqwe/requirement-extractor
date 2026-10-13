# 图像处理软件 Makefile

# 编译器和编译选项
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -g -O2 -pthread
LDFLAGS = -pthread -lm

# 目录定义
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build
BIN_DIR = bin

# 可执行文件名
TARGET = image_processor

# 源文件查找
CORE_SOURCES = $(wildcard $(SRC_DIR)/core/*.c)
ACQUISITION_SOURCES = $(wildcard $(SRC_DIR)/acquisition/*.c)
PROCESSING_SOURCES = $(wildcard $(SRC_DIR)/processing/*/*.c)
DISPLAY_SOURCES = $(wildcard $(SRC_DIR)/display/*.c)
UTILS_SOURCES = $(wildcard $(SRC_DIR)/utils/*.c)
CONFIG_SOURCES = $(wildcard $(SRC_DIR)/config/*.c)
MAIN_SOURCE = $(SRC_DIR)/main.c

# 所有源文件
SOURCES = $(MAIN_SOURCE) $(CORE_SOURCES) $(ACQUISITION_SOURCES) \
          $(PROCESSING_SOURCES) $(DISPLAY_SOURCES) $(UTILS_SOURCES) \
          $(CONFIG_SOURCES)

# 目标文件
OBJECTS = $(SOURCES:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)

# 头文件搜索路径
INCLUDES = -I$(INC_DIR)

# 默认目标
all: directories $(BIN_DIR)/$(TARGET)

# 创建必要的目录
directories:
	@mkdir -p $(BUILD_DIR)/core
	@mkdir -p $(BUILD_DIR)/acquisition
	@mkdir -p $(BUILD_DIR)/processing/filters
	@mkdir -p $(BUILD_DIR)/processing/algorithms
	@mkdir -p $(BUILD_DIR)/processing/enhancement
	@mkdir -p $(BUILD_DIR)/display
	@mkdir -p $(BUILD_DIR)/utils
	@mkdir -p $(BUILD_DIR)/config
	@mkdir -p $(BIN_DIR)

# 链接生成可执行文件
$(BIN_DIR)/$(TARGET): $(OBJECTS)
	@echo "Linking $@"
	@$(CC) $(OBJECTS) -o $@ $(LDFLAGS)
	@echo "Build completed: $@"

# 编译源文件为目标文件
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	@echo "Compiling $<"
	@$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# 清理构建文件
clean:
	@echo "Cleaning build files"
	@rm -rf $(BUILD_DIR)
	@rm -rf $(BIN_DIR)

# 安装
install: $(BIN_DIR)/$(TARGET)
	@echo "Installing $(TARGET)"
	@cp $(BIN_DIR)/$(TARGET) /usr/local/bin/
	@chmod +x /usr/local/bin/$(TARGET)

# 卸载
uninstall:
	@echo "Uninstalling $(TARGET)"
	@rm -f /usr/local/bin/$(TARGET)

# 运行程序
run: $(BIN_DIR)/$(TARGET)
	@echo "Running $(TARGET)"
	@cd $(BIN_DIR) && ./$(TARGET)

# 调试运行
debug: $(BIN_DIR)/$(TARGET)
	@echo "Running $(TARGET) with gdb"
	@cd $(BIN_DIR) && gdb ./$(TARGET)

# 代码统计
stats:
	@echo "Code statistics:"
	@echo "Lines of code:"
	@find $(SRC_DIR) -name "*.c" | xargs wc -l | tail -1
	@echo "Header files:"
	@find $(INC_DIR) -name "*.h" | xargs wc -l | tail -1
	@echo "Total files:"
	@find $(SRC_DIR) $(INC_DIR) -name "*.c" -o -name "*.h" | wc -l

# 内存检查
memcheck: $(BIN_DIR)/$(TARGET)
	@echo "Running memory check with valgrind"
	@cd $(BIN_DIR) && valgrind --leak-check=full --show-leak-kinds=all ./$(TARGET)

# 性能分析
profile: $(BIN_DIR)/$(TARGET)
	@echo "Running performance profile with gprof"
	@cd $(BIN_DIR) && gprof ./$(TARGET) gmon.out > analysis.txt

# 帮助信息
help:
	@echo "Available targets:"
	@echo "  all       - Build the project"
	@echo "  clean     - Remove build files"
	@echo "  install   - Install to system"
	@echo "  uninstall - Remove from system"
	@echo "  run       - Run the program"
	@echo "  debug     - Run with debugger"
	@echo "  stats     - Show code statistics"
	@echo "  memcheck  - Run memory leak check"
	@echo "  profile   - Run performance analysis"
	@echo "  help      - Show this help"

.PHONY: all clean install uninstall run debug stats memcheck profile help directories 