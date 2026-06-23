/*
 * strict_sandbox.c - Example: strict sandbox with minimal syscalls
 *
 * Demonstrates:
 * - Very restrictive whitelist (only read/write/exit)
 * - Tight resource limits
 * - Useful for running untrusted code snippets
 */

#include <stdio.h>
#include <stdlib.h>
#include "sandbox.h"

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <command> [args...]\n", argv[0]);
        return 1;
    }

    sandbox_ctx_t *ctx = sandbox_create();
    if (!ctx) {
        fprintf(stderr, "Failed to create sandbox\n");
        return 1;
    }

    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    /* Minimal whitelist: only essential syscalls */
    int minimal_syscalls[] = {
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

    int count = sizeof(minimal_syscalls) / sizeof(minimal_syscalls[0]);
    for (int i = 0; i < count; i++) {
        if (minimal_syscalls[i] == 0) continue;
        sandbox_syscall_rule_t rule = {
            .syscall_nr = minimal_syscalls[i],
            .allow = true,
            .num_args = 0,
            .description = sandbox_syscall_name(minimal_syscalls[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    /* Very tight resource limits */
    sandbox_rlimits_t limits = {
        .file_size_limit = 1 * 1024 * 1024,     /* 1 MB */
        .open_files_limit = 16,                    /* 16 file descriptors */
        .stack_size_limit = 2 * 1024 * 1024,     /* 2 MB stack */
        .pids_max = 1,                             /* No forking */
    };
    sandbox_set_rlimits(ctx, &limits);

    printf("[SANDBOX] Strict mode. Running: %s\n", argv[1]);

    if (sandbox_exec(ctx, argc - 1, (char *const *)(argv + 1)) != 0) {
        fprintf(stderr, "Failed to execute in sandbox\n");
        sandbox_destroy(ctx);
        return 1;
    }

    sandbox_stats_t stats;
    if (sandbox_wait(ctx, &stats) != 0) {
        fprintf(stderr, "Failed to wait for sandboxed process\n");
        sandbox_destroy(ctx);
        return 1;
    }

    printf("\n");
    sandbox_print_stats(&stats);

    int rc = stats.exited_normally ? stats.exit_status : 128 + stats.exit_signal;

    if (stats.exited_normally && stats.exit_status == 0) {
        printf("[SANDBOX] Program completed successfully under strict sandbox.\n");
    } else {
        printf("[SANDBOX] Program terminated (exit=%d, signal=%d)\n",
               stats.exit_status, stats.exit_signal);
    }

    sandbox_destroy(ctx);
    return rc;
}
