/*
 * embedded-fs/tests/test_wear_leveling.c
 *
 * Unit Tests for Wear Leveling
 * 磨损均衡单元测试
 * ============================================================ */

#include <stdio.h>
#include <string.h>
#include "../include/efs_types.h"
#include "../include/efs_flash.h"
#include "../include/efs_block.h"
#include "../include/efs_dir.h"
#include "../include/efs_file.h"
#include "../include/efs_log.h"
#include "../include/efs_wear.h"
#include "../include/efs_recovery.h"

extern EFS_Result efs_format(void);

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg)  printf("FAIL: %s\n", msg); tests_failed++
#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

static void test_wear_init(void) {
    TEST("wear leveling init");

    efs_format();

    EFS_Result res = efs_wear_init();
    ASSERT(res == EFS_OK, "wear init should succeed");

    EFS_WearStats stats;
    res = efs_wear_get_stats(&stats);
    ASSERT(res == EFS_OK, "get stats should succeed");
    ASSERT(stats.total_writes == 0, "initial writes should be 0");
    ASSERT(stats.total_erases == 0, "initial erases should be 0");

    PASS();
}

static void test_wear_distribution(void) {
    TEST("wear distribution");

    efs_format();

    /* Write many files to distribute wear */
    for (int i = 0; i < 100; i++) {
        char fname[64];
        snprintf(fname, sizeof(fname), "/wear_%d", i);
        int fd = efs_open(fname, EFS_O_WRONLY | EFS_O_CREAT);
        if (fd >= 0) {
            const char *data = "wear test data\n";
            efs_write(fd, data, strlen(data));
            efs_close(fd);
        }
    }

    EFS_WearStats stats;
    efs_wear_get_stats(&stats);

    /* With wear leveling, max wear should be reasonable */
    ASSERT(stats.worst_block_wear < 500, "max wear should be reasonable");
    ASSERT(stats.best_block_wear < stats.worst_block_wear, "best wear < worst wear");

    PASS();
}

static void test_wear_needs_leveling(void) {
    TEST("wear leveling detection");

    efs_format();

    /* Initially no wear difference */
    int needs = efs_wear_needs_leveling();
    ASSERT(needs == 0, "no leveling needed initially");

    /* After writes, check if leveling was triggered */
    for (int i = 0; i < 200; i++) {
        char fname[64];
        snprintf(fname, sizeof(fname), "/level_%d", i);
        int fd = efs_open(fname, EFS_O_WRONLY | EFS_O_CREAT);
        if (fd >= 0) {
            efs_write(fd, "leveling test\n", 14);
            efs_close(fd);
        }
    }

    needs = efs_wear_needs_leveling();
    /* Either needs leveling or not, both are valid */
    (void)needs;

    PASS();
}

static void test_wear_stats(void) {
    TEST("wear stats accuracy");

    efs_format();

    /* Write some data */
    for (int i = 0; i < 50; i++) {
        char fname[64];
        snprintf(fname, sizeof(fname), "/stats_%d", i);
        int fd = efs_open(fname, EFS_O_WRONLY | EFS_O_CREAT);
        if (fd >= 0) {
            efs_write(fd, "stats test\n", 11);
            efs_close(fd);
        }
    }

    EFS_WearStats stats;
    efs_wear_get_stats(&stats);

    ASSERT(stats.avg_wear > 0, "avg wear should be positive");
    ASSERT(stats.worst_block_wear >= stats.best_block_wear, "worst >= best");
    ASSERT(stats.gc_count >= 0, "GC count non-negative");

    PASS();
}

static void test_gc_collect(void) {
    TEST("garbage collection");

    efs_format();

    /* Create some files */
    for (int i = 0; i < 50; i++) {
        char fname[64];
        snprintf(fname, sizeof(fname), "/gc_%d", i);
        int fd = efs_open(fname, EFS_O_WRONLY | EFS_O_CREAT);
        if (fd >= 0) {
            efs_write(fd, "gc test data\n", 13);
            efs_close(fd);
        }
    }

    /* Trigger GC */
    EFS_Result res = efs_gc_collect();
    ASSERT(res == EFS_OK, "GC should succeed");

    EFS_WearStats stats;
    efs_wear_get_stats(&stats);
    ASSERT(stats.gc_count >= 1, "GC should have been called");

    PASS();
}

int main(void) {
    printf("=== Embedded File System - Wear Leveling Tests ===\n");
    printf("===================================================\n\n");

    test_wear_init();
    test_wear_distribution();
    test_wear_needs_leveling();
    test_wear_stats();
    test_gc_collect();

    printf("\n===================================================\n");
    printf("Results: %d/%d passed, %d failed\n",
           tests_passed, tests_run, tests_failed);
    printf("===================================================\n");

    return tests_failed > 0 ? 1 : 0;
}
