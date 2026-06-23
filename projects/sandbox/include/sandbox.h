#ifndef SANDBOX_H
#define SANDBOX_H

#include <stdbool.h>
#include <stdint.h>
#include <sys/types.h>

/* Maximum number of syscall rules */
#define SANDBOX_MAX_SYSCALL_RULES 64
#define SANDBOX_MAX_SYSCALL_ARGS 6

/* Sandbox operation modes */
typedef enum {
    SANDBOX_MODE_WHITELIST,  /* Only allow listed syscalls */
    SANDBOX_MODE_BLACKLIST   /* Block listed syscalls, allow others */
} sandbox_mode_t;

/* Argument comparison operators */
typedef enum {
    SANDBOX_CMP_EQ,    /* Equal */
    SANDBOX_CMP_NE,    /* Not equal */
    SANDBOX_CMP_GT,    /* Greater than */
    SANDBOX_CMP_GE,    /* Greater or equal */
    SANDBOX_CMP_LT,    /* Less than */
    SANDBOX_CMP_LE     /* Less or equal */
} sandbox_cmp_t;

/* Single syscall argument constraint */
typedef struct {
    uint32_t arg_index;        /* Argument index (0-5) */
    sandbox_cmp_t op;          /* Comparison operator */
    uint64_t value;            /* Value to compare against */
    bool enabled;              /* Whether this constraint is active */
} sandbox_arg_constraint_t;

/* Syscall filter rule */
typedef struct {
    int syscall_nr;            /* Syscall number, -1 = wildcard */
    bool allow;                /* true = allow, false = block */
    sandbox_arg_constraint_t args[SANDBOX_MAX_SYSCALL_ARGS];
    int num_args;              /* Number of active arg constraints */
    const char *description;   /* Human-readable description */
} sandbox_syscall_rule_t;

/* Resource limits configuration */
typedef struct {
    /* Memory limits (in bytes, 0 = no limit) */
    uint64_t memory_limit;
    uint64_t memory_swap_limit;

    /* CPU limits */
    uint64_t cpu_shares;       /* Relative CPU weight (1024 = default) */
    uint64_t cpu_quota_us;     /* CPU quota in microseconds per period */
    uint64_t cpu_period_us;    /* CPU period in microseconds */

    /* Process limits */
    uint64_t pids_max;         /* Maximum number of processes */

    /* File size limit (in bytes, 0 = no limit) */
    uint64_t file_size_limit;

    /* Stack size limit (in bytes) */
    uint64_t stack_size_limit;

    /* Open files limit */
    uint64_t open_files_limit;
} sandbox_rlimits_t;

/* Sandbox statistics */
typedef struct {
    uint64_t syscalls_allowed;
    uint64_t syscalls_blocked;
    uint64_t syscalls_total;
    uint64_t memory_peak_bytes;
    uint64_t cpu_time_user_us;
    uint64_t cpu_time_sys_us;
    pid_t child_pid;
    int exit_status;
    int exit_signal;
    bool exited_normally;
} sandbox_stats_t;

/* Sandbox context (opaque) */
typedef struct sandbox_ctx sandbox_ctx_t;

/* Core API */

/**
 * Create a new sandbox context.
 * @return New sandbox context, or NULL on failure.
 */
sandbox_ctx_t *sandbox_create(void);

/**
 * Destroy a sandbox context and free resources.
 * @param ctx Sandbox context to destroy.
 */
void sandbox_destroy(sandbox_ctx_t *ctx);

/**
 * Set sandbox mode (whitelist or blacklist).
 * @param ctx Sandbox context.
 * @param mode Operation mode.
 * @return 0 on success, -1 on failure.
 */
int sandbox_set_mode(sandbox_ctx_t *ctx, sandbox_mode_t mode);

/**
 * Add a syscall filter rule.
 * @param ctx Sandbox context.
 * @param rule Pointer to the rule to add.
 * @return 0 on success, -1 on failure.
 */
int sandbox_add_rule(sandbox_ctx_t *ctx, const sandbox_syscall_rule_t *rule);

/**
 * Set resource limits.
 * @param ctx Sandbox context.
 * @param limits Pointer to limits configuration.
 * @return 0 on success, -1 on failure.
 */
int sandbox_set_rlimits(sandbox_ctx_t *ctx, const sandbox_rlimits_t *limits);

/**
 * Execute a command inside the sandbox.
 * The sandbox will fork and apply all filters to the child process.
 * @param ctx Sandbox context.
 * @param argc Argument count.
 * @param argv Argument vector (NULL-terminated).
 * @return 0 on success, -1 on failure.
 */
int sandbox_exec(sandbox_ctx_t *ctx, int argc, char *const argv[]);

/**
 * Wait for the sandboxed process to finish and collect stats.
 * @param ctx Sandbox context.
 * @param stats Output statistics structure.
 * @return 0 on success, -1 on failure.
 */
int sandbox_wait(sandbox_ctx_t *ctx, sandbox_stats_t *stats);

/**
 * Get a human-readable name for a syscall number.
 * @param syscall_nr Syscall number.
 * @return String name of the syscall, or "unknown".
 */
const char *sandbox_syscall_name(int syscall_nr);

/**
 * Get the default whitelist of commonly safe syscalls.
 * @return Static array of syscall numbers, terminated by -1.
 */
const int *sandbox_default_whitelist(void);

/* Utility: Print sandbox statistics */
void sandbox_print_stats(const sandbox_stats_t *stats);

#endif /* SANDBOX_H */
