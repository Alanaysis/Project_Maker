#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/resource.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/ptrace.h>
#include <syscall.h>
#include <asm/unistd.h>

#include "sandbox.h"

/* BPF instruction helpers - wrappers that work with array assignment */
static inline struct sock_filter SANDBOX_BPF_STMT_OP(__u16 code, __u32 k) {
    struct sock_filter f = { code, 0, 0, k };
    return f;
}

static inline struct sock_filter SANDBOX_BPF_JUMP_OP(__u16 code, __u32 k, __u8 jt, __u8 jf) {
    struct sock_filter f = { code, jt, jf, k };
    return f;
}

#define SANDBOX_BPF_STMT(code, k) SANDBOX_BPF_STMT_OP(code, k)
#define SANDBOX_BPF_JUMP(code, k, jt, jf) SANDBOX_BPF_JUMP_OP(code, k, jt, jf)

/* Syscall name table for common x86_64 syscalls */
struct syscall_entry {
    int nr;
    const char *name;
};

static const struct syscall_entry syscall_table[] = {
#ifdef __NR_read
    { __NR_read, "read" },
#endif
#ifdef __NR_write
    { __NR_write, "write" },
#endif
#ifdef __NR_open
    { __NR_open, "open" },
#endif
#ifdef __NR_close
    { __NR_close, "close" },
#endif
#ifdef __NR_stat
    { __NR_stat, "stat" },
#endif
#ifdef __NR_fstat
    { __NR_fstat, "fstat" },
#endif
#ifdef __NR_mmap
    { __NR_mmap, "mmap" },
#endif
#ifdef __NR_mprotect
    { __NR_mprotect, "mprotect" },
#endif
#ifdef __NR_munmap
    { __NR_munmap, "munmap" },
#endif
#ifdef __NR_brk
    { __NR_brk, "brk" },
#endif
#ifdef __NR_ioctl
    { __NR_ioctl, "ioctl" },
#endif
#ifdef __NR_access
    { __NR_access, "access" },
#endif
#ifdef __NR_pipe
    { __NR_pipe, "pipe" },
#endif
#ifdef __NR_dup
    { __NR_dup, "dup" },
#endif
#ifdef __NR_dup2
    { __NR_dup2, "dup2" },
#endif
#ifdef __NR_getpid
    { __NR_getpid, "getpid" },
#endif
#ifdef __NR_getuid
    { __NR_getuid, "getuid" },
#endif
#ifdef __NR_getgid
    { __NR_getgid, "getgid" },
#endif
#ifdef __NR_geteuid
    { __NR_geteuid, "geteuid" },
#endif
#ifdef __NR_getegid
    { __NR_getegid, "getegid" },
#endif
#ifdef __NR_fork
    { __NR_fork, "fork" },
#endif
#ifdef __NR_execve
    { __NR_execve, "execve" },
#endif
#ifdef __NR_exit
    { __NR_exit, "exit" },
#endif
#ifdef __NR_exit_group
    { __NR_exit_group, "exit_group" },
#endif
#ifdef __NR_mkdir
    { __NR_mkdir, "mkdir" },
#endif
#ifdef __NR_rmdir
    { __NR_rmdir, "rmdir" },
#endif
#ifdef __NR_unlink
    { __NR_unlink, "unlink" },
#endif
#ifdef __NR_rename
    { __NR_rename, "rename" },
#endif
#ifdef __NR_getcwd
    { __NR_getcwd, "getcwd" },
#endif
#ifdef __NR_chdir
    { __NR_chdir, "chdir" },
#endif
#ifdef __NR_openat
    { __NR_openat, "openat" },
#endif
#ifdef __NR_unlinkat
    { __NR_unlinkat, "unlinkat" },
#endif
#ifdef __NR_futex
    { __NR_futex, "futex" },
#endif
#ifdef __NR_set_tid_address
    { __NR_set_tid_address, "set_tid_address" },
#endif
#ifdef __NR_clock_gettime
    { __NR_clock_gettime, "clock_gettime" },
#endif
#ifdef __NR_rt_sigaction
    { __NR_rt_sigaction, "rt_sigaction" },
#endif
#ifdef __NR_rt_sigprocmask
    { __NR_rt_sigprocmask, "rt_sigprocmask" },
#endif
#ifdef __NR_arch_prctl
    { __NR_arch_prctl, "arch_prctl" },
#endif
#ifdef __NR_fcntl
    { __NR_fcntl, "fcntl" },
#endif
#ifdef __NR_lseek
    { __NR_lseek, "lseek" },
#endif
    { -1, NULL }
};

/* Default safe syscall whitelist */
static const int default_whitelist[] = {
#ifdef __NR_read
    __NR_read,
#endif
#ifdef __NR_write
    __NR_write,
#endif
#ifdef __NR_close
    __NR_close,
#endif
#ifdef __NR_fstat
    __NR_fstat,
#endif
#ifdef __NR_mmap
    __NR_mmap,
#endif
#ifdef __NR_mprotect
    __NR_mprotect,
#endif
#ifdef __NR_munmap
    __NR_munmap,
#endif
#ifdef __NR_brk
    __NR_brk,
#endif
#ifdef __NR_access
    __NR_access,
#endif
#ifdef __NR_dup
    __NR_dup,
#endif
#ifdef __NR_dup2
    __NR_dup2,
#endif
#ifdef __NR_getpid
    __NR_getpid,
#endif
#ifdef __NR_getuid
    __NR_getuid,
#endif
#ifdef __NR_getgid
    __NR_getgid,
#endif
#ifdef __NR_geteuid
    __NR_geteuid,
#endif
#ifdef __NR_getegid
    __NR_getegid,
#endif
#ifdef __NR_exit
    __NR_exit,
#endif
#ifdef __NR_exit_group
    __NR_exit_group,
#endif
#ifdef __NR_futex
    __NR_futex,
#endif
#ifdef __NR_set_tid_address
    __NR_set_tid_address,
#endif
#ifdef __NR_clock_gettime
    __NR_clock_gettime,
#endif
#ifdef __NR_rt_sigaction
    __NR_rt_sigaction,
#endif
#ifdef __NR_rt_sigprocmask
    __NR_rt_sigprocmask,
#endif
#ifdef __NR_arch_prctl
    __NR_arch_prctl,
#endif
#ifdef __NR_fcntl
    __NR_fcntl,
#endif
    -1  /* sentinel */
};

/* Internal sandbox context */
struct sandbox_ctx {
    sandbox_mode_t mode;
    sandbox_syscall_rule_t rules[SANDBOX_MAX_SYSCALL_RULES];
    int num_rules;
    sandbox_rlimits_t limits;
    bool limits_set;
    pid_t child_pid;
    sandbox_stats_t stats;
};

/* Public API implementation */

sandbox_ctx_t *sandbox_create(void) {
    sandbox_ctx_t *ctx = calloc(1, sizeof(sandbox_ctx_t));
    if (!ctx) {
        return NULL;
    }
    ctx->mode = SANDBOX_MODE_WHITELIST;
    ctx->num_rules = 0;
    ctx->limits_set = false;
    ctx->child_pid = -1;
    return ctx;
}

void sandbox_destroy(sandbox_ctx_t *ctx) {
    if (ctx) {
        /* Free description strings (they are owned by caller normally,
           but we don't strdup them, so nothing to free here) */
        free(ctx);
    }
}

int sandbox_set_mode(sandbox_ctx_t *ctx, sandbox_mode_t mode) {
    if (!ctx) return -1;
    ctx->mode = mode;
    return 0;
}

int sandbox_add_rule(sandbox_ctx_t *ctx, const sandbox_syscall_rule_t *rule) {
    if (!ctx || !rule) return -1;
    if (ctx->num_rules >= SANDBOX_MAX_SYSCALL_RULES) {
        fprintf(stderr, "sandbox: maximum number of rules reached (%d)\n",
                SANDBOX_MAX_SYSCALL_RULES);
        return -1;
    }
    ctx->rules[ctx->num_rules] = *rule;
    ctx->num_rules++;
    return 0;
}

int sandbox_set_rlimits(sandbox_ctx_t *ctx, const sandbox_rlimits_t *limits) {
    if (!ctx || !limits) return -1;
    ctx->limits = *limits;
    ctx->limits_set = true;
    return 0;
}

const char *sandbox_syscall_name(int syscall_nr) {
    for (int i = 0; syscall_table[i].name != NULL; i++) {
        if (syscall_table[i].nr == syscall_nr) {
            return syscall_table[i].name;
        }
    }
    return "unknown";
}

const int *sandbox_default_whitelist(void) {
    return default_whitelist;
}

/* Build BPF program for seccomp filtering */
static struct sock_filter *build_bpf_program(sandbox_ctx_t *ctx, size_t *out_len) {
    /*
     * BPF program structure:
     * - Load syscall number
     * - For each rule: compare and jump to ALLOW or KILL
     * - Default action at end
     *
     * We use a linear scan approach for simplicity.
     * Each rule needs approximately 3-4 BPF instructions.
     *
     * Worst case instruction count:
     * - 1 (load arch) + 1 (arch check) + 1 (load nr) + rules * 4 + 1 (default) + 1 (allow)
     */
    int max_insn = 3 + ctx->num_rules * 4 + 2 + 10;  /* extra margin */
    struct sock_filter *prog = calloc(max_insn, sizeof(struct sock_filter));
    if (!prog) return NULL;

    int pc = 0;

    /* Load architecture and verify */
    prog[pc++] = SANDBOX_BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                           offsetof(struct seccomp_data, arch));
    prog[pc++] = SANDBOX_BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0);
    prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL);

    /* Load syscall number */
    prog[pc++] = SANDBOX_BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                           offsetof(struct seccomp_data, nr));

    /*
     * For whitelist mode: if syscall matches a rule that allows it, allow.
     * If no rule matches, kill.
     * For blacklist mode: if syscall matches a rule that blocks it, kill.
     * If no rule matches, allow.
     */

    if (ctx->mode == SANDBOX_MODE_WHITELIST) {
        /* In whitelist mode, each "allow" rule jumps to ALLOW */
        for (int i = 0; i < ctx->num_rules; i++) {
            const sandbox_syscall_rule_t *rule = &ctx->rules[i];
            if (rule->allow) {
                /* Jump forward to ALLOW if match; skip to next rule if not */
                int jump_to_allow = ctx->num_rules - i + 1;  /* instructions to skip */
                prog[pc++] = SANDBOX_BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                       (uint32_t)rule->syscall_nr, jump_to_allow, 0);
            } else {
                /* Blocked syscall - jump to KILL */
                prog[pc++] = SANDBOX_BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                       (uint32_t)rule->syscall_nr, 0, 0);
                /* Kill immediately */
                prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL);
            }
        }
        /* Default: kill (whitelist) */
        prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL);
        /* Allow */
        prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW);
    } else {
        /* Blacklist mode */
        for (int i = 0; i < ctx->num_rules; i++) {
            const sandbox_syscall_rule_t *rule = &ctx->rules[i];
            if (!rule->allow) {
                int jump_to_kill = ctx->num_rules - i + 1;
                prog[pc++] = SANDBOX_BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                       (uint32_t)rule->syscall_nr, jump_to_kill, 0);
            } else {
                /* Allowed syscall - just skip */
                prog[pc++] = SANDBOX_BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K,
                                       (uint32_t)rule->syscall_nr, 0, 0);
            }
        }
        /* Default: allow (blacklist) */
        prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW);
        /* Kill */
        prog[pc++] = SANDBOX_BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL);
    }

    *out_len = pc;
    return prog;
}

/* Apply seccomp BPF filter */
static int apply_seccomp(sandbox_ctx_t *ctx) {
    size_t prog_len;
    struct sock_filter *prog = build_bpf_program(ctx, &prog_len);
    if (!prog) {
        fprintf(stderr, "sandbox: failed to build BPF program\n");
        return -1;
    }

    struct sock_fprog fprog = {
        .len = (unsigned short)prog_len,
        .filter = prog,
    };

    /* Enable NO_NEW_PRIVS to allow unprivileged seccomp */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        fprintf(stderr, "sandbox: prctl(NO_NEW_PRIVS) failed: %s\n",
                strerror(errno));
        free(prog);
        return -1;
    }

    /* Install the BPF filter */
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog, 0, 0) != 0) {
        fprintf(stderr, "sandbox: prctl(SECCOMP) failed: %s\n",
                strerror(errno));
        free(prog);
        return -1;
    }

    free(prog);
    return 0;
}

/* Apply POSIX resource limits (rlimit) */
static int apply_rlimits(sandbox_ctx_t *ctx) {
    if (!ctx->limits_set) return 0;

    const sandbox_rlimits_t *lim = &ctx->limits;

    /* File size limit */
    if (lim->file_size_limit > 0) {
        struct rlimit rl = { .rlim_cur = lim->file_size_limit, .rlim_max = lim->file_size_limit };
        if (setrlimit(RLIMIT_FSIZE, &rl) != 0) {
            fprintf(stderr, "sandbox: setrlimit(FSIZE) failed: %s\n", strerror(errno));
        }
    }

    /* Stack size limit */
    if (lim->stack_size_limit > 0) {
        struct rlimit rl = { .rlim_cur = lim->stack_size_limit, .rlim_max = lim->stack_size_limit };
        if (setrlimit(RLIMIT_STACK, &rl) != 0) {
            fprintf(stderr, "sandbox: setrlimit(STACK) failed: %s\n", strerror(errno));
        }
    }

    /* Open files limit */
    if (lim->open_files_limit > 0) {
        struct rlimit rl = { .rlim_cur = lim->open_files_limit, .rlim_max = lim->open_files_limit };
        if (setrlimit(RLIMIT_NOFILE, &rl) != 0) {
            fprintf(stderr, "sandbox: setrlimit(NOFILE) failed: %s\n", strerror(errno));
        }
    }

    /* Process limit (RLIMIT_NPROC) */
    if (lim->pids_max > 0) {
        struct rlimit rl = { .rlim_cur = lim->pids_max, .rlim_max = lim->pids_max };
        if (setrlimit(RLIMIT_NPROC, &rl) != 0) {
            fprintf(stderr, "sandbox: setrlimit(NPROC) failed: %s\n", strerror(errno));
        }
    }

    return 0;
}

/* Print a blocked syscall (called from the child via signal handler) */
static void sigsys_handler(int sig, siginfo_t *info, void *ucontext) {
    (void)sig;
    (void)ucontext;
    int syscall_nr = info->si_syscall;
    fprintf(stderr, "[SANDBOX BLOCKED] syscall: %s (%d)\n",
            sandbox_syscall_name(syscall_nr), syscall_nr);
    _exit(128 + sig);
}

/* Install SIGSYS handler for blocked syscalls (TRAP mode) */
static void install_sigsys_handler(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = sigsys_handler;
    sa.sa_flags = SA_SIGINFO;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSYS, &sa, NULL);
}

/* Child process: apply sandbox restrictions and exec */
static int sandbox_child(sandbox_ctx_t *ctx, int argc, char *const argv[]) {
    /* Apply resource limits first (before seccomp) */
    if (apply_rlimits(ctx) != 0) {
        fprintf(stderr, "sandbox: failed to apply resource limits\n");
        _exit(127);
    }

    /* Install SIGSYS handler for better error messages */
    install_sigsys_handler();

    /* Apply seccomp filter */
    if (apply_seccomp(ctx) != 0) {
        fprintf(stderr, "sandbox: failed to apply seccomp filter\n");
        _exit(127);
    }

    /* Build argv for execvp */
    char **exec_argv = calloc(argc + 1, sizeof(char *));
    if (!exec_argv) {
        _exit(127);
    }
    for (int i = 0; i < argc; i++) {
        exec_argv[i] = argv[i];
    }
    exec_argv[argc] = NULL;

    /* Execute the target program */
    execvp(exec_argv[0], exec_argv);

    /* If execvp returns, it failed */
    fprintf(stderr, "sandbox: execvp(%s) failed: %s\n",
            exec_argv[0], strerror(errno));
    free(exec_argv);
    _exit(127);
}

int sandbox_exec(sandbox_ctx_t *ctx, int argc, char *const argv[]) {
    if (!ctx || argc <= 0 || !argv) return -1;

    pid_t pid = fork();
    if (pid < 0) {
        fprintf(stderr, "sandbox: fork failed: %s\n", strerror(errno));
        return -1;
    }

    if (pid == 0) {
        /* Child */
        sandbox_child(ctx, argc, argv);
        /* Should not reach here */
        _exit(127);
    }

    /* Parent */
    ctx->child_pid = pid;
    ctx->stats.child_pid = pid;
    return 0;
}

int sandbox_wait(sandbox_ctx_t *ctx, sandbox_stats_t *stats) {
    if (!ctx || ctx->child_pid < 0) return -1;

    int status;
    struct rusage usage;

    pid_t result = wait4(ctx->child_pid, &status, 0, &usage);
    if (result < 0) {
        fprintf(stderr, "sandbox: wait4 failed: %s\n", strerror(errno));
        return -1;
    }

    /* Collect statistics */
    ctx->stats.cpu_time_user_us = (uint64_t)usage.ru_utime.tv_sec * 1000000 +
                                   (uint64_t)usage.ru_utime.tv_usec;
    ctx->stats.cpu_time_sys_us = (uint64_t)usage.ru_stime.tv_sec * 1000000 +
                                  (uint64_t)usage.ru_stime.tv_usec;
    ctx->stats.memory_peak_bytes = (uint64_t)usage.ru_maxrss * 1024;  /* ru_maxrss is in KB */

    if (WIFEXITED(status)) {
        ctx->stats.exited_normally = true;
        ctx->stats.exit_status = WEXITSTATUS(status);
        ctx->stats.exit_signal = 0;
    } else if (WIFSIGNALED(status)) {
        ctx->stats.exited_normally = false;
        ctx->stats.exit_status = -1;
        ctx->stats.exit_signal = WTERMSIG(status);
    }

    if (stats) {
        *stats = ctx->stats;
    }

    return 0;
}

void sandbox_print_stats(const sandbox_stats_t *stats) {
    if (!stats) return;

    printf("=== Sandbox Statistics ===\n");
    printf("Child PID:        %d\n", stats->child_pid);
    if (stats->exited_normally) {
        printf("Exit Status:      %d\n", stats->exit_status);
    } else {
        printf("Exit Signal:      %d (%s)\n",
               stats->exit_signal, strsignal(stats->exit_signal));
    }
    printf("Peak Memory:      %lu KB\n", stats->memory_peak_bytes / 1024);
    printf("CPU Time (user):  %lu.%06lu s\n",
           stats->cpu_time_user_us / 1000000,
           stats->cpu_time_user_us % 1000000);
    printf("CPU Time (sys):   %lu.%06lu s\n",
           stats->cpu_time_sys_us / 1000000,
           stats->cpu_time_sys_us % 1000000);
    printf("========================\n");
}
