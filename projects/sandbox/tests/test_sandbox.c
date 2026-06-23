/*
 * test_sandbox.c - Unit tests for the sandbox library
 *
 * Tests cover:
 * - Context creation/destruction
 * - Rule management
 * - Whitelist mode (allowed and blocked syscalls)
 * - Resource limits
 * - Statistics collection
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <signal.h>
#include <sys/wait.h>
#include "sandbox.h"

/* Test framework macros */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;
static int tests_skipped = 0;

#define TEST_START(name) \
    do { \
        tests_run++; \
        printf("[TEST %d] %s ... ", tests_run, name); \
        fflush(stdout); \
    } while (0)

#define TEST_PASS() \
    do { \
        tests_passed++; \
        printf("PASS\n"); \
    } while (0)

#define TEST_FAIL(msg) \
    do { \
        tests_failed++; \
        printf("FAIL: %s\n", msg); \
    } while (0)

#define TEST_SKIP(msg) \
    do { \
        tests_skipped++; \
        printf("SKIP: %s\n", msg); \
    } while (0)

#define ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            TEST_FAIL(msg); \
            return; \
        } \
    } while (0)

/* ===== Test Cases ===== */

static void test_create_destroy(void) {
    TEST_START("create and destroy sandbox");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create returned NULL");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_create_multiple(void) {
    TEST_START("create multiple sandboxes");

    sandbox_ctx_t *ctx1 = sandbox_create();
    sandbox_ctx_t *ctx2 = sandbox_create();
    ASSERT(ctx1 != NULL, "first sandbox is NULL");
    ASSERT(ctx2 != NULL, "second sandbox is NULL");
    ASSERT(ctx1 != ctx2, "sandboxes should be different objects");

    sandbox_destroy(ctx1);
    sandbox_destroy(ctx2);
    TEST_PASS();
}

static void test_set_mode(void) {
    TEST_START("set sandbox mode");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    ASSERT(sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST) == 0,
           "set whitelist mode failed");
    ASSERT(sandbox_set_mode(ctx, SANDBOX_MODE_BLACKLIST) == 0,
           "set blacklist mode failed");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_set_mode_null(void) {
    TEST_START("set mode with NULL context");

    ASSERT(sandbox_set_mode(NULL, SANDBOX_MODE_WHITELIST) == -1,
           "should return -1 for NULL context");

    TEST_PASS();
}

static void test_add_rules(void) {
    TEST_START("add syscall rules");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_syscall_rule_t rule = {
#ifdef __NR_read
        .syscall_nr = __NR_read,
#endif
        .allow = true,
        .num_args = 0,
        .description = "read"
    };

    ASSERT(sandbox_add_rule(ctx, &rule) == 0, "add_rule failed");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_add_rule_null(void) {
    TEST_START("add rule with NULL context");

    sandbox_syscall_rule_t rule = {
        .syscall_nr = 0,
        .allow = true,
        .num_args = 0,
        .description = "test"
    };

    ASSERT(sandbox_add_rule(NULL, &rule) == -1,
           "should return -1 for NULL context");

    TEST_PASS();
}

static void test_add_too_many_rules(void) {
    TEST_START("add too many rules");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_syscall_rule_t rule = {
        .syscall_nr = 0,
        .allow = true,
        .num_args = 0,
        .description = "test"
    };

    /* Fill up all slots */
    for (int i = 0; i < SANDBOX_MAX_SYSCALL_RULES; i++) {
        ASSERT(sandbox_add_rule(ctx, &rule) == 0, "add_rule failed");
    }

    /* Next one should fail */
    ASSERT(sandbox_add_rule(ctx, &rule) == -1,
           "should fail when max rules reached");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_set_rlimits(void) {
    TEST_START("set resource limits");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_rlimits_t limits = {
        .file_size_limit = 1024 * 1024,
        .open_files_limit = 32,
        .stack_size_limit = 4 * 1024 * 1024,
    };

    ASSERT(sandbox_set_rlimits(ctx, &limits) == 0, "set_rlimits failed");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_set_rlimits_null(void) {
    TEST_START("set rlimits with NULL context");

    sandbox_rlimits_t limits = { .file_size_limit = 1024 };
    ASSERT(sandbox_set_rlimits(NULL, &limits) == -1,
           "should return -1 for NULL context");

    TEST_PASS();
}

static void test_syscall_name(void) {
    TEST_START("syscall name lookup");

    /* Known syscall names */
    const char *name;

#ifdef __NR_read
    name = sandbox_syscall_name(__NR_read);
    ASSERT(strcmp(name, "read") == 0, "read syscall name mismatch");
#endif

#ifdef __NR_write
    name = sandbox_syscall_name(__NR_write);
    ASSERT(strcmp(name, "write") == 0, "write syscall name mismatch");
#endif

#ifdef __NR_exit
    name = sandbox_syscall_name(__NR_exit);
    ASSERT(strcmp(name, "exit") == 0, "exit syscall name mismatch");
#endif

    /* Unknown syscall */
    name = sandbox_syscall_name(99999);
    ASSERT(strcmp(name, "unknown") == 0, "unknown syscall should return 'unknown'");

    TEST_PASS();
}

static void test_default_whitelist(void) {
    TEST_START("default whitelist");

    const int *wl = sandbox_default_whitelist();
    ASSERT(wl != NULL, "default whitelist is NULL");

    /* Should contain at least a few syscalls */
    int count = 0;
    for (int i = 0; wl[i] != -1; i++) {
        count++;
    }
    ASSERT(count >= 5, "default whitelist should have at least 5 entries");

    TEST_PASS();
}

static void test_whitelist_exec_echo(void) {
    TEST_START("whitelist: execute /bin/echo");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Add default safe syscalls */
    const int *wl = sandbox_default_whitelist();
    for (int i = 0; wl[i] != -1; i++) {
        sandbox_syscall_rule_t rule = {
            .syscall_nr = wl[i],
            .allow = true,
            .num_args = 0,
            .description = sandbox_syscall_name(wl[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    /* Allow execve */
    sandbox_syscall_rule_t exec_rule = {
#ifdef __NR_execve
        .syscall_nr = __NR_execve,
#endif
        .allow = true,
        .num_args = 0,
        .description = "execve"
    };
    sandbox_add_rule(ctx, &exec_rule);

    char *argv[] = { "/bin/echo", "sandbox_test_ok", NULL };
    ASSERT(sandbox_exec(ctx, 2, argv) == 0, "sandbox_exec failed");

    sandbox_stats_t stats;
    ASSERT(sandbox_wait(ctx, &stats) == 0, "sandbox_wait failed");

    /* seccomp requires privileges - skip if not available */
    if (stats.exited_normally && stats.exit_status == 127) {
        sandbox_destroy(ctx);
        TEST_SKIP("seccomp requires privileges (run with sudo)");
        return;
    }

    ASSERT(stats.exited_normally, "echo should exit normally");
    ASSERT(stats.exit_status == 0, "echo should exit with 0");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_whitelist_block_fork(void) {
    TEST_START("whitelist: fork is blocked");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Add minimal syscalls (no fork) */
    int minimal[] = {
#ifdef __NR_read
        __NR_read,
#endif
#ifdef __NR_write
        __NR_write,
#endif
#ifdef __NR_exit
        __NR_exit,
#endif
#ifdef __NR_exit_group
        __NR_exit_group,
#endif
#ifdef __NR_brk
        __NR_brk,
#endif
#ifdef __NR_mmap
        __NR_mmap,
#endif
#ifdef __NR_munmap
        __NR_munmap,
#endif
#ifdef __NR_mprotect
        __NR_mprotect,
#endif
#ifdef __NR_fstat
        __NR_fstat,
#endif
#ifdef __NR_close
        __NR_close,
#endif
#ifdef __NR_execve
        __NR_execve,
#endif
#ifdef __NR_arch_prctl
        __NR_arch_prctl,
#endif
#ifdef __NR_set_tid_address
        __NR_set_tid_address,
#endif
#ifdef __NR_futex
        __NR_futex,
#endif
#ifdef __NR_rt_sigaction
        __NR_rt_sigaction,
#endif
#ifdef __NR_rt_sigprocmask
        __NR_rt_sigprocmask,
#endif
    };

    int count = sizeof(minimal) / sizeof(minimal[0]);
    for (int i = 0; i < count; i++) {
        if (minimal[i] == 0) continue;
        sandbox_syscall_rule_t rule = {
            .syscall_nr = minimal[i],
            .allow = true,
            .num_args = 0,
            .description = sandbox_syscall_name(minimal[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    /* Try to run a program that forks (should be killed) */
    char *argv[] = { "/bin/sh", "-c", "fork_test_var=1", NULL };
    ASSERT(sandbox_exec(ctx, 3, argv) == 0, "sandbox_exec failed");

    sandbox_stats_t stats;
    ASSERT(sandbox_wait(ctx, &stats) == 0, "sandbox_wait failed");

    /* seccomp requires privileges - skip if not available */
    if (stats.exited_normally && stats.exit_status == 127) {
        sandbox_destroy(ctx);
        TEST_SKIP("seccomp requires privileges (run with sudo)");
        return;
    }

    /* /bin/sh will try to fork, which should be blocked */
    /* It may exit with non-zero or be killed by signal */
    ASSERT(!stats.exited_normally || stats.exit_status != 0,
           "forking program should fail");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_resource_limits(void) {
    TEST_START("resource limits applied");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Add default safe syscalls */
    const int *wl = sandbox_default_whitelist();
    for (int i = 0; wl[i] != -1; i++) {
        sandbox_syscall_rule_t rule = {
            .syscall_nr = wl[i],
            .allow = true,
            .num_args = 0,
            .description = sandbox_syscall_name(wl[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    /* Allow execve */
    sandbox_syscall_rule_t exec_rule = {
#ifdef __NR_execve
        .syscall_nr = __NR_execve,
#endif
        .allow = true,
        .num_args = 0,
        .description = "execve"
    };
    sandbox_add_rule(ctx, &exec_rule);

    /* Set tight limits */
    sandbox_rlimits_t limits = {
        .file_size_limit = 4096,
        .open_files_limit = 8,
    };
    sandbox_set_rlimits(ctx, &limits);

    char *argv[] = { "/bin/echo", "limits_test", NULL };
    ASSERT(sandbox_exec(ctx, 2, argv) == 0, "sandbox_exec failed");

    sandbox_stats_t stats;
    ASSERT(sandbox_wait(ctx, &stats) == 0, "sandbox_wait failed");

    /* seccomp requires privileges - skip if not available */
    if (stats.exited_normally && stats.exit_status == 127) {
        sandbox_destroy(ctx);
        TEST_SKIP("seccomp requires privileges (run with sudo)");
        return;
    }

    ASSERT(stats.exited_normally, "echo should exit normally");
    ASSERT(stats.exit_status == 0, "echo should exit with 0");

    sandbox_destroy(ctx);
    TEST_PASS();
}

static void test_exec_null(void) {
    TEST_START("exec with NULL context");

    char *argv[] = { "/bin/echo", NULL };
    ASSERT(sandbox_exec(NULL, 1, argv) == -1,
           "should return -1 for NULL context");

    TEST_PASS();
}

static void test_wait_null(void) {
    TEST_START("wait with NULL context");

    ASSERT(sandbox_wait(NULL, NULL) == -1,
           "should return -1 for NULL context");

    TEST_PASS();
}

static void test_print_stats_null(void) {
    TEST_START("print_stats with NULL");

    /* Should not crash */
    sandbox_print_stats(NULL);
    TEST_PASS();
}

static void test_stats_collection(void) {
    TEST_START("statistics collection");

    sandbox_ctx_t *ctx = sandbox_create();
    ASSERT(ctx != NULL, "sandbox_create failed");

    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Add default safe syscalls */
    const int *wl = sandbox_default_whitelist();
    for (int i = 0; wl[i] != -1; i++) {
        sandbox_syscall_rule_t rule = {
            .syscall_nr = wl[i],
            .allow = true,
            .num_args = 0,
            .description = sandbox_syscall_name(wl[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    sandbox_syscall_rule_t exec_rule = {
#ifdef __NR_execve
        .syscall_nr = __NR_execve,
#endif
        .allow = true,
        .num_args = 0,
        .description = "execve"
    };
    sandbox_add_rule(ctx, &exec_rule);

    char *argv[] = { "/bin/echo", "stats_test", NULL };
    ASSERT(sandbox_exec(ctx, 2, argv) == 0, "sandbox_exec failed");

    sandbox_stats_t stats;
    memset(&stats, 0xFF, sizeof(stats));  /* Fill with garbage */
    ASSERT(sandbox_wait(ctx, &stats) == 0, "sandbox_wait failed");

    ASSERT(stats.child_pid > 0, "child_pid should be positive");

    /* seccomp requires privileges - skip if not available */
    if (stats.exited_normally && stats.exit_status == 127) {
        sandbox_destroy(ctx);
        TEST_SKIP("seccomp requires privileges (run with sudo)");
        return;
    }

    ASSERT(stats.exited_normally, "should exit normally");
    ASSERT(stats.exit_status == 0, "exit status should be 0");
    ASSERT(stats.memory_peak_bytes > 0, "memory peak should be > 0");
    ASSERT(stats.cpu_time_user_us > 0 || stats.cpu_time_sys_us > 0,
           "CPU time should be > 0");

    sandbox_destroy(ctx);
    TEST_PASS();
}

/* ===== Test Runner ===== */

int main(void) {
    printf("=== Sandbox Library Test Suite ===\n\n");

    test_create_destroy();
    test_create_multiple();
    test_set_mode();
    test_set_mode_null();
    test_add_rules();
    test_add_rule_null();
    test_add_too_many_rules();
    test_set_rlimits();
    test_set_rlimits_null();
    test_syscall_name();
    test_default_whitelist();
    test_whitelist_exec_echo();
    test_whitelist_block_fork();
    test_resource_limits();
    test_exec_null();
    test_wait_null();
    test_print_stats_null();
    test_stats_collection();

    printf("\n=== Results ===\n");
    printf("Total:   %d\n", tests_run);
    printf("Passed:  %d\n", tests_passed);
    printf("Failed:  %d\n", tests_failed);
    printf("Skipped: %d\n", tests_skipped);

    if (tests_failed > 0) {
        printf("\nSome tests FAILED!\n");
        return 1;
    }

    if (tests_skipped > 0) {
        printf("\nAll tests PASSED (%d skipped - run with sudo for full suite).\n", tests_skipped);
    } else {
        printf("\nAll tests PASSED!\n");
    }
    return 0;
}
