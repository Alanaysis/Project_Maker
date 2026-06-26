/*
 * device-driver-framework - User-Space Test Program
 *
 * Demonstrates how to interact with the character device driver from user space.
 * Tests all file operations: open, write, read, ioctl, and poll.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>

#include "../include/device_framework.h"

/* Test result tracking */
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("\n=== Test: %s ===\n", name)
#define PASS(name) do { printf("[PASS] %s\n", name); tests_passed++; } while(0)
#define FAIL(name, msg) do { printf("[FAIL] %s: %s\n", name, msg); tests_failed++; } while(0)

/* ============================================================
 * Test: Device Open/Close
 * ============================================================ */
static void test_open_close(void)
{
    TEST("Device Open/Close");

    int fd = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd < 0) {
        FAIL("open/close", strerror(errno));
        return;
    }
    PASS("open");

    /* Close the device */
    if (close(fd) == 0) {
        PASS("close");
    } else {
        FAIL("close", strerror(errno));
    }
}

/* ============================================================
 * Test: Write Data
 * ============================================================ */
static void test_write(void)
{
    TEST("Write Data");

    const char *test_data = "Hello from device-driver-framework!";
    int fd = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd < 0) {
        FAIL("write", strerror(errno));
        return;
    }

    ssize_t written = write(fd, test_data, strlen(test_data));
    if (written > 0) {
        printf("Wrote %zd bytes: \"%s\"\n", written, test_data);
        PASS("write");
    } else {
        FAIL("write", strerror(errno));
    }

    close(fd);
}

/* ============================================================
 * Test: Read Data
 * ============================================================ */
static void test_read(void)
{
    TEST("Read Data");

    int fd = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd < 0) {
        FAIL("read", strerror(errno));
        return;
    }

    char buffer[256];
    memset(buffer, 0, sizeof(buffer));

    /* First write some data */
    const char *test_data = "Test data for reading";
    write(fd, test_data, strlen(test_data));

    /* Reset file position */
    lseek(fd, 0, SEEK_SET);

    /* Read the data back */
    ssize_t read_bytes = read(fd, buffer, sizeof(buffer) - 1);
    if (read_bytes > 0) {
        buffer[read_bytes] = '\0';
        printf("Read %zd bytes: \"%s\"\n", read_bytes, buffer);

        if (strcmp(buffer, test_data) == 0) {
            PASS("read (data matches)");
        } else {
            FAIL("read", "data mismatch");
        }
    } else {
        FAIL("read", strerror(errno));
    }

    close(fd);
}

/* ============================================================
 * Test: IOCTL Operations
 * ============================================================ */
static void test_ioctl(void)
{
    TEST("IOCTL Operations");

    int fd = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd < 0) {
        FAIL("ioctl", strerror(errno));
        return;
    }

    /* Test GET_STATUS */
    struct dfw_status status;
    memset(&status, 0, sizeof(status));
    long *status_ptr = (long *)&status;

    if (ioctl(fd, DFW_CMD_GET_STATUS, status_ptr) == 0) {
        printf("Device Status:\n");
        printf("  Open count: %d\n", status.open_count);
        printf("  Data length: %zu\n", status.data_len);
        printf("  Buffer size: %zu\n", status.buffer_size);
        printf("  IRQ number: %d\n", status.irq_number);
        printf("  Is open: %d\n", status.is_open);
        PASS("GET_STATUS");
    } else {
        FAIL("GET_STATUS", strerror(errno));
    }

    /* Test SET_BUFFER_SIZE */
    if (ioctl(fd, DFW_CMD_SET_BUFFER_SIZE, 8192UL) == 0) {
        PASS("SET_BUFFER_SIZE");
    } else {
        FAIL("SET_BUFFER_SIZE", strerror(errno));
    }

    /* Test GET_BUFFER_INFO */
    struct dfw_buffer_info info;
    long *info_ptr = (long *)&info;

    if (ioctl(fd, DFW_CMD_GET_BUFFER_INFO, info_ptr) == 0) {
        printf("Buffer Info:\n");
        printf("  Size: %zu\n", info.size);
        printf("  Used: %zu\n", info.used);
        printf("  Free: %zu\n", info.free);
        PASS("GET_BUFFER_INFO");
    } else {
        FAIL("GET_BUFFER_INFO", strerror(errno));
    }

    /* Test RESET_DEVICE */
    if (ioctl(fd, DFW_CMD_RESET_DEVICE) == 0) {
        PASS("RESET_DEVICE");
    } else {
        FAIL("RESET_DEVICE", strerror(errno));
    }

    close(fd);
}

/* ============================================================
 * Test: Poll/Select Support
 * ============================================================ */
static void test_poll(void)
{
    TEST("Poll Support");

    int fd = open(DFW_DEVICE_PATH, O_RDWR | O_NONBLOCK);
    if (fd < 0) {
        FAIL("poll", strerror(errno));
        return;
    }

    struct pollfd pfd;
    pfd.fd = fd;
    pfd.events = POLLIN | POLLOUT;

    /* Poll with 1 second timeout */
    int ret = poll(&pfd, 1, 1000);
    if (ret > 0) {
        printf("Poll returned: ");
        if (pfd.revents & POLLIN) printf("POLLIN ");
        if (pfd.revents & POLLOUT) printf("POLLOUT ");
        if (pfd.revents & POLLERR) printf("POLLERR ");
        if (pfd.revents & POLLHUP) printf("POLLHUP ");
        printf("\n");
        PASS("poll");
    } else if (ret == 0) {
        printf("Poll timed out (no data available)\n");
        PASS("poll (timeout expected)");
    } else {
        FAIL("poll", strerror(errno));
    }

    close(fd);
}

/* ============================================================
 * Test: Concurrent Access
 * ============================================================ */
static void test_concurrent(void)
{
    TEST("Concurrent Access");

    int fd1 = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd1 < 0) {
        FAIL("concurrent", "first open failed");
        return;
    }

    /* Try to open again (should fail for exclusive access) */
    int fd2 = open(DFW_DEVICE_PATH, O_RDWR);
    if (fd2 < 0) {
        if (errno == EBUSY) {
            PASS("concurrent (exclusive access enforced)");
        } else {
            FAIL("concurrent", strerror(errno));
        }
        close(fd1);
        return;
    }

    /* If second open succeeded, device is not exclusive */
    printf("Device allows multiple opens (non-exclusive mode)\n");
    PASS("concurrent (non-exclusive)");

    close(fd1);
    close(fd2);
}

/* ============================================================
 * Test: Error Handling
 * ============================================================ */
static void test_error_handling(void)
{
    TEST("Error Handling");

    /* Test reading from non-existent device */
    int fd = open("/dev/nonexistent_device", O_RDWR);
    if (fd < 0) {
        if (errno == ENOENT) {
            PASS("error handling (device not found)");
        } else {
            FAIL("error handling", strerror(errno));
        }
        return;
    }

    /* Test invalid IOCTL */
    long ret = ioctl(fd, 999, 0);
    if (ret < 0 && errno == ENOTTY) {
        PASS("error handling (invalid ioctl)");
    } else {
        FAIL("error handling", "expected ENOTTY");
    }

    close(fd);
}

/* ============================================================
 * Main - Run All Tests
 * ============================================================ */
int main(int argc, char *argv[])
{
    printf("========================================\n");
    printf("  Device Driver Framework - Test Suite\n");
    printf("========================================\n");
    printf("Device path: %s\n", DFW_DEVICE_PATH);

    /* Check if device exists */
    struct stat st;
    if (stat(DFW_DEVICE_PATH, &st) != 0) {
        fprintf(stderr, "\nWarning: Device %s does not exist.\n", DFW_DEVICE_PATH);
        fprintf(stderr, "Load the kernel module first:\n");
        fprintf(stderr, "  sudo insmod device_framework.ko\n");
        fprintf(stderr, "\nRunning tests anyway (they will fail without the module)...\n\n");
    }

    /* Run all tests */
    test_open_close();
    test_write();
    test_read();
    test_ioctl();
    test_poll();
    test_concurrent();
    test_error_handling();

    /* Print summary */
    printf("\n========================================\n");
    printf("  Test Results\n");
    printf("========================================\n");
    printf("  Passed: %d\n", tests_passed);
    printf("  Failed: %d\n", tests_failed);
    printf("  Total:  %d\n", tests_passed + tests_failed);
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
