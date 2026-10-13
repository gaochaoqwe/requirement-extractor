CC = gcc
CXX = g++
CFLAGS = -Wall -Wextra -std=c99 -O2
CXXFLAGS = -Wall -Wextra -std=c++11 -O2
LDFLAGS = -lm

# Directories
SRCDIR = .
OBJDIR = build
BINDIR = bin

# Source files
C_SOURCES = $(wildcard utils/*.c) $(wildcard data/*.c)
CXX_SOURCES = $(wildcard core/*.cpp) $(wildcard filters/*.cpp) main.cpp

# Object files
C_OBJECTS = $(C_SOURCES:%.c=$(OBJDIR)/%.o)
CXX_OBJECTS = $(CXX_SOURCES:%.cpp=$(OBJDIR)/%.o)
OBJECTS = $(C_OBJECTS) $(CXX_OBJECTS)

# Target executable
TARGET = $(BINDIR)/image_processor

# Default target
all: $(TARGET)

# Create directories
$(OBJDIR):
	mkdir -p $(OBJDIR)/core $(OBJDIR)/filters $(OBJDIR)/utils $(OBJDIR)/data

$(BINDIR):
	mkdir -p $(BINDIR)

# Build target
$(TARGET): $(OBJECTS) | $(BINDIR)
	$(CXX) $(OBJECTS) -o $@ $(LDFLAGS)

# Compile C sources
$(OBJDIR)/%.o: %.c | $(OBJDIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Compile C++ sources
$(OBJDIR)/%.o: %.cpp | $(OBJDIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build files
clean:
	rm -rf $(OBJDIR) $(BINDIR)

# Install target
install: $(TARGET)
	cp $(TARGET) /usr/local/bin/

# Debug build
debug: CFLAGS += -g -DDEBUG
debug: CXXFLAGS += -g -DDEBUG
debug: $(TARGET)

# Release build
release: CFLAGS += -DNDEBUG
release: CXXFLAGS += -DNDEBUG
release: $(TARGET)

# Run tests
test: $(TARGET)
	./$(TARGET) --help

# Show help
help:
	@echo "Available targets:"
	@echo "  all     - Build the project (default)"
	@echo "  clean   - Remove build files"
	@echo "  debug   - Build with debug symbols"
	@echo "  release - Build optimized release version"
	@echo "  install - Install to /usr/local/bin"
	@echo "  test    - Run basic tests"
	@echo "  help    - Show this help message"

.PHONY: all clean install debug release test help 