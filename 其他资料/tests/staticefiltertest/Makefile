# Makefile for static analysis filter test
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -g
TARGET = test_program
SOURCES = main.c array_bounds.c memory_usage.c uninitialized_vars.c test_utils.c
OBJECTS = $(SOURCES:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

# 运行测试
run: $(TARGET)
	./$(TARGET)

# 静态分析
analyze:
	@echo "Running static analysis..."
	@echo "Note: This would typically run tools like cppcheck, clang-static-analyzer, etc."
	
# 帮助信息
help:
	@echo "Available targets:"
	@echo "  all     - Build the test program"
	@echo "  clean   - Remove object files and executable"
	@echo "  run     - Build and run the test program"
	@echo "  analyze - Run static analysis tools"
	@echo "  help    - Show this help message"
