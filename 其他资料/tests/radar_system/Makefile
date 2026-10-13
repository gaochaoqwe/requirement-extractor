# Makefile for Radar Simulation System

CC = gcc
CFLAGS = -Wall -Wextra -I include -std=c99
LDFLAGS = -lm
TARGET = radar_sim
SRC_DIR = src
INC_DIR = include
OBJ_DIR = obj

# Source files
SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(SRCS:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

# Default target
all: $(TARGET)

# Create object directory
$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

# Compile source files
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Link object files
$(TARGET): $(OBJS)
	$(CC) $(OBJS) $(LDFLAGS) -o $(TARGET)

# Clean build files
clean:
	rm -rf $(OBJ_DIR) $(TARGET) radar.log

# Run the program
run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run

