# 防火墙项目 Makefile

# 编译器
CC = gcc

# 编译选项
CFLAGS = -Wall -Wextra -g -O2
LDFLAGS = -lnetfilter_queue -lpcap -lpthread

# 目录
SRCDIR = src
INCDIR = include
BUILDDIR = build
TESTDIR = tests

# 源文件
SRCS = $(wildcard $(SRCDIR)/*.c)
OBJS = $(SRCS:$(SRCDIR)/%.c=$(BUILDDIR)/%.o)

# 测试文件
TEST_SRCS = $(wildcard $(TESTDIR)/*.c)
TEST_OBJS = $(TEST_SRCS:$(TESTDIR)/%.c=$(BUILDDIR)/%.o)
TEST_BINS = $(TEST_SRCS:$(TESTDIR)/%.c=$(BUILDDIR)/%)

# 目标
TARGET = $(BUILDDIR)/firewall

# 默认目标
all: $(TARGET) tests

# 创建构建目录
$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# 编译源文件
$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -I$(INCDIR) -c $< -o $@

# 链接主程序
$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $@ $(LDFLAGS)
	@echo "Build complete: $(TARGET)"

# 编译测试
tests: $(TEST_BINS)

$(BUILDDIR)/test_%: $(BUILDDIR)/test_%.o
	$(CC) $< -o $@ $(LDFLAGS)
	@echo "Test built: $@"

$(BUILDDIR)/test_%.o: $(TESTDIR)/%.c | $(BUILDDIR)
	$(CC) $(CFLAGS) -I$(INCDIR) -c $< -o $@

# 运行测试
test: tests
	@echo "Running tests..."
	@for test in $(TEST_BINS); do \
		echo "Running $$test..."; \
		./$$test || exit 1; \
	done
	@echo "All tests passed!"

# 清理
clean:
	rm -rf $(BUILDDIR)

# 安装
install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/firewall
	@echo "Installed to /usr/local/bin/firewall"

# 卸载
uninstall:
	rm -f /usr/local/bin/firewall
	@echo "Uninstalled"

# 调试版本
debug: CFLAGS += -DDEBUG -g3
debug: clean all

# 发布版本
release: CFLAGS += -DNDEBUG -O3
release: clean all

# 代码统计
stats:
	@echo "Source files:"
	@find $(SRCDIR) -name "*.c" | wc -l
	@echo "Header files:"
	@find $(INCDIR) -name "*.h" | wc -l
	@echo "Lines of code:"
	@find $(SRCDIR) $(INCDIR) -name "*.c" -o -name "*.h" | xargs wc -l | tail -1

# 帮助
help:
	@echo "Firewall Project Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all      - Build everything (default)"
	@echo "  tests    - Build tests"
	@echo "  test     - Build and run tests"
	@echo "  clean    - Remove build files"
	@echo "  install  - Install to /usr/local/bin"
	@echo "  uninstall - Remove from /usr/local/bin"
	@echo "  debug    - Build debug version"
	@echo "  release  - Build release version"
	@echo "  stats    - Show code statistics"
	@echo "  help     - Show this help"

.PHONY: all tests test clean install uninstall debug release stats help
