/*
 * basic_whitelist.c - Basic whitelist sandbox example
 *
 * Demonstrates:
 * - Creating a sandbox with syscall whitelist
 * - Using default safe syscalls
 * - Executing a command inside the sandbox
 * - Collecting execution statistics
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sandbox.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        fprintf(stderr, "Example: %s /bin/echo Hello World\n", argv[0]);
        return 1;
    }

    /* Create sandbox context */
    sandbox_ctx_t *ctx = sandbox_create();
    if (!ctx) {
        fprintf(stderr, "Failed to create sandbox\n");
        return 1;
    }

    /* Set whitelist mode */
    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Add default safe syscalls to whitelist */
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

    /* Also allow execve for the child to run */
    sandbox_syscall_rule_t exec_rule = {
#ifdef __NR_execve
        .syscall_nr = __NR_execve,
#endif
        .allow = true,
        .num_args = 0,
        .description = "execve"
    };
    sandbox_add_rule(ctx, &exec_rule);

    /* Set resource limits */
    sandbox_rlimits_t limits = {
        .file_size_limit = 10 * 1024 * 1024,  /* 10 MB */
        .open_files_limit = 64,
        .stack_size_limit = 8 * 1024 * 1024,   /* 8 MB */
    };
    sandbox_set_rlimits(ctx, &limits);

    printf("[SANDBOX] Starting whitelisted execution: %s\n", argv[1]);

    /* Execute the command */
    if (sandbox_exec(ctx, argc - 1, (char *const *)(argv + 1)) != 0) {
        fprintf(stderr, "Failed to execute in sandbox\n");
        sandbox_destroy(ctx);
        return 1;
    }

    /* Wait for completion and get stats */
    sandbox_stats_t stats;
    if (sandbox_wait(ctx, &stats) != 0) {
        fprintf(stderr, "Failed to wait for sandboxed process\n");
        sandbox_destroy(ctx);
        return 1;
    }

    /* Print results */
    printf("\n");
    sandbox_print_stats(&stats);

    sandbox_destroy(ctx);

    if (stats.exited_normally) {
        return stats.exit_status;
    } else {
        return 128 + stats.exit_signal;
    }
}
