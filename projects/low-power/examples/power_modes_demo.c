/**
 * power_modes_demo.c - Power Mode Switching Demo
 *
 * 功耗模式切换演示
 *
 * This demo illustrates the power mode switching lifecycle:
 * 本演示说明功耗模式切换周期：
 *
 * Active -> Idle -> Sleep -> Deep Sleep -> Wakeup -> Active
 * 活动 -> 空闲 -> 睡眠 -> 深度睡眠 -> 唤醒 -> 活动
 *
 * Each mode transition demonstrates different low-power techniques:
 * 每次模式转换演示不同的低功耗技术：
 * - Clock gating  时钟门控
 * - Voltage scaling  电压缩放
 * - Peripheral power gating  外设电源门控
 * - Context save/restore  上下文保存/恢复
 */

#include <stdio.h>
#include <string.h>
#include "../include/low_power.h"

/**
 * Simulate some work being done in active mode
 * 模拟在活动模式下完成一些工作
 */
void do_work(low_power_context_t *ctx, const char *task_name, uint32_t duration_ms) {
    printf("  [WORK] %s (%u ms)\n", task_name, duration_ms);

    /* Record power samples during work */
    /* 记录工作期间的功耗采样 */
    for (uint32_t i = 0; i < duration_ms; i += 10) {
        /* Simulate varying current during active work */
        /* 模拟活动工作期间的变化电流 */
        uint32_t current = 18000 + (i % 4000);
        lp_record_sample(ctx, current, ctx->current_mode.voltage_mv, i);
    }
}

/**
 * Demonstrate power mode switching
 * 演示功耗模式切换
 */
int main(void) {
    printf("========================================\n");
    printf("  Power Mode Switching Demo\n");
    printf("  功耗模式切换演示\n");
    printf("========================================\n\n");

    low_power_context_t ctx;

    /* Initialize framework */
    /* 初始化框架 */
    printf("[1] Initializing low-power framework...\n");
    printf("[1] 初始化低功耗框架...\n");
    lp_init(&ctx);
    printf("  Current mode: %s\n", lp_mode_name(ctx.current_mode.mode));
    printf("  Current: %u uA\n\n", ctx.current_mode.current_uA);

    /* Set up DVFS operating points */
    /* 设置DVFS工作点 */
    printf("[2] Setting up DVFS operating points...\n");
    printf("[2] 设置DVFS工作点...\n");

    dvfs_operating_point_t points[8];
    memset(points, 0, sizeof(points));

    /* Define 8 operating points from highest to lowest performance */
    /* 定义8个工作点，从最高到最低性能 */
    /* High performance point: 3.3V, 72MHz */
    /* 高性能点：3.3V，72MHz */
    points[0].voltage_mv = 3300;
    points[0].frequency_khz = 72000;
    points[0].is_valid = true;
    points[0].min_safe_freq = 36000;
    points[0].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 3300, 72000);

    /* Medium-high: 3.0V, 48MHz */
    /* 中高：3.0V，48MHz */
    points[1].voltage_mv = 3000;
    points[1].frequency_khz = 48000;
    points[1].is_valid = true;
    points[1].min_safe_freq = 24000;
    points[1].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 3000, 48000);

    /* Medium: 2.7V, 36MHz */
    /* 中等：2.7V，36MHz */
    points[2].voltage_mv = 2700;
    points[2].frequency_khz = 36000;
    points[2].is_valid = true;
    points[2].min_safe_freq = 18000;
    points[2].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 2700, 36000);

    /* Medium-low: 2.5V, 24MHz */
    /* 中低：2.5V，24MHz */
    points[3].voltage_mv = 2500;
    points[3].frequency_khz = 24000;
    points[3].is_valid = true;
    points[3].min_safe_freq = 12000;
    points[3].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 2500, 24000);

    /* Low: 2.2V, 12MHz */
    /* 低：2.2V，12MHz */
    points[4].voltage_mv = 2200;
    points[4].frequency_khz = 12000;
    points[4].is_valid = true;
    points[4].min_safe_freq = 6000;
    points[4].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 2200, 12000);

    /* Very low: 1.8V, 4MHz */
    /* 很低：1.8V，4MHz */
    points[5].voltage_mv = 1800;
    points[5].frequency_khz = 4000;
    points[5].is_valid = true;
    points[5].min_safe_freq = 2000;
    points[5].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 1800, 4000);

    /* Ultra low: 1.5V, 1MHz */
    /* 超低：1.5V，1MHz */
    points[6].voltage_mv = 1500;
    points[6].frequency_khz = 1000;
    points[6].is_valid = true;
    points[6].min_safe_freq = 500;
    points[6].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 1500, 1000);

    /* Minimum: 1.2V, 100kHz (RTC speed) */
    /* 最低：1.2V，100kHz（实时时钟速度） */
    points[7].voltage_mv = 1200;
    points[7].frequency_khz = 100;
    points[7].is_valid = true;
    points[7].min_safe_freq = 50;
    points[7].power_uW = lp_calc_dynamic_power(0.1f, 50.0f, 1200, 100);

    lp_dvfs_init(&ctx, points, 8, DVFS_POLICY_EFFICIENT);

    printf("  DVFS points configured:\n");
    for (uint32_t i = 0; i < 8; i++) {
        printf("    Point %u: %u mV / %u kHz -> %u uW\n",
               i, points[i].voltage_mv, points[i].frequency_khz, points[i].power_uW);
    }
    printf("\n");

    /* === Power Mode Switching Cycle === */
    /* === 功耗模式切换周期 === */
    printf("[3] Power Mode Switching Cycle\n");
    printf("[3] 功耗模式切换周期\n");
    printf("----------------------------------------\n\n");

    /* Phase 1: Active mode - Full performance */
    /* 阶段1：活动模式 - 全性能 */
    printf("--- Phase 1: ACTIVE MODE (Full Performance)\n");
    printf("--- 阶段1：活动模式（全性能）\n");
    lp_dvfs_switch(&ctx, 0);  /* Highest performance point */
    printf("  DVFS: %u mV / %u kHz\n",
           ctx.dvfs.current_point.voltage_mv, ctx.dvfs.current_point.frequency_khz);
    printf("  Power: %u uW\n", ctx.dvfs.current_point.power_uW);
    do_work(&ctx, "Sensor Read", 50);
    do_work(&ctx, "Data Processing", 30);
    printf("  Mode power: ~%u uA estimated\n\n", ctx.current_mode.current_uA);

    /* Phase 2: Enter Idle mode */
    /* 阶段2：进入空闲模式 */
    printf("--- Phase 2: IDLE MODE\n");
    printf("--- 阶段2：空闲模式\n");
    printf("  Technique: CPU halted, peripherals active\n");
    printf("  技术：CPU暂停，外设活动\n");
    lp_switch_mode(&ctx, POWER_MODE_IDLE);
    printf("  Wake latency: %u us\n", ctx.current_mode.wake_latency_us);
    printf("  Estimated current: %u uA (savings: ~25%%)\n\n",
           ctx.current_mode.current_uA);

    /* Phase 3: Enter Sleep mode with clock gating */
    /* 阶段3：进入睡眠模式并使用时钟门控 */
    printf("--- Phase 3: SLEEP MODE (Clock Gating)\n");
    printf("--- 阶段3：睡眠模式（时钟门控）\n");
    printf("  Gating clocks to unused peripherals...\n");
    printf("  门控未使用外设的时钟...\n");
    lp_clock_gate(&ctx, CLOCK_PERIPH_SPI, false);
    lp_clock_gate(&ctx, CLOCK_PERIPH_USB, false);
    lp_clock_gate(&ctx, CLOCK_PERIPH_CAN, false);
    clock_gate_state_t clocks = lp_get_clock_stats(&ctx);
    printf("  Clocks gated: %u peripherals\n", clocks.gate_count);
    printf("  Estimated savings: ~%u uA\n", clocks.estimated_savings_uA);
    lp_switch_mode(&ctx, POWER_MODE_SLEEP);
    printf("  Wake latency: %u us\n", ctx.current_mode.wake_latency_us);
    printf("  Estimated current: %u uA (savings: ~90%%)\n\n",
           ctx.current_mode.current_uA);

    /* Phase 4: Enter Deep Sleep */
    /* 阶段4：进入深度睡眠 */
    printf("--- Phase 4: DEEP SLEEP MODE\n");
    printf("--- 阶段4：深度睡眠模式\n");
    printf("  Powering down non-essential domains...\n");
    printf("  关闭非必要域...\n");
    lp_peripheral_power(&ctx, POWER_DOMAIN_PERIPH_USB, false);
    lp_peripheral_power(&ctx, POWER_DOMAIN_PERIPH_ADC_DAC, false);
    lp_switch_mode(&ctx, POWER_MODE_DEEP_SLEEP);
    printf("  Wake latency: %u us\n", ctx.current_mode.wake_latency_us);
    printf("  Estimated current: %u uA (savings: ~99.9%%)\n\n",
           ctx.current_mode.current_uA);

    /* Phase 5: Simulate wake-up */
    /* 阶段5：模拟唤醒 */
    printf("--- Phase 5: WAKE-UP PROCESS\n");
    printf("--- 阶段5：唤醒过程\n");

    /* Configure wake-up sources before deep sleep */
    /* 在深度睡眠前配置唤醒源 */
    wakeup_source_config_t pin_wakeup = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x01,  /* Pin 0 */
        .pending = true,        /* Simulate pin interrupt */
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &pin_wakeup);

    wakeup_source_config_t rtc_wakeup = {
        .source = WAKEUP_SOURCE_RTC,
        .enabled = true,
        .configuration = 32768, /* 32.768 kHz RTC */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_RTC, &rtc_wakeup);

    /* Process wake-up sources */
    /* 处理唤醒源 */
    wakeup_source_t woke = lp_process_wakeups(&ctx);
    printf("  Wake-up source: ");
    switch (woke) {
        case WAKEUP_SOURCE_PIN:        printf("Pin Interrupt\n"); break;
        case WAKEUP_SOURCE_RTC:        printf("RTC Alarm\n"); break;
        case WAKEUP_SOURCE_TIMER:      printf("Timer\n"); break;
        default:                       printf("Unknown\n"); break;
    }
    printf("  Total wake-ups so far: %u\n\n", ctx.wakeup_mgr.wakeup_count);

    /* Phase 6: Return to active mode with DVFS scaling */
    /* 阶段6：返回活动模式并缩放DVFS */
    printf("--- Phase 6: RETURN TO ACTIVE (DVFS Scaling)\n");
    printf("--- 阶段6：返回活动（DVFS缩放）\n");

    /* Workload analysis - determine needed performance */
    /* 工作负载分析 - 确定所需性能 */
    printf("  Analyzing workload requirements...\n");
    printf("  分析工作负载需求...\n");

    /* Switch to medium performance for moderate workload */
    /* 切换到中等性能以适应中等工作负载 */
    lp_dvfs_switch(&ctx, 2);  /* 2.7V / 36MHz */
    printf("  DVFS: %u mV / %u kHz (balanced point)\n",
           ctx.dvfs.current_point.voltage_mv,
           ctx.dvfs.current_point.frequency_khz);
    printf("  Power: %u uW\n", ctx.dvfs.current_point.power_uW);

    lp_switch_mode(&ctx, POWER_MODE_ACTIVE);
    printf("  Estimated current: %u uA\n\n", ctx.current_mode.current_uA);

    /* Phase 7: Continue with efficient operation */
    /* 阶段7：继续高效运行 */
    printf("--- Phase 7: EFFICIENT OPERATION\n");
    printf("--- 阶段7：高效运行\n");
    do_work(&ctx, "Low-power task processing", 20);

    /* Show energy profile */
    /* 显示能耗分析 */
    printf("\n[4] Energy Profile Summary\n");
    printf("[4] 能耗分析摘要\n");
    printf("----------------------------------------\n");
    energy_profile_t profile = lp_get_energy_profile(&ctx);
    printf("  Total Energy:     %u mJ\n", profile.total_energy_mJ);
    printf("  Avg Current:      %u uA\n", profile.avg_current_uA);
    printf("  Peak Current:     %u uA\n", profile.peak_current_uA);
    printf("  Min Current:      %u uA\n", profile.min_current_uA);
    printf("  Active Time:      %u ms\n", profile.active_time_ms);
    printf("  Sleep Time:       %u ms\n", profile.sleep_time_ms);
    printf("  Deep Sleep Time:  %u ms\n", profile.deep_sleep_time_ms);
    printf("  Mode Switches:    %u\n", profile.mode_switch_count);
    printf("  Energy/Operation: %u uJ\n", profile.energy_per_operation);
    printf("\n");

    /* Print full state */
    /* 打印完整状态 */
    printf("[5] Full Framework State\n");
    printf("[5] 完整框架状态\n");
    lp_print_state(&ctx);

    printf("\nDemo complete! / 演示完成！\n");
    return 0;
}
