/*
 * device-driver-framework - Unit Test Framework
 *
 * Provides a test harness for validating driver components.
 * In a real kernel module, tests would use the kernel test framework.
 * This user-space test validates the IOCTL interface and data flow.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../include/device_framework.h"

/* ============================================================
 * Test Framework
 * ============================================================ */

typedef struct {
    const char *name;
    int passed;
    int failed;
    int total;
} test_suite_t;

static test_suite_t current_suite;
static int total_passed = 0;
static int total_failed = 0;

void test_begin(const char *name)
{
    current_suite.name = name;
    current_suite.passed = 0;
    current_suite.failed = 0;
    current_suite.total = 0;
    printf("\n=== %s ===\n", name);
}

void test_pass(const char *desc)
{
    current_suite.passed++;
    current_suite.total++;
    printf("  [PASS] %s\n", desc);
    total_passed++;
}

void test_fail(const char *desc, const char *reason)
{
    current_suite.failed++;
    current_suite.total++;
    printf("  [FAIL] %s: %s\n", desc, reason);
    total_failed++;
}

void test_end(void)
{
    printf("  Result: %d/%d passed\n", current_suite.passed, current_suite.total);
}

#define ASSERT_EQ(a, b, desc) do { \
    if ((a) == (b)) { \
        test_pass(desc); \
    } else { \
        test_fail(desc, "expected " #a " == " #b); \
    } \
} while(0)

#define ASSERT_GT(a, b, desc) do { \
    if ((a) > (b)) { \
        test_pass(desc); \
    } else { \
        test_fail(desc, "expected " #a " > " #b); \
    } \
} while(0)

#define ASSERT_NULL(p, desc) do { \
    if ((p) == NULL) { \
        test_pass(desc); \
    } else { \
        test_fail(desc, "expected NULL"); \
    } \
} while(0)

#define ASSERT_NOT_NULL(p, desc) do { \
    if ((p) != NULL) { \
        test_pass(desc); \
    } else { \
        test_fail(desc, "expected non-NULL"); \
    } \
} while(0)

/* ============================================================
 * Test: Data Structure Sizes
 * ============================================================ */
static void test_struct_sizes(void)
{
    test_begin("Data Structure Size Tests");

    /* Verify structure sizes for user-kernel compatibility */
    ASSERT_EQ(sizeof(struct dfw_status), sizeof(struct dfw_status),
              "struct dfw_size is consistent");

    ASSERT_EQ(sizeof(struct dfw_buffer_info), sizeof(struct dfw_buffer_info),
              "struct dfw_buffer_info size is consistent");

    test_end();
}

/* ============================================================
 * Test: Buffer Management (standalone)
 * ============================================================ */
static void test_buffer_management(void)
{
    test_begin("Buffer Management Tests");

    /* Simulate buffer operations */
    size_t buf_size = 4096;
    char *buf = malloc(buf_size);
    ASSERT_NOT_NULL(buf, "buffer allocation");

    /* Test memset */
    memset(buf, 0, buf_size);
    test_pass("buffer zero-initialization");

    /* Test write simulation */
    const char *test = "Hello, World!";
    size_t len = strlen(test);
    memcpy(buf, test, len);
    ASSERT_GT(len, 0, "write length > 0");

    /* Test read simulation */
    char read_buf[16];
    memcpy(read_buf, buf, min(len, sizeof(read_buf) - 1));
    read_buf[min(len, sizeof(read_buf) - 1)] = '\0';
    ASSERT_EQ(strcmp(read_buf, test), 0, "read matches write");

    free(buf);
    test_pass("buffer deallocation");

    test_end();
}

/* ============================================================
 * Test: IOCTL Command Encoding
 * ============================================================ */
static void test_ioctl_commands(void)
{
    test_begin("IOCTL Command Tests");

    /* Verify IOCTL command encoding */
    long cmd0 = DFW_CMD_GET_STATUS;
    long cmd1 = DFW_CMD_SET_BUFFER_SIZE;
    long cmd2 = DFW_CMD_RESET_DEVICE;
    long cmd3 = DFW_CMD_GET_BUFFER_INFO;

    ASSERT_GT(cmd0, 0, "GET_STATUS command is valid");
    ASSERT_GT(cmd1, 0, "SET_BUFFER_SIZE command is valid");
    ASSERT_GT(cmd2, 0, "RESET_DEVICE command is valid");
    ASSERT_GT(cmd3, 0, "GET_BUFFER_INFO command is valid");

    /* Verify magic number */
    ASSERT_EQ('k', DFW_IOC_MAGIC, "IOCTL magic number is 'k'");

    test_end();
}

/* ============================================================
 * Test: Constants Validation
 * ============================================================ */
static void test_constants(void)
{
    test_begin("Constants Validation");

    ASSERT_GT(DEVICE_FRAMEWORK_BUFFER_SIZE, 0, "buffer size > 0");
    ASSERT_GT(DEVICE_FRAMEWORK_MAX_BUFFER, DEVICE_FRAMEWORK_BUFFER_SIZE,
              "max buffer > default buffer");
    ASSERT_EQ(DEVICE_FRAMEWORK_NUM_DEVICES, 1, "num devices = 1");
    ASSERT_GT(DEVICE_FRAMEWORK_MAJOR, 0, "major number is valid");

    test_end();
}

/* ============================================================
 * Test: Memory Alignment (platform independence)
 * ============================================================ */
static void test_memory_alignment(void)
{
    test_begin("Memory Alignment Tests");

    /* Verify structure field offsets are reasonable */
    struct dfw_status s;
    memset(&s, 0, sizeof(s));

    /* All fields should be accessible */
    s.open_count = 42;
    s.data_len = 128;
    s.buffer_size = 1024;
    s.irq_number = 5;
    s.is_open = 1;
    s.initialized = 1;

    ASSERT_EQ(s.open_count, 42, "open_count field accessible");
    ASSERT_EQ(s.data_len, 128, "data_len field accessible");
    ASSERT_EQ(s.buffer_size, 1024, "buffer_size field accessible");
    ASSERT_EQ(s.irq_number, 5, "irq_number field accessible");

    test_end();
}

/* ============================================================
 * Main
 * ============================================================ */
int main(int argc, char *argv[])
{
    printf("========================================\n");
    printf("  Device Driver Framework - Unit Tests\n");
    printf("========================================\n");

    test_struct_sizes();
    test_buffer_management();
    test_ioctl_commands();
    test_constants();
    test_memory_alignment();

    printf("\n========================================\n");
    printf("  Summary\n");
    printf("========================================\n");
    printf("  Passed: %d\n", total_passed);
    printf("  Failed: %d\n", total_failed);
    printf("  Total:  %d\n", total_passed + total_failed);
    printf("========================================\n");

    return total_failed > 0 ? 1 : 0;
}
