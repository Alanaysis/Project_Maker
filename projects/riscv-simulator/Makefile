# ============================================================
# RISC-V Simulator Makefile
# ============================================================

CC      = gcc
CFLAGS  = -Wall -Wextra -std=c11 -Iinclude -g -O2
LDFLAGS =

# 源文件
SRC_DIR  = src
TEST_DIR = tests
INC_DIR  = include

SRCS = $(SRC_DIR)/memory.c \
       $(SRC_DIR)/decoder.c \
       $(SRC_DIR)/executor.c \
       $(SRC_DIR)/cpu.c \
       $(SRC_DIR)/assembler.c

OBJS = $(SRCS:.c=.o)

# 主程序
MAIN_SRC = $(SRC_DIR)/main.c
TARGET   = riscv-sim

# 测试程序
TEST_MEMORY    = test_memory
TEST_DECODER   = test_decoder
TEST_ASSEMBLER = test_assembler
TEST_INTEGRATION = test_integration

# 验证脚本
VERIFY_SCRIPT = verify.sh

# ============================================================
# 构建目标
# ============================================================

.PHONY: all clean test test-memory test-decoder test-assembler test-integration verify help

all: $(TARGET)

$(TARGET): $(OBJS) $(MAIN_SRC)
	$(CC) $(CFLAGS) -o $@ $(MAIN_SRC) $(OBJS) $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# ============================================================
# 测试目标
# ============================================================

test: test-memory test-decoder test-assembler test-integration
	@echo "All tests completed."

test-memory: $(TEST_DIR)/test_memory.c $(SRC_DIR)/memory.c
	$(CC) $(CFLAGS) -o $(TEST_DIR)/$(TEST_MEMORY) $^ $(LDFLAGS)
	./$(TEST_DIR)/$(TEST_MEMORY)

test-decoder: $(TEST_DIR)/test_decoder.c $(SRC_DIR)/decoder.c
	$(CC) $(CFLAGS) -o $(TEST_DIR)/$(TEST_DECODER) $^ $(LDFLAGS)
	./$(TEST_DIR)/$(TEST_DECODER)

test-assembler: $(TEST_DIR)/test_assembler.c $(SRC_DIR)/assembler.c $(SRC_DIR)/decoder.c
	$(CC) $(CFLAGS) -o $(TEST_DIR)/$(TEST_ASSEMBLER) $^ $(LDFLAGS)
	./$(TEST_DIR)/$(TEST_ASSEMBLER)

test-integration: $(TEST_DIR)/test_integration.c $(OBJS)
	$(CC) $(CFLAGS) -o $(TEST_DIR)/$(TEST_INTEGRATION) $(TEST_DIR)/test_integration.c $(OBJS) $(LDFLAGS)
	./$(TEST_DIR)/$(TEST_INTEGRATION)

# ============================================================
# 验证
# ============================================================

verify: all test
	@echo "Running verification..."
	@if [ -f $(VERIFY_SCRIPT) ]; then bash $(VERIFY_SCRIPT); fi
	@echo "Verification complete."

# ============================================================
# 内置测试
# ============================================================

builtin-test: $(TARGET)
	./$(TARGET) --test

# ============================================================
# 清理
# ============================================================

clean:
	rm -f $(OBJS)
	rm -f $(TARGET)
	rm -f $(TEST_DIR)/$(TEST_MEMORY)
	rm -f $(TEST_DIR)/$(TEST_DECODER)
	rm -f $(TEST_DIR)/$(TEST_ASSEMBLER)
	rm -f $(TEST_DIR)/$(TEST_INTEGRATION)

# ============================================================
# 帮助
# ============================================================

help:
	@echo "RISC-V Simulator Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all              Build the simulator"
	@echo "  test             Run all tests"
	@echo "  test-memory      Run memory tests"
	@echo "  test-decoder     Run decoder tests"
	@echo "  test-assembler   Run assembler tests"
	@echo "  test-integration Run integration tests"
	@echo "  builtin-test     Run built-in test program"
	@echo "  verify           Build, test, and verify"
	@echo "  clean            Remove build artifacts"
	@echo "  help             Show this help"
	@echo ""
	@echo "Usage:"
	@echo "  ./riscv-sim program.bin           Run binary"
	@echo "  ./riscv-sim -a program.s          Assemble and run"
	@echo "  ./riscv-sim -d 4 program.bin      Run with trace"
	@echo "  ./riscv-sim -s program.bin        Single-step mode"
	@echo "  ./riscv-sim --test                Run built-in test"
