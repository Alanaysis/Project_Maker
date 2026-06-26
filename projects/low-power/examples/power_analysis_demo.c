/**
 * power_analysis_demo.c - Power Consumption Analysis Demo
 *
 * 功耗分析演示
 *
 * This demo demonstrates power consumption analysis and profiling:
 * 本演示说明功耗消耗分析和分析：
 *
 * 1. Recording power samples over time
 *    随时间记录功耗采样
 * 2. Analyzing power usage patterns
 *    分析功耗使用模式
 * 3. Identifying power optimization opportunities
 *    识别功耗优化机会
 * 4. Comparing different power management strategies
 *    比较不同的电源管理策略
 */

#include <stdio.h>
#include <string.h>
#include "../include/low_power.h"

/**
 * Simulate a typical embedded application power profile
 * 模拟典型的嵌入式应用程序功耗曲线
 *
 * Typical power profile for a battery-powered sensor node:
 * 电池供电传感器节点的典型功耗曲线：
 *
 * Time 0-100ms:   Active (sensor read, processing)
 * Time 100-1000ms: Deep sleep (waiting for next sample)
 * Time 1000-1100ms: Active (transmit data)
 * Time 1100-10000ms: Deep sleep (waiting for next cycle)
 *
 * 时间 0-100毫秒：  活动（传感器读取，处理）
 * 时间 100-1000毫秒：深度睡眠（等待下次采样）
 * 时间 1000-1100毫秒：活动（传输数据）
 * 时间 1100-10000毫秒：深度睡眠（等待下一个周期）
 */
void simulate_sensor_node(low_power_context_t *ctx) {
    printf("  Simulating sensor node power profile...\n");
    printf("  模拟传感器节点功耗曲线...\n");
    printf("  ----------------------------------------\n");

    uint32_t timestamp = 0;

    /* Cycle 1: Active phase - sensor read */
    /* 周期1：活动阶段 - 传感器读取 */
    printf("  [Cycle 1] Active: Sensor Read\n");
    printf("  [周期1] 活动：传感器读取\n");
    lp_switch_mode(ctx, POWER_MODE_ACTIVE);
    for (int i = 0; i < 100; i++) {
        lp_record_sample(ctx, 18000 + (i % 2000), 3300, timestamp);
        timestamp += 1;
    }
    printf("    Duration: 100 ms, Avg current: ~19000 uA\n");
    printf("    持续时间：100毫秒，平均电流：~19000 uA\n");

    /* Deep sleep phase */
    /* 深度睡眠阶段 */
    printf("  [Cycle 2] Deep Sleep\n");
    printf("  [周期2] 深度睡眠\n");
    lp_switch_mode(ctx, POWER_MODE_DEEP_SLEEP);
    for (int i = 0; i < 900; i++) {
        lp_record_sample(ctx, 10, 0, timestamp);
        timestamp += 1;
    }
    printf("    Duration: 900 ms, Current: 10 uA\n");
    printf("    持续时间：900毫秒，电流：10 uA\n");

    /* Active phase - data transmission */
    /* 活动阶段 - 数据传输 */
    printf("  [Cycle 3] Active: Data Transmission\n");
    printf("  [周期3] 活动：数据传输\n");
    lp_switch_mode(ctx, POWER_MODE_ACTIVE);
    for (int i = 0; i < 100; i++) {
        lp_record_sample(ctx, 25000 + (i % 5000), 3300, timestamp);
        timestamp += 1;
    }
    printf("    Duration: 100 ms, Avg current: ~27500 uA\n");
    printf("    持续时间：100毫秒，平均电流：~27500 uA\n");

    /* Long deep sleep */
    /* 长时间深度睡眠 */
    printf("  [Cycle 4] Deep Sleep (long)\n");
    printf("  [周期4] 深度睡眠（长）\n");
    lp_switch_mode(ctx, POWER_MODE_DEEP_SLEEP);
    for (int i = 0; i < 8900; i++) {
        lp_record_sample(ctx, 10, 0, timestamp);
        timestamp += 1;
    }
    printf("    Duration: 8900 ms, Current: 10 uA\n");
    printf("    持续时间：8900毫秒，电流：10 uA\n");

    printf("\n");
}

/**
 * Simulate a different power strategy: using sleep instead of deep sleep
 * 模拟不同的功耗策略：使用睡眠而非深度睡眠
 */
void simulate_sleep_strategy(low_power_context_t *ctx) {
    printf("  Simulating sleep mode strategy...\n");
    printf("  模拟睡眠模式策略...\n");
    printf("  ----------------------------------------\n");

    uint32_t timestamp = 0;

    /* Active phase */
    /* 活动阶段 */
    printf("  [Cycle 1] Active: Sensor Read\n");
    lp_switch_mode(ctx, POWER_MODE_ACTIVE);
    for (int i = 0; i < 100; i++) {
        lp_record_sample(ctx, 18000, 3300, timestamp);
        timestamp += 1;
    }

    /* Sleep phase (instead of deep sleep) */
    /* 睡眠阶段（而非深度睡眠） */
    printf("  [Cycle 2] Sleep Mode\n");
    lp_switch_mode(ctx, POWER_MODE_SLEEP);
    for (int i = 0; i < 900; i++) {
        lp_record_sample(ctx, 2000, 3300, timestamp);
        timestamp += 1;
    }
    printf("    Duration: 900 ms, Current: 2000 uA\n");

    /* Active phase */
    /* 活动阶段 */
    printf("  [Cycle 3] Active: Data Transmission\n");
    lp_switch_mode(ctx, POWER_MODE_ACTIVE);
    for (int i = 0; i < 100; i++) {
        lp_record_sample(ctx, 25000, 3300, timestamp);
        timestamp += 1;
    }

    /* Sleep phase */
    /* 睡眠阶段 */
    printf("  [Cycle 4] Sleep Mode\n");
    lp_switch_mode(ctx, POWER_MODE_SLEEP);
    for (int i = 0; i < 8900; i++) {
        lp_record_sample(ctx, 2000, 3300, timestamp);
        timestamp += 1;
    }

    printf("\n");
}

/**
 * Calculate and display energy comparison
 * 计算并显示能耗对比
 */
void compare_strategies(low_power_context_t *ctx_deep, low_power_context_t *ctx_sleep) {
    printf("\n  Strategy Comparison / 策略对比\n");
    printf("  ----------------------------------------\n");

    energy_profile_t profile_deep = lp_get_energy_profile(ctx_deep);
    energy_profile_t profile_sleep = lp_get_energy_profile(ctx_sleep);

    printf("  Metric                    | Deep Sleep | Sleep Mode\n");
    printf("  --------------------------|------------|----------\n");
    printf("  Total Energy (mJ)         | %-10u | %u\n",
           profile_deep.total_energy_mJ, profile_sleep.total_energy_mJ);
    printf("  Avg Current (uA)          | %-10u | %u\n",
           profile_deep.avg_current_uA, profile_sleep.avg_current_uA);
    printf("  Peak Current (uA)         | %-10u | %u\n",
           profile_deep.peak_current_uA, profile_sleep.peak_current_uA);
    printf("  Deep Sleep Time (ms)      | %-10u | %u\n",
           profile_deep.deep_sleep_time_ms, profile_sleep.deep_sleep_time_ms);
    printf("  Sleep Time (ms)           | %-10u | %u\n",
           profile_deep.sleep_time_ms, profile_sleep.sleep_time_ms);

    /* Calculate savings */
    /* 计算节省 */
    if (profile_sleep.total_energy_mJ > 0) {
        float savings = (1.0f - (float)profile_deep.total_energy_mJ /
                        (float)profile_sleep.total_energy_mJ) * 100.0f;
        printf("  Energy Savings            |            | %.1f%%\n", savings);
    }
    printf("\n");
}

/**
 * Demonstrate clock gating impact on power
 * 演示时钟门控对功耗的影响
 */
void demonstrate_clock_gating_impact(low_power_context_t *ctx) {
    printf("\n  Clock Gating Impact Analysis\n");
    printf("  时钟门控影响分析\n");
    printf("  ----------------------------------------\n");

    /* Without clock gating */
    /* 无时钟门控 */
    printf("  Without Clock Gating / 无时钟门控:\n");
    clock_gate_state_t clocks_off = lp_get_clock_stats(ctx);
    printf("    Active peripherals: %u / %u\n",
           clocks_off.active_count, CLOCK_PERIPH_MAX);
    printf("    Estimated savings: ~0 uA\n");

    /* With selective clock gating */
    /* 选择性时钟门控 */
    printf("\n  With Selective Clock Gating / 选择性时钟门控:\n");

    /* Gate clocks to unused peripherals */
    /* 门控未使用外设的时钟 */
    lp_clock_gate(ctx, CLOCK_PERIPH_SPI, false);
    lp_clock_gate(ctx, CLOCK_PERIPH_USB, false);
    lp_clock_gate(ctx, CLOCK_PERIPH_CAN, false);
    lp_clock_gate(ctx, CLOCK_PERIPH_DAC, false);

    clocks_off = lp_get_clock_stats(ctx);
    printf("    Active peripherals: %u / %u\n",
           clocks_off.active_count, CLOCK_PERIPH_MAX);
    printf("    Gated peripherals: %u\n", clocks_off.gate_count);
    printf("    Estimated savings: ~%u uA\n", clocks_off.estimated_savings_uA);

    /* Calculate power reduction */
    /* 计算功耗降低 */
    uint32_t base_power = lp_calc_dynamic_power(0.1f, 50.0f, 3300, 72000);
    uint32_t gated_power = lp_calc_dynamic_power(0.05f, 50.0f, 3300, 72000);
    uint32_t savings = base_power > gated_power ? base_power - gated_power : 0;

    printf("\n  Dynamic Power Calculation / 动态功耗计算:\n");
    printf("    Without gating: %u uW\n", base_power);
    printf("    With gating:    %u uW\n", gated_power);
    printf("    Savings:         %u uW (%.1f%%)\n",
           savings, (float)savings / base_power * 100.0f);
    printf("\n");
}

int main(void) {
    printf("========================================\n");
    printf("  Power Consumption Analysis Demo\n");
    printf("  功耗分析演示\n");
    printf("========================================\n\n");

    /* Demo 1: Sensor node power profile */
    /* 演示1：传感器节点功耗曲线 */
    printf("[1] Sensor Node Power Profile\n");
    printf("[1] 传感器节点功耗曲线\n");
    printf("----------------------------------------\n");

    low_power_context_t ctx_deep;
    lp_init(&ctx_deep);
    simulate_sensor_node(&ctx_deep);

    energy_profile_t profile_deep = lp_get_energy_profile(&ctx_deep);
    printf("  Energy Profile / 能耗分析:\n");
    printf("    Total Energy:     %u mJ\n", profile_deep.total_energy_mJ);
    printf("    Avg Current:      %u uA\n", profile_deep.avg_current_uA);
    printf("    Peak Current:     %u uA\n", profile_deep.peak_current_uA);
    printf("    Active Time:      %u ms\n", profile_deep.active_time_ms);
    printf("    Deep Sleep Time:  %u ms\n", profile_deep.deep_sleep_time_ms);
    printf("\n");

    /* Demo 2: Compare strategies */
    /* 演示2：对比策略 */
    printf("[2] Strategy Comparison: Deep Sleep vs Sleep\n");
    printf("[2] 策略对比：深度睡眠 vs 睡眠\n");
    printf("----------------------------------------\n");

    low_power_context_t ctx_sleep;
    lp_init(&ctx_sleep);
    simulate_sleep_strategy(&ctx_sleep);

    compare_strategies(&ctx_deep, &ctx_sleep);

    /* Demo 3: Clock gating impact */
    /* 演示3：时钟门控影响 */
    printf("[3] Clock Gating Impact\n");
    printf("[3] 时钟门控影响\n");
    printf("----------------------------------------\n");

    low_power_context_t ctx_gating;
    lp_init(&ctx_gating);
    demonstrate_clock_gating_impact(&ctx_gating);

    /* Demo 4: DVFS energy comparison */
    /* 演示4：DVFS能耗对比 */
    printf("[4] DVFS Energy Comparison\n");
    printf("[4] DVFS能耗对比\n");
    printf("----------------------------------------\n");

    printf("  DVFS Operating Points / DVFS工作点:\n");
    printf("  %-8s | %-10s | %-10s | %-12s | %-10s\n",
           "Point", "Voltage", "Frequency", "Power", "Efficiency");
    printf("  %-8s | %-10s | %-10s | %-12s | %-10s\n",
           "------", "--------", "---------", "--------", "----------");

    dvfs_operating_point_t points[8];
    memset(points, 0, sizeof(points));

    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;
    points[1].voltage_mv = 3000; points[1].frequency_khz = 48000;
    points[2].voltage_mv = 2700; points[2].frequency_khz = 36000;
    points[3].voltage_mv = 2500; points[3].frequency_khz = 24000;
    points[4].voltage_mv = 2200; points[4].frequency_khz = 12000;
    points[5].voltage_mv = 1800; points[5].frequency_khz = 4000;
    points[6].voltage_mv = 1500; points[6].frequency_khz = 1000;
    points[7].voltage_mv = 1200; points[7].frequency_khz = 100;

    for (int i = 0; i < 8; i++) {
        points[i].is_valid = true;
        points[i].power_uW = lp_calc_dynamic_power(0.1f, 50.0f,
                              points[i].voltage_mv, points[i].frequency_khz);
        points[i].current_uA = points[i].power_uW / points[i].voltage_mv;

        /* Energy per operation: P / f */
        /* 每次操作能耗：P / f */
        float energy_per_op = points[i].frequency_khz > 0 ?
            (float)points[i].power_uW / (points[i].frequency_khz / 1000.0f) : 0;

        printf("  %-8u | %-8u mV | %-8u kHz | %-10u uW | %.2f uJ/op\n",
               i, points[i].voltage_mv, points[i].frequency_khz,
               points[i].power_uW, energy_per_op);
    }

    printf("\n  Note: Lower energy per operation = more efficient\n");
    printf("  注意：每次操作能耗越低 = 越高效\n");
    printf("\n");

    /* Summary */
    printf("[5] Low-Power Design Summary / 低功耗设计摘要\n");
    printf("----------------------------------------\n");
    printf("  Key techniques for reducing power:\n");
    printf("  降低功耗的关键技术：\n");
    printf("  1. Use deeper sleep modes when possible\n");
    printf("     尽可能使用更深的睡眠模式\n");
    printf("  2. Apply clock gating to idle peripherals\n");
    printf("     对空闲外设应用时钟门控\n");
    printf("  3. Use DVFS to match performance to workload\n");
    printf("     使用DVFS使性能与工作负载匹配\n");
    printf("  4. Power off unused peripheral domains\n");
    printf("     关闭未使用的外设域\n");
    printf("  5. Minimize active time, maximize sleep time\n");
    printf("     最小化活动时间，最大化睡眠时间\n");
    printf("\nDemo complete! / 演示完成！\n");
    return 0;
}
