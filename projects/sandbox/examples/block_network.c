/*
 * block_network.c - Example: block network syscalls
 *
 * Demonstrates:
 * - Whitelist mode with network syscalls blocked
 * - The child can read/write files but cannot create sockets
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

    /* Add safe syscalls */
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

    /* Explicitly block network syscalls */
    int network_syscalls[] = {
#ifdef __NR_socket
        __NR_socket,
#endif
#ifdef __NR_connect
        __NR_connect,
#endif
#ifdef __NR_bind
        __NR_bind,
#endif
#ifdef __NR_listen
        __NR_listen,
#endif
#ifdef __NR_accept
        __NR_accept,
#endif
#ifdef __NR_sendto
        __NR_sendto,
#endif
#ifdef __NR_recvfrom
        __NR_recvfrom,
#endif
    };

    int num_blocked = sizeof(network_syscalls) / sizeof(network_syscalls[0]);
    for (int i = 0; i < num_blocked; i++) {
        if (network_syscalls[i] == 0) continue;
        sandbox_syscall_rule_t rule = {
            .syscall_nr = network_syscalls[i],
            .allow = false,
            .num_args = 0,
            .description = sandbox_syscall_name(network_syscalls[i])
        };
        sandbox_add_rule(ctx, &rule);
    }

    /* Set limits */
    sandbox_rlimits_t limits = {
        .file_size_limit = 5 * 1024 * 1024,
        .open_files_limit = 32,
    };
    sandbox_set_rlimits(ctx, &limits);

    printf("[SANDBOX] Network access blocked. Running: %s\n", argv[1]);

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

    sandbox_destroy(ctx);

    if (stats.exited_normally) {
        return stats.exit_status;
    } else {
        return 128 + stats.exit_signal;
    }
}
