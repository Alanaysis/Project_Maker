# 键盘驱动 Makefile

# 编译器
CC = gcc

# 编译选项
CFLAGS = -Wall -Wextra -Werror -std=c99 -g -I./include
LDFLAGS =

# 目录
SRCDIR = src
INCDIR = include
TESTDIR = tests
EXAMPLEDIR = examples
BUILDDIR = build

# 源文件
SRC_FILES = $(SRCDIR)/keyboard_driver.c \
            $(SRCDIR)/matrix_scanner.c \
            $(SRCDIR)/interrupt_handler.c \
            $(SRCDIR)/debounce.c \
            $(SRCDIR)/input_event.c

# 目标文件
OBJ_FILES = $(patsubst $(SRCDIR)/%.c,$(BUILDDIR)/%.o,$(SRC_FILES))

# 可执行文件
TEST_BIN = $(BUILDDIR)/keyboard_test
EXAMPLE_BIN = $(BUILDDIR)/keyboard_example

# 默认目标
all: dirs test example

# 创建构建目录
dirs:
	@mkdir -p $(BUILDDIR)

# 编译源文件
$(BUILDDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# 编译测试
test: dirs $(OBJ_FILES) $(TESTDIR)/test_keyboard.c
	$(CC) $(CFLAGS) $(OBJ_FILES) $(TESTDIR)/test_keyboard.c -o $(TEST_BIN) $(LDFLAGS)
	@echo "Test binary built: $(TEST_BIN)"

# 编译示例
example: dirs $(OBJ_FILES) $(EXAMPLEDIR)/example.c
	$(CC) $(CFLAGS) $(OBJ_FILES) $(EXAMPLEDIR)/example.c -o $(EXAMPLE_BIN) $(LDFLAGS)
	@echo "Example binary built: $(EXAMPLE_BIN)"

# 运行测试
run-test: test
	@echo "Running tests..."
	@$(TEST_BIN)

# 运行示例
run-example: example
	@echo "Running example..."
	@$(EXAMPLE_BIN)

# 清理
clean:
	rm -rf $(BUILDDIR)

# 重新构建
rebuild: clean all

# 安装（模拟）
install:
	@echo "Installing keyboard driver..."
	@echo "Note: This is a userspace simulation, not a real kernel module"

# 显示帮助
help:
	@echo "Keyboard Driver Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all         - Build test and example binaries"
	@echo "  test        - Build test binary"
	@echo "  example     - Build example binary"
	@echo "  run-test    - Build and run tests"
	@echo "  run-example - Build and run example"
	@echo "  clean       - Remove build artifacts"
	@echo "  rebuild     - Clean and rebuild"
	@echo "  install     - Install (simulated)"
	@echo "  help        - Show this help"
	@echo ""
	@echo "Variables:"
	@echo "  CC          - Compiler (default: gcc)"
	@echo "  CFLAGS      - Compiler flags"
	@echo "  LDFLAGS     - Linker flags"

.PHONY: all dirs test example run-test run-example clean rebuild install help
