CC = gcc
CFLAGS = -Wall -Wextra -g
LDFLAGS = 

SRC_DIR = src
INCLUDE_DIR = include
OBJ_DIR = obj
BIN_DIR = bin

# 源文件列表
SRC_FILES = $(wildcard $(SRC_DIR)/*.c)
OBJ_FILES = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SRC_FILES))

# 可执行文件
TARGET = $(BIN_DIR)/system_monitor

# 默认目标
all: directories $(TARGET)

# 创建必要的目录
directories:
	mkdir -p $(OBJ_DIR) $(BIN_DIR)

# 编译可执行文件
$(TARGET): $(OBJ_FILES)
	$(CC) $(LDFLAGS) -o $@ $^

# 编译源文件
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c -o $@ $<

# 清理生成的文件
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

# 运行程序
run: all
	$(TARGET)

.PHONY: all directories clean run 