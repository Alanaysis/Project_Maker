/**
 * low_power.c - Embedded Low-Power Design Framework Implementation
 *
 * 嵌入式低功耗设计框架实现
 *
 * This file implements the core low-power management framework including:
 * 本文件实现核心低功耗管理框架，包括：
 * - Power mode definitions and transitions 功耗模式定义和转换
 * - Clock gating management 时钟门控管理
 * - Peripheral power control 外设电源控制
 * - Wake-up source management 唤醒源管理
 * - DVFS (Dynamic Voltage Frequency Scaling) DVFS（动态电压频率调节）
 * - Power monitoring and energy profiling 功耗监测和能耗分析
 *
 * Low-Power Design Concepts / 低功耗设计概念:
 * =============================================
 *
 * 1. Power Modes / 功耗模式:
 *    - Active: Full performance, highest power 全性能，最高功耗
 *    - Idle: CPU halted, peripherals active CPU暂停，外设活动
 *    - Sleep: Clocks gated, RAM retained 时钟门控，RAM保留
 *    - Deep Sleep: Minimal power, RAM lost 最小功耗，RAM丢失
 *    - Standby: RTC running, fast wake 实时时钟运行，快速唤醒
 *    - Off: No power, requires reset 无电源，需要复位
 *
 * 2. Clock Gating / 时钟门控:
 *    - Most effective low-power technique 最有效的低功耗技术
 *    - Reduces dynamic power without functional impact 减少动态功耗不影响功能
 *    - P_dyn = alpha * C * V^2 * f, reducing alpha saves power 减少alpha可省电
 *
 * 3. DVFS / 动态电压频率调节:
 *    - Voltage and frequency are coupled 电压和频率耦合
 *    - Lower voltage = less dynamic power (quadratic effect) 更低电压=更少动态功耗(平方效应)
 *    - Lower frequency = less dynamic power (linear effect) 更低频率=更少动态功耗(线性效应)
 *    - Minimum voltage depends on max required frequency 最低电压取决于最大需求频率
 *
 * 4. Power Gating / 电源门控:
 *    - Cuts power to entire blocks 切断整个模块的电源
 *    - Deeper savings than clock gating 比时钟门控更深的节省
 *    - Higher wake-up latency 更高的唤醒延迟
 *
 * 5. Wake-up Sources / 唤醒源:
 *    - Must be configured before entering sleep 进入睡眠前必须配置
 *    - Different sources have different wake-up latencies 不同源有不同的唤醒延迟
 *    - RTC and pin interrupts are common wake-up sources 实时时钟和引脚中断是常见的唤醒源
 */

#include "low_power.h"
#include <string.h>
#include <stdlib.h>

/* ======================================================================
 * Internal helper functions / 内部辅助函数
 * ====================================================================== */

/**
 * Simulate power mode transition timing
 * 模拟功耗模式转换时序
 *
 * Different modes have different transition latencies due to:
 * 不同模式有不同的转换延迟，因为：
 * - Context save/restore time 上下文保存/恢复时间
 * - Clock stabilization time 时钟稳定时间
 * - Voltage ramp time 电压爬升时间
 * - Peripheral initialization time 外设初始化时间
 */
static uint32_t simulate_mode_latency(power_mode_t from, power_mode_t to) {
    /* Deeper transitions take longer */
    /* 更深的转换需要更长时间 */
    uint32_t latency_us = 0;

    if (from == to) {
        return 0;
    }

    /* Calculate minimum of source and target modes */
    /* 计算源和目标模式的最小值 */
    int from_depth = from;
    int to_depth = to;
    int max_depth = (from_depth > to_depth) ? from_depth : to_depth;

    /* Base latency for entering sleep states */
    /* 进入睡眠状态的基础延迟 */
    switch (to) {
        case POWER_MODE_IDLE:
            latency_us = 2;           /* 2 microseconds - very fast */
            break;
        case POWER_MODE_SLEEP:
            latency_us = 10;          /* 10 microseconds */
            break;
        case POWER_MODE_DEEP_SLEEP:
            latency_us = 100;         /* 100 microseconds */
            break;
        case POWER_MODE_STANDBY:
            latency_us = 5;           /* 5 microseconds */
            break;
        case POWER_MODE_OFF:
            latency_us = 10000;       /* 10ms - requires full reset */
            break;
        default:
            latency_us = 1;
            break;
    }

    /* Add transition penalty for deeper transitions */
    /* 为更深的转换添加转换惩罚 */
    latency_us += max_depth * 5;

    return latency_us;
}

/**
 * Simulate current draw for a given power mode
 * 模拟给定功耗模式的电流消耗
 *
 * Current draw depends on:
 * 电流消耗取决于：
 * - Base silicon leakage 基础硅漏电流
 * - Active peripherals 活动外设
 * - Clock frequency 时钟频率
 * - Supply voltage 供电电压
 * - RAM retention state RAM保留状态
 */
static uint32_t simulate_current(power_mode_t mode, uint32_t voltage_mv,
                                  uint32_t clock_khz, clock_gate_state_t *clocks,
                                  peripheral_power_state_t *periph) {
    uint32_t current_uA = 0;

    /* Base silicon leakage current - varies with voltage and temperature */
    /* 基础硅漏电流 - 随电压和温度变化 */
    current_uA = (voltage_mv / 3300.0f) * 5;  /* ~5uA at 3.3V base */

    switch (mode) {
        case POWER_MODE_ACTIVE:
            /* Full current: core + all active peripherals */
            /* 完整电流：核心 + 所有活动外设 */
            current_uA += (clock_khz / 1000) * 20;  /* Core current scales with freq */
            current_uA += clocks->estimated_savings_uA ? (100 - clocks->estimated_savings_uA / 10) : 100;
            break;

        case POWER_MODE_IDLE:
            /* CPU halted, peripherals still drawing */
            /* CPU暂停，外设仍在耗电 */
            current_uA += 50;  /* Idle core current */
            current_uA += clocks->estimated_savings_uA ? (80 - clocks->estimated_savings_uA / 10) : 80;
            break;

        case POWER_MODE_SLEEP:
            /* Clocks gated, RAM retained */
            /* 时钟门控，RAM保留 */
            current_uA += 5;   /* Very low core current */
            current_uA += clocks->estimated_savings_uA ? (50 - clocks->estimated_savings_uA / 10) : 50;
            break;

        case POWER_MODE_DEEP_SLEEP:
            /* Minimal power, RAM lost */
            /* 最小功耗，RAM丢失 */
            current_uA += 1;   /* Near-zero core current */
            if (!periph->powered[POWER_DOMAIN_PERIPH_CORE]) {
                current_uA /= 2;  /* Core powered down */
            }
            break;

        case POWER_MODE_STANDBY:
            /* RTC running, fast wake */
            /* 实时时钟运行，快速唤醒 */
            current_uA += 10;  /* RTC current */
            break;

        case POWER_MODE_OFF:
            current_uA = 0;
            break;

        default:
            current_uA = 50;
            break;
    }

    return current_uA;
}

/* ======================================================================
 * Initialization / 初始化
 * ====================================================================== */

int lp_init(low_power_context_t *ctx) {
    if (!ctx) {
        return -1;
    }

    memset(ctx, 0, sizeof(low_power_context_t));

    /* Set default active mode configuration */
    /* 设置默认活动模式配置 */
    ctx->current_mode.mode = POWER_MODE_ACTIVE;
    ctx->current_mode.voltage_mv = 3300;      /* 3.3V default 默认3.3V */
    ctx->current_mode.clock_freq_khz = 72000; /* 72 MHz default 默认72MHz */
    ctx->current_mode.ram_retention = true;
    ctx->current_mode.rtc_running = false;
    ctx->current_mode.backup_domain_powered = false;
    ctx->current_mode.wake_latency_us = 1;
    ctx->current_mode.current_uA = 0;

    /* Initialize clock gating - all enabled by default */
    /* 初始化时钟门控 - 默认全部使能 */
    memset(ctx->clock_gating.enabled, 1, sizeof(ctx->clock_gating.enabled));
    ctx->clock_gating.gate_count = 0;
    ctx->clock_gating.active_count = CLOCK_PERIPH_MAX;
    ctx->clock_gating.estimated_savings_uA = 0;

    /* Initialize peripheral power - all domains powered by default */
    /* 初始化外设电源 - 默认所有域供电 */
    memset(ctx->periph_power.powered, 1, sizeof(ctx->periph_power.powered));
    ctx->periph_power.active_domains = (1 << POWER_DOMAIN_PERIPH_MAX) - 1;
    ctx->periph_power.power_reduction_pct = 0;

    /* Initialize wake-up manager - no sources enabled by default */
    /* 初始化唤醒管理器 - 默认无使能源 */
    memset(ctx->wakeup_mgr.sources, 0, sizeof(ctx->wakeup_mgr.sources));
    ctx->wakeup_mgr.last_wakeup = WAKEUP_SOURCE_NONE;
    ctx->wakeup_mgr.wakeup_count = 0;

    /* Initialize DVFS with default operating points */
    /* 使用默认工作点初始化DVFS */
    ctx->dvfs.current_point.voltage_mv = 3300;
    ctx->dvfs.current_point.frequency_khz = 72000;
    ctx->dvfs.current_point.current_uA = 20000;
    ctx->dvfs.current_point.power_uW = 66000;
    ctx->dvfs.current_point.is_valid = true;
    ctx->dvfs.policy = DVFS_POLICY_BALANCED;
    ctx->dvfs.num_points = 0;

    /* Initialize power monitor buffer */
    /* 初始化功耗监测缓冲区 */
    ctx->power_monitor.head = 0;
    ctx->power_monitor.tail = 0;
    ctx->power_monitor.count = 0;
    ctx->power_monitor.is_full = false;

    /* Initialize energy profile */
    /* 初始化能耗分析 */
    memset(&ctx->profile, 0, sizeof(energy_profile_t));

    ctx->is_initialized = true;

    return 0;
}

/* ======================================================================
 * Power Mode Management / 功耗模式管理
 * ====================================================================== */

void lp_get_mode_config(power_mode_t mode, power_mode_config_t *config) {
    if (!config) return;

    memset(config, 0, sizeof(power_mode_config_t));
    config->mode = mode;

    switch (mode) {
        case POWER_MODE_ACTIVE:
            config->voltage_mv = 3300;
            config->clock_freq_khz = 72000;
            config->ram_retention = true;
            config->rtc_running = true;
            config->backup_domain_powered = true;
            config->wake_latency_us = 1;
            config->current_uA = 20000;
            break;

        case POWER_MODE_IDLE:
            config->voltage_mv = 3300;
            config->clock_freq_khz = 72000;
            config->ram_retention = true;
            config->rtc_running = true;
            config->backup_domain_powered = true;
            config->wake_latency_us = 2;
            config->current_uA = 15000;
            break;

        case POWER_MODE_SLEEP:
            config->voltage_mv = 3300;
            config->clock_freq_khz = 0;
            config->ram_retention = true;
            config->rtc_running = true;
            config->backup_domain_powered = false;
            config->wake_latency_us = 10;
            config->current_uA = 2000;
            break;

        case POWER_MODE_DEEP_SLEEP:
            config->voltage_mv = 0;
            config->clock_freq_khz = 0;
            config->ram_retention = false;
            config->rtc_running = false;
            config->backup_domain_powered = true;
            config->wake_latency_us = 100;
            config->current_uA = 10;
            break;

        case POWER_MODE_STANDBY:
            config->voltage_mv = 3300;
            config->clock_freq_khz = 0;
            config->ram_retention = true;
            config->rtc_running = true;
            config->backup_domain_powered = true;
            config->wake_latency_us = 5;
            config->current_uA = 500;
            break;

        case POWER_MODE_OFF:
            config->voltage_mv = 0;
            config->clock_freq_khz = 0;
            config->ram_retention = false;
            config->rtc_running = false;
            config->backup_domain_powered = false;
            config->wake_latency_us = 10000;
            config->current_uA = 0;
            break;

        default:
            config->voltage_mv = 3300;
            config->clock_freq_khz = 72000;
            config->current_uA = 20000;
            break;
    }
}

int lp_switch_mode(low_power_context_t *ctx, power_mode_t target) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    power_mode_t current = ctx->current_mode.mode;

    /* Validate mode transition */
    /* 验证模式转换 */
    if (target < POWER_MODE_ACTIVE || target > POWER_MODE_OFF) {
        return -1;
    }

    /* Simulate mode transition */
    /* 模拟模式转换 */
    uint32_t latency = simulate_mode_latency(current, target);

    /* Save current state for profiling */
    /* 保存当前状态用于分析 */
    uint32_t old_voltage = ctx->current_mode.voltage_mv;
    uint32_t old_freq = ctx->current_mode.clock_freq_khz;

    /* Get target mode configuration */
    /* 获取目标模式配置 */
    power_mode_config_t target_config;
    lp_get_mode_config(target, &target_config);

    /* Apply DVFS scaling if voltage/frequency changes */
    /* 如果电压/频率变化则应用DVFS缩放 */
    if (target_config.voltage_mv != old_voltage ||
        target_config.clock_freq_khz != old_freq) {
        /* In real hardware, voltage must be scaled BEFORE frequency
         * to avoid timing violations. On exit, frequency first, then voltage.
         * 在真实硬件中，电压必须在频率之前缩放以避免时序违规。
         * 退出时，先频率后电压。 */
        ctx->dvfs.transition_count++;
    }

    /* Update context */
    /* 更新上下文 */
    ctx->current_mode = target_config;

    /* Update wake latency based on transition */
    /* 根据转换更新唤醒延迟 */
    ctx->current_mode.wake_latency_us = latency;

    /* Update current estimate */
    /* 更新电流估计 */
    ctx->current_mode.current_uA = simulate_current(
        target, target_config.voltage_mv,
        target_config.clock_freq_khz,
        &ctx->clock_gating, &ctx->periph_power
    );

    /* Update energy profile */
    /* 更新能耗分析 */
    ctx->profile.mode_switch_count++;

    /* Record power sample */
    /* 记录功耗采样 */
    lp_record_sample(ctx, ctx->current_mode.current_uA,
                     ctx->current_mode.voltage_mv, 0);

    return 0;
}

const char *lp_mode_name(power_mode_t mode) {
    switch (mode) {
        case POWER_MODE_ACTIVE:   return "ACTIVE";
        case POWER_MODE_IDLE:     return "IDLE";
        case POWER_MODE_SLEEP:    return "SLEEP";
        case POWER_MODE_DEEP_SLEEP: return "DEEP_SLEEP";
        case POWER_MODE_STANDBY:  return "STANDBY";
        case POWER_MODE_OFF:      return "OFF";
        default:                  return "UNKNOWN";
    }
}

/* ======================================================================
 * Clock Gating / 时钟门控
 * ====================================================================== */

int lp_clock_gate(low_power_context_t *ctx, clock_periph_t periph, bool enable) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    if (periph >= CLOCK_PERIPH_MAX) {
        return -1;
    }

    bool was_enabled = ctx->clock_gating.enabled[periph];

    if (enable && !was_enabled) {
        /* Enabling clock - remove from gating list */
        /* 使能时钟 - 从门控列表中移除 */
        ctx->clock_gating.enabled[periph] = true;
        ctx->clock_gating.gate_count--;
        /* Estimate current savings reduction */
        /* 估计电流节省减少 */
        if (ctx->clock_gating.estimated_savings_uA > 10) {
            ctx->clock_gating.estimated_savings_uA -= 10;
        }
    } else if (!enable && was_enabled) {
        /* Disabling clock - add to gating list */
        /* 禁用时钟 - 添加到门控列表 */
        ctx->clock_gating.enabled[periph] = false;
        ctx->clock_gating.gate_count++;
        /* Estimate current savings */
        /* 估计电流节省 */
        ctx->clock_gating.estimated_savings_uA += 10;
    }

    /* Recalculate active count */
    /* 重新计算活动计数 */
    ctx->clock_gating.active_count = 0;
    for (int i = 0; i < CLOCK_PERIPH_MAX; i++) {
        if (ctx->clock_gating.enabled[i]) {
            ctx->clock_gating.active_count++;
        }
    }

    return 0;
}

clock_gate_state_t lp_get_clock_stats(low_power_context_t *ctx) {
    if (!ctx) {
        clock_gate_state_t empty = {0};
        return empty;
    }
    return ctx->clock_gating;
}

/* ======================================================================
 * Peripheral Power Control / 外设电源控制
 * ====================================================================== */

int lp_peripheral_power(low_power_context_t *ctx, power_domain_t domain, bool enable) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    if (domain >= POWER_DOMAIN_PERIPH_MAX) {
        return -1;
    }

    bool was_powered = ctx->periph_power.powered[domain];

    if (enable && !was_powered) {
        ctx->periph_power.powered[domain] = true;
        ctx->periph_power.active_domains |= (1 << domain);
    } else if (!enable && was_powered) {
        ctx->periph_power.powered[domain] = false;
        ctx->periph_power.active_domains &= ~(1 << domain);
    }

    /* Recalculate power reduction percentage */
    /* 重新计算功耗降低百分比 */
    uint32_t active_count = 0;
    for (int i = 0; i < POWER_DOMAIN_PERIPH_MAX; i++) {
        if (ctx->periph_power.powered[i]) {
            active_count++;
        }
    }
    ctx->periph_power.power_reduction_pct =
        ((POWER_DOMAIN_PERIPH_MAX - active_count) * 100) / POWER_DOMAIN_PERIPH_MAX;

    return 0;
}

/* ======================================================================
 * Wake-up Source Management / 唤醒源管理
 * ====================================================================== */

int lp_configure_wakeup(low_power_context_t *ctx, wakeup_source_t source,
                        const wakeup_source_config_t *config) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    if (source >= WAKEUP_SOURCE_MAX || !config) {
        return -1;
    }

    ctx->wakeup_mgr.sources[source] = *config;

    return 0;
}

wakeup_source_t lp_process_wakeups(low_power_context_t *ctx) {
    if (!ctx || !ctx->is_initialized) {
        return WAKEUP_SOURCE_NONE;
    }

    wakeup_source_t last = WAKEUP_SOURCE_NONE;

    /* Check all wake-up sources */
    /* 检查所有唤醒源 */
    for (int i = WAKEUP_SOURCE_PIN; i < WAKEUP_SOURCE_MAX; i++) {
        if (ctx->wakeup_mgr.sources[i].enabled && ctx->wakeup_mgr.sources[i].pending) {
            last = (wakeup_source_t)i;
            ctx->wakeup_mgr.last_wakeup = last;
            ctx->wakeup_mgr.wakeup_count++;

            /* Clear pending if configured */
            /* 如果配置则清除待处理标志 */
            if (ctx->wakeup_mgr.sources[i].clear_on_wake) {
                ctx->wakeup_mgr.sources[i].pending = false;
            }

            /* In real hardware, different sources have different wake paths.
             * Pin interrupts typically wake fastest, RTC takes longer.
             * 在真实硬件中，不同源有不同的唤醒路径。
             * 引脚中断通常唤醒最快，实时时钟需要更长时间。 */
        }
    }

    return last;
}

bool lp_has_pending_wakeup(low_power_context_t *ctx) {
    if (!ctx || !ctx->is_initialized) {
        return false;
    }

    for (int i = WAKEUP_SOURCE_PIN; i < WAKEUP_SOURCE_MAX; i++) {
        if (ctx->wakeup_mgr.sources[i].enabled && ctx->wakeup_mgr.sources[i].pending) {
            return true;
        }
    }

    return false;
}

/* ======================================================================
 * DVFS Management / DVFS管理
 * ====================================================================== */

int lp_dvfs_init(low_power_context_t *ctx, dvfs_operating_point_t *points,
                 uint32_t count, dvfs_policy_t policy) {
    if (!ctx || !ctx->is_initialized || !points || count == 0 || count > 8) {
        return -1;
    }

    ctx->dvfs.num_points = count;

    /* Copy operating points */
    /* 复制工作点 */
    for (uint32_t i = 0; i < count; i++) {
        ctx->dvfs.points[i] = points[i];
        /* Validate points: higher voltage must support higher frequency */
        /* 验证工作点：更高电压必须支持更高频率 */
        if (points[i].voltage_mv > 0 && points[i].frequency_khz > 0) {
            points[i].is_valid = true;
            /* Calculate estimated power: P = alpha * C * V^2 * f */
            /* 计算估计功耗：P = alpha * C * V^2 * f */
            float alpha = 0.1f;       /* Typical switching activity 典型翻转活动 */
            float capacitance = 50.0f; /* Estimated load capacitance 估计负载电容(pF) */
            points[i].power_uW = (uint32_t)(alpha * capacitance *
                (points[i].voltage_mv / 1000.0f) *
                (points[i].voltage_mv / 1000.0f) *
                (points[i].frequency_khz / 1000.0f) * 1000.0f);
            points[i].current_uA = points[i].power_uW / points[i].voltage_mv;
            /* Minimum safe frequency is typically 50% of max at this voltage */
            /* 最低安全频率通常为此电压下最大值的50% */
            points[i].min_safe_freq = points[i].frequency_khz / 2;
        } else {
            points[i].is_valid = false;
        }
    }

    /* Set current point to highest valid */
    /* 设置当前点为最高有效点 */
    for (int i = count - 1; i >= 0; i--) {
        if (ctx->dvfs.points[i].is_valid) {
            ctx->dvfs.current_point = ctx->dvfs.points[i];
            ctx->dvfs.target_point = ctx->dvfs.points[i];
            break;
        }
    }

    ctx->dvfs.policy = policy;

    return 0;
}

int lp_dvfs_set_policy(low_power_context_t *ctx, dvfs_policy_t policy) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    ctx->dvfs.policy = policy;
    return 0;
}

int lp_dvfs_switch(low_power_context_t *ctx, uint32_t point) {
    if (!ctx || !ctx->is_initialized) {
        return -1;
    }

    if (point >= ctx->dvfs.num_points) {
        return -1;
    }

    dvfs_operating_point_t *target = &ctx->dvfs.points[point];

    if (!target->is_valid) {
        return -1;
    }

    /* DVFS transition sequence:
     * 1. If increasing frequency: voltage FIRST, then frequency
     *    如果增加频率：先电压，后频率
     * 2. If decreasing frequency: frequency FIRST, then voltage
     *    如果降低频率：先频率，后电压
     *
     * This prevents timing violations during transitions.
     * 这防止转换期间的时序违规。 */

    bool freq_increase = target->frequency_khz > ctx->dvfs.current_point.frequency_khz;

    if (freq_increase) {
        /* Increase voltage first to ensure stability */
        /* 先增加电压以确保稳定性 */
        ctx->dvfs.current_point.voltage_mv = target->voltage_mv;
        /* In real hardware, wait for voltage to stabilize */
        /* 在真实硬件中，等待电压稳定 */
    }

    /* Update frequency */
    /* 更新频率 */
    ctx->dvfs.current_point.frequency_khz = target->frequency_khz;

    if (!freq_increase) {
        /* Decrease voltage after frequency to prevent overvoltage */
        /* 在频率后降低电压以防止过压 */
        ctx->dvfs.current_point.voltage_mv = target->voltage_mv;
    }

    /* Update current and power estimates */
    /* 更新电流和功耗估计 */
    ctx->dvfs.current_point.current_uA = target->current_uA;
    ctx->dvfs.current_point.power_uW = target->power_uW;
    ctx->dvfs.current_point.min_safe_freq = target->min_safe_freq;
    ctx->dvfs.current_point.is_valid = true;

    ctx->dvfs.target_point = *target;
    ctx->dvfs.transition_count++;
    ctx->dvfs.last_switch_time = ctx->power_monitor.head;

    return 0;
}

/* ======================================================================
 * Power Monitoring / 功耗监测
 * ====================================================================== */

void lp_record_sample(low_power_context_t *ctx, uint32_t current_uA,
                      uint32_t voltage_mv, uint32_t timestamp_ms) {
    if (!ctx || !ctx->is_initialized) {
        return;
    }

    power_sample_t *sample = &ctx->power_monitor.samples[ctx->power_monitor.head];

    sample->timestamp_ms = timestamp_ms;
    sample->current_uA = current_uA;
    sample->voltage_mv = voltage_mv;
    sample->mode = ctx->current_mode.mode;
    sample->clock_freq_khz = ctx->current_mode.clock_freq_khz;
    sample->active_peripherals = ctx->clock_gating.active_count;

    /* Advance head pointer (circular buffer) */
    /* 前进头指针（环形缓冲区） */
    ctx->power_monitor.head = (ctx->power_monitor.head + 1) % 128;

    if (ctx->power_monitor.is_full) {
        ctx->power_monitor.tail = ctx->power_monitor.head;
    }

    ctx->power_monitor.count++;
    if (ctx->power_monitor.count > 128) {
        ctx->power_monitor.count = 128;
        ctx->power_monitor.is_full = true;
    }
}

energy_profile_t lp_get_energy_profile(low_power_context_t *ctx) {
    if (!ctx || !ctx->is_initialized) {
        energy_profile_t empty = {0};
        return empty;
    }

    energy_profile_t profile;
    memset(&profile, 0, sizeof(energy_profile_t));

    uint32_t total_current = 0;
    uint32_t peak_current = 0;
    uint32_t min_current = UINT32_MAX;
    uint32_t sample_count = 0;

    /* Iterate through all recorded samples */
    /* 遍历所有记录的采样 */
    uint32_t num_samples = ctx->power_monitor.count;
    uint32_t start_idx = ctx->power_monitor.head;

    for (uint32_t i = 0; i < num_samples; i++) {
        uint32_t idx = (start_idx + i) % 128;
        power_sample_t *sample = &ctx->power_monitor.samples[idx];

        total_current += sample->current_uA;
        if (sample->current_uA > peak_current) {
            peak_current = sample->current_uA;
        }
        if (sample->current_uA < min_current) {
            min_current = sample->current_uA;
        }

        /* Classify time by power mode */
        /* 按功耗模式分类时间 */
        switch (sample->mode) {
            case POWER_MODE_ACTIVE:
                profile.active_time_ms += 10;  /* Assume 10ms per sample */
                break;
            case POWER_MODE_IDLE:
                profile.idle_time_ms += 10;
                break;
            case POWER_MODE_SLEEP:
                profile.sleep_time_ms += 10;
                break;
            case POWER_MODE_DEEP_SLEEP:
                profile.deep_sleep_time_ms += 10;
                break;
            default:
                break;
        }

        sample_count++;
    }

    if (sample_count == 0) {
        min_current = 0;
    }

    /* Calculate energy: E = P * t = I * V * t */
    /* 计算能耗：E = P * t = I * V * t */
    if (sample_count > 0) {
        profile.avg_current_uA = total_current / sample_count;
        profile.peak_current_uA = peak_current;
        profile.min_current_uA = min_current;

        /* Total energy in mJ (assuming 10ms per sample) */
        /* 总能耗(mJ，假设每采样10ms) */
        for (uint32_t i = 0; i < num_samples; i++) {
            uint32_t idx = (start_idx + i) % 128;
            power_sample_t *sample = &ctx->power_monitor.samples[idx];
            /* E(uJ) = I(uA) * V(mV) * t(ms) / 1000 */
            profile.total_energy_mJ +=
                (uint32_t)((uint64_t)sample->current_uA * sample->voltage_mv * 10 / 1000000);
        }
    }

    /* Mode switch count from context */
    /* 从上下文获取模式切换计数 */
    profile.mode_switch_count = ctx->profile.mode_switch_count;

    /* Energy per operation estimate */
    /* 每次操作能耗估计 */
    if (ctx->dvfs.current_point.frequency_khz > 0) {
        profile.energy_per_operation =
            ctx->dvfs.current_point.power_uW / (ctx->dvfs.current_point.frequency_khz / 1000);
    }

    return profile;
}

/* ======================================================================
 * Utility Functions / 工具函数
 * ====================================================================== */

uint32_t lp_calc_dynamic_power(float alpha, float capacitance_pF,
                               uint32_t voltage_mv, uint32_t frequency_khz) {
    /* Dynamic power formula: P = alpha * C * V^2 * f
     * 动态功耗公式：P = alpha * C * V^2 * f
     *
     * Units:
     *   alpha: dimensionless (0-1) 无量纲(0-1)
     *   C: Farads (pF input, convert to F) 法拉(pF输入，转换为F)
     *   V: Volts (mV input, convert to V) 伏特(mV输入，转换为V)
     *   f: Hertz (kHz input, convert to Hz) 赫兹(kHz输入，转换为Hz)
     *   P: Watts (convert to uW for output) 瓦特(转换为uW输出)
     */
    float voltage_v = voltage_mv / 1000.0f;
    float capacitance_f = capacitance_pF / 1e12f;
    float frequency_hz = frequency_khz * 1000.0f;

    /* P in watts, convert to micro-watts */
    /* P单位为瓦特，转换为微瓦 */
    float power_w = alpha * capacitance_f * voltage_v * voltage_v * frequency_hz;
    return (uint32_t)(power_w * 1e6f);  /* Convert to uW */
}

uint32_t lp_calc_energy(uint32_t power_uW, uint32_t duration_ms) {
    /* Energy formula: E = P * t
     * 能量公式：E = P * t
     *
     * Units:
     *   P: micro-watts (uW)
     *   t: milliseconds (ms)
     *   E: micro-joules (uJ)
     */
    /* E(uJ) = P(uW) * t(ms) */
    return power_uW * duration_ms;
}

void lp_print_state(low_power_context_t *ctx) {
    if (!ctx || !ctx->is_initialized) {
        printf("Low-power framework not initialized.\n");
        printf("低功耗框架未初始化。\n");
        return;
    }

    printf("========================================\n");
    printf("  Low-Power Framework State / 低功耗框架状态\n");
    printf("========================================\n\n");

    /* Current power mode */
    /* 当前功耗模式 */
    printf("[Power Mode / 功耗模式]\n");
    printf("  Mode:        %s\n", lp_mode_name(ctx->current_mode.mode));
    printf("  Voltage:     %u mV\n", ctx->current_mode.voltage_mv);
    printf("  Frequency:   %u kHz\n", ctx->current_mode.clock_freq_khz);
    printf("  Current:     %u uA\n", ctx->current_mode.current_uA);
    printf("  Wake Latency:%u us\n", ctx->current_mode.wake_latency_us);
    printf("  RAM Retain:  %s\n", ctx->current_mode.ram_retention ? "Yes" : "No");
    printf("  RTC Running: %s\n", ctx->current_mode.rtc_running ? "Yes" : "No");
    printf("\n");

    /* Clock gating status */
    /* 时钟门控状态 */
    printf("[Clock Gating / 时钟门控]\n");
    printf("  Active:      %u / %u peripherals\n",
           ctx->clock_gating.active_count, CLOCK_PERIPH_MAX);
    printf("  Gated:       %u peripherals\n", ctx->clock_gating.gate_count);
    printf("  Savings:     ~%u uA estimated\n", ctx->clock_gating.estimated_savings_uA);
    printf("  Peripherals:\n");
    const char *periph_names[] = {
        "GPIO", "SPI", "I2C", "UART", "TIMERS",
        "ADC", "DAC", "DMA", "USB", "CAN", "RTC", "WDT"
    };
    for (int i = 0; i < CLOCK_PERIPH_MAX; i++) {
        printf("    %12s: %s\n", periph_names[i],
               ctx->clock_gating.enabled[i] ? "CLK ON" : "CLK OFF");
    }
    printf("\n");

    /* Peripheral power domains */
    /* 外设电源域 */
    printf("[Peripheral Power / 外设电源]\n");
    const char *domain_names[] = {
        "AON (Always-On)", "Core Peripherals", "I/O Peripherals",
        "ADC/DAC", "USB"
    };
    for (int i = 0; i < POWER_DOMAIN_PERIPH_MAX; i++) {
        printf("  %20s: %s\n", domain_names[i],
               ctx->periph_power.powered[i] ? "POWERED" : "GATED");
    }
    printf("  Power Reduction: %u%%\n", ctx->periph_power.power_reduction_pct);
    printf("\n");

    /* Wake-up sources */
    /* 唤醒源 */
    printf("[Wake-up Sources / 唤醒源]\n");
    printf("  Total Wakeups: %u\n", ctx->wakeup_mgr.wakeup_count);
    printf("  Last Source:   ");
    switch (ctx->wakeup_mgr.last_wakeup) {
        case WAKEUP_SOURCE_PIN:        printf("Pin Interrupt\n"); break;
        case WAKEUP_SOURCE_RTC:        printf("RTC Alarm\n"); break;
        case WAKEUP_SOURCE_TIMER:      printf("Timer\n"); break;
        case WAKEUP_SOURCE_UART:       printf("UART\n"); break;
        case WAKEUP_SOURCE_I2C:        printf("I2C\n"); break;
        case WAKEUP_SOURCE_SPI:        printf("SPI\n"); break;
        case WAKEUP_SOURCE_DMA:        printf("DMA\n"); break;
        case WAKEUP_SOURCE_WATCHDOG:   printf("Watchdog\n"); break;
        case WAKEUP_SOURCE_ADC:        printf("ADC\n"); break;
        case WAKEUP_SOURCE_COMPARATOR: printf("Comparator\n"); break;
        default:                       printf("None\n"); break;
    }
    printf("  Enabled Sources:\n");
    const char *wakeup_names[] = {
        "Pin", "RTC", "Timer", "UART", "I2C",
        "SPI", "DMA", "Watchdog", "ADC", "Comparator"
    };
    for (int i = WAKEUP_SOURCE_PIN; i < WAKEUP_SOURCE_MAX; i++) {
        if (ctx->wakeup_mgr.sources[i].enabled) {
            printf("    - %s (pending: %s)\n",
                   wakeup_names[i - 1],
                   ctx->wakeup_mgr.sources[i].pending ? "YES" : "no");
        }
    }
    printf("\n");

    /* DVFS status */
    /* DVFS状态 */
    printf("[DVFS Status / DVFS状态]\n");
    printf("  Policy:      ");
    switch (ctx->dvfs.policy) {
        case DVFS_POLICY_MANUAL:      printf("MANUAL\n"); break;
        case DVFS_POLICY_AGGRESSIVE:  printf("AGGRESSIVE\n"); break;
        case DVFS_POLICY_BALANCED:    printf("BALANCED\n"); break;
        case DVFS_POLICY_EFFICIENT:   printf("EFFICIENT\n"); break;
        default:                      printf("UNKNOWN\n"); break;
    }
    printf("  Current:     %u mV / %u kHz\n",
           ctx->dvfs.current_point.voltage_mv,
           ctx->dvfs.current_point.frequency_khz);
    printf("  Power:       %u uW\n", ctx->dvfs.current_point.power_uW);
    printf("  Operating Points: %u\n", ctx->dvfs.num_points);
    printf("  Transitions:   %u\n", ctx->dvfs.transition_count);
    printf("\n");

    /* Energy profile */
    /* 能耗分析 */
    energy_profile_t profile = lp_get_energy_profile(ctx);
    printf("[Energy Profile / 能耗分析]\n");
    printf("  Total Energy:    %u mJ\n", profile.total_energy_mJ);
    printf("  Avg Current:     %u uA\n", profile.avg_current_uA);
    printf("  Peak Current:    %u uA\n", profile.peak_current_uA);
    printf("  Min Current:     %u uA\n", profile.min_current_uA);
    printf("  Active Time:     %u ms\n", profile.active_time_ms);
    printf("  Idle Time:       %u ms\n", profile.idle_time_ms);
    printf("  Sleep Time:      %u ms\n", profile.sleep_time_ms);
    printf("  Deep Sleep Time: %u ms\n", profile.deep_sleep_time_ms);
    printf("  Mode Switches:   %u\n", profile.mode_switch_count);
    printf("  Energy/Op:       %u uJ\n", profile.energy_per_operation);
    printf("\n");

    printf("========================================\n");
}
