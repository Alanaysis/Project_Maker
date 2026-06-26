/**
 * dvfs_demo.c - Dynamic Voltage Frequency Scaling Demo
 *
 * DVFS演示
 *
 * This demo illustrates Dynamic Voltage Frequency Scaling (DVFS):
 * 本演示说明动态电压频率调节（DVFS）：
 *
 * DVFS dynamically adjusts supply voltage and clock frequency
 * to minimize energy per operation based on workload demands.
 *
 * DVFS根据工作负载需求动态调整供电电压和时钟频率，
 * 以最小化每次操作的能耗。
 *
 * Key principle: Dynamic power P = alpha * C * V^2 * f
 * 关键原理：动态功耗 P = alpha * C * V^2 * f
 *
 * Since voltage is squared, reducing voltage has a quadratic
 * effect on power reduction, making it extremely effective.
 *
 * 由于电压是平方项，降低电压对功耗降低有平方效应，
 * 使其非常有效。
 */

#include <stdio.h>
#include <string.h>
#include "../include/low_power.h"

/**
 * Display DVFS operating point details
 * 显示DVFS工作点详情
 */
void display_operating_point(const char *label, uint32_t voltage_mv,
                              uint32_t frequency_khz) {
    uint32_t power = lp_calc_dynamic_power(0.1f, 50.0f, voltage_mv, frequency_khz);
    uint32_t energy_per_op = frequency_khz > 0 ?
        power / (frequency_khz / 1000) : 0;

    printf("    %-20s | %4u mV | %6u kHz | %7u uW | %5.2f uJ/op\n",
           label, voltage_mv, frequency_khz, power, (float)energy_per_op);
}

/**
 * Demonstrate DVFS policy behaviors
 * 演示DVFS策略行为
 */
void demonstrate_policy(low_power_context_t *ctx, dvfs_policy_t policy,
                        const char *policy_name) {
    printf("\n  Policy: %s\n", policy_name);
    printf("  策略：");

    switch (policy) {
        case DVFS_POLICY_MANUAL:      printf("手动\n"); break;
        case DVFS_POLICY_AGGRESSIVE:  printf("激进\n"); break;
        case DVFS_POLICY_BALANCED:    printf("平衡\n"); break;
        case DVFS_POLICY_EFFICIENT:   printf("高效\n"); break;
        default:                      printf("未知\n"); break;
    }

    printf("  ----------------------------------------\n");

    /* Simulate workload changes */
    /* 模拟工作负载变化 */
    uint32_t workloads[] = {10, 30, 60, 90, 50, 20, 80, 10};
    const char *workload_names[] = {
        "Idle", "Light", "Medium", "Heavy",
        "Medium", "Light", "Heavy", "Idle"
    };

    for (int i = 0; i < 8; i++) {
        /* Determine operating point based on policy */
        /* 根据策略确定工作点 */
        int point_idx;
        switch (policy) {
            case DVFS_POLICY_MANUAL:
                point_idx = 4;  /* Always medium */
                break;
            case DVFS_POLICY_AGGRESSIVE:
                point_idx = workloads[i] > 50 ? 0 : 2;  /* High or medium */
                break;
            case DVFS_POLICY_BALANCED:
                if (workloads[i] < 20)      point_idx = 5;
                else if (workloads[i] < 50) point_idx = 3;
                else if (workloads[i] < 80) point_idx = 1;
                else                          point_idx = 0;
                break;
            case DVFS_POLICY_EFFICIENT:
                if (workloads[i] < 15)      point_idx = 7;
                else if (workloads[i] < 30) point_idx = 6;
                else if (workloads[i] < 60) point_idx = 4;
                else                          point_idx = 2;
                break;
            default:
                point_idx = 4;
                break;
        }

        dvfs_operating_point_t *pt = &ctx->dvfs.points[point_idx];
        uint32_t power = lp_calc_dynamic_power(0.1f, 50.0f,
                              pt->voltage_mv, pt->frequency_khz);
        uint32_t energy = lp_calc_energy(power, 10);  /* 10ms per task */

        printf("    [%s] -> Point %u: %u mV / %u kHz | Power: %u uW | Energy: %u uJ\n",
               workload_names[i], point_idx, pt->voltage_mv, pt->frequency_khz,
               power, energy);

        lp_dvfs_switch(ctx, point_idx);
    }
}

/**
 * Show the relationship between voltage, frequency, and power
 * 显示电压、频率和功耗之间的关系
 */
void demonstrate_power_relationship(void) {
    printf("\n  Voltage-Frequency-Power Relationship\n");
    printf("  电压-频率-功耗关系\n");
    printf("  ----------------------------------------\n");
    printf("  P = alpha * C * V^2 * f\n");
    printf("  (alpha=0.1, C=50pF)\n\n");

    printf("  %-15s | %-12s | %-12s | %-12s\n",
           "Voltage (mV)", "Frequency (kHz)", "Power (uW)", "Power Ratio");
    printf("  %-15s | %-12s | %-12s | %-12s\n",
           "--------------", "-------------", "------------", "------------");

    /* Show how power changes with voltage at fixed frequency */
    /* 显示固定频率下功耗随电压的变化 */
    uint32_t freq = 72000;
    uint32_t base_power = lp_calc_dynamic_power(0.1f, 50.0f, 3300, freq);

    uint32_t voltages[] = {3300, 3000, 2700, 2500, 2200, 1800, 1500, 1200};
    for (int i = 0; i < 8; i++) {
        uint32_t p = lp_calc_dynamic_power(0.1f, 50.0f, voltages[i], freq);
        float ratio = (float)p / base_power * 100.0f;
        printf("  %-15u | %-12u | %-12u | %.1f%%\n",
               voltages[i], freq, p, ratio);
    }

    printf("\n  Notice: Power scales with V^2 (quadratic relationship)\n");
    printf("  注意：功耗与V^2成正比（二次关系）\n");
    printf("  Reducing voltage from 3.3V to 1.2V saves ~87%% of dynamic power!\n");
    printf("  将电压从3.3V降至1.2V可节省约87%%的动态功耗！\n");
    printf("\n");
}

/**
 * Demonstrate DVFS transition sequence
 * 演示DVFS转换序列
 */
void demonstrate_transition_sequence(low_power_context_t *ctx) {
    printf("\n  DVFS Transition Sequence\n");
    printf("  DVFS转换序列\n");
    printf("  ----------------------------------------\n");

    printf("  Scenario 1: Scaling UP (increasing performance)\n");
    printf("  场景1：向上缩放（增加性能）\n");
    printf("  Step 1: Increase voltage FIRST (ensure stability)\n");
    printf("  步骤1：先增加电压（确保稳定性）\n");
    printf("  Step 2: Increase frequency SECOND (avoid timing violations)\n");
    printf("  步骤2：后增加频率（避免时序违规）\n");
    printf("  V: 1.2V -> 3.3V  |  F: 100kHz -> 72MHz\n");
    printf("  电压: 1.2V -> 3.3V  |  频率: 100kHz -> 72MHz\n");

    lp_dvfs_switch(ctx, 7);  /* Start from lowest */
    printf("  Current: %u mV / %u kHz\n",
           ctx->dvfs.current_point.voltage_mv,
           ctx->dvfs.current_point.frequency_khz);

    lp_dvfs_switch(ctx, 0);  /* Go to highest */
    printf("  After:   %u mV / %u kHz\n",
           ctx->dvfs.current_point.voltage_mv,
           ctx->dvfs.current_point.frequency_khz);

    printf("\n  Scenario 2: Scaling DOWN (saving power)\n");
    printf("  场景2：向下缩放（节省功耗）\n");
    printf("  Step 1: Decrease frequency FIRST (reduce workload)\n");
    printf("  步骤1：先降低频率（减少工作负载）\n");
    printf("  Step 2: Decrease voltage SECOND (prevent overvoltage)\n");
    printf("  步骤2：后降低电压（防止过压）\n");
    printf("  V: 3.3V -> 1.2V  |  F: 72MHz -> 100kHz\n");
    printf("  电压: 3.3V -> 1.2V  |  频率: 72MHz -> 100kHz\n");

    lp_dvfs_switch(ctx, 0);  /* Start from highest */
    printf("  Current: %u mV / %u kHz\n",
           ctx->dvfs.current_point.voltage_mv,
           ctx->dvfs.current_point.frequency_khz);

    lp_dvfs_switch(ctx, 7);  /* Go to lowest */
    printf("  After:   %u mV / %u kHz\n",
           ctx->dvfs.current_point.voltage_mv,
           ctx->dvfs.current_point.frequency_khz);

    printf("\n");
}

int main(void) {
    printf("========================================\n");
    printf("  DVFS (Dynamic Voltage Frequency Scaling) Demo\n");
    printf("  DVFS（动态电压频率调节）演示\n");
    printf("========================================\n\n");

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Set up DVFS operating points */
    /* 设置DVFS工作点 */
    printf("[1] DVFS Operating Points Configuration\n");
    printf("[1] DVFS工作点配置\n");
    printf("----------------------------------------\n");

    dvfs_operating_point_t points[8];
    memset(points, 0, sizeof(points));

    /* Define operating points from high to low performance */
    /* 定义从高到低性能的工作点 */
    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;
    points[1].voltage_mv = 3000; points[1].frequency_khz = 48000;
    points[2].voltage_mv = 2700; points[2].frequency_khz = 36000;
    points[3].voltage_mv = 2500; points[3].frequency_khz = 24000;
    points[4].voltage_mv = 2200; points[4].frequency_khz = 12000;
    points[5].voltage_mv = 1800; points[5].frequency_khz = 4000;
    points[6].voltage_mv = 1500; points[6].frequency_khz = 1000;
    points[7].voltage_mv = 1200; points[7].frequency_khz = 100;

    lp_dvfs_init(&ctx, points, 8, DVFS_POLICY_BALANCED);

    printf("  Configured %u operating points:\n", 8);
    display_operating_point("Point 0 (Max Perf)", 3300, 72000);
    display_operating_point("Point 1", 3000, 48000);
    display_operating_point("Point 2", 2700, 36000);
    display_operating_point("Point 3", 2500, 24000);
    display_operating_point("Point 4", 2200, 12000);
    display_operating_point("Point 5", 1800, 4000);
    display_operating_point("Point 6", 1500, 1000);
    display_operating_point("Point 7 (Min Power)", 1200, 100);
    printf("\n");

    /* Demonstrate power relationship */
    /* 演示功耗关系 */
    demonstrate_power_relationship();

    /* Demonstrate different policies */
    /* 演示不同策略 */
    printf("[2] DVFS Policy Comparison\n");
    printf("[2] DVFS策略对比\n");
    printf("----------------------------------------\n");

    dvfs_policy_t policies[] = {
        DVFS_POLICY_MANUAL,
        DVFS_POLICY_AGGRESSIVE,
        DVFS_POLICY_BALANCED,
        DVFS_POLICY_EFFICIENT
    };
    const char *policy_names[] = {
        "MANUAL", "AGGRESSIVE", "BALANCED", "EFFICIENT"
    };

    for (int p = 0; p < 4; p++) {
        low_power_context_t policy_ctx;
        lp_init(&policy_ctx);
        lp_dvfs_init(&policy_ctx, points, 8, policies[p]);
        demonstrate_policy(&policy_ctx, policies[p], policy_names[p]);
    }

    /* Demonstrate transition sequence */
    /* 演示转换序列 */
    printf("[3] DVFS Transition Safety\n");
    printf("[3] DVFS转换安全性\n");
    printf("----------------------------------------\n");

    low_power_context_t transition_ctx;
    lp_init(&transition_ctx);
    lp_dvfs_init(&transition_ctx, points, 8, DVFS_POLICY_BALANCED);
    demonstrate_transition_sequence(&transition_ctx);

    /* Energy savings calculation */
    /* 能耗节省计算 */
    printf("[4] Energy Savings Analysis\n");
    printf("[4] 能耗节省分析\n");
    printf("----------------------------------------\n");

    uint32_t base_power = lp_calc_dynamic_power(0.1f, 50.0f, 3300, 72000);
    uint32_t optimized_power = lp_calc_dynamic_power(0.1f, 50.0f, 1800, 4000);

    printf("  Baseline: 3.3V / 72MHz = %u uW\n", base_power);
    printf("  Optimized: 1.8V / 4MHz = %u uW\n", optimized_power);

    uint32_t savings = base_power > optimized_power ? base_power - optimized_power : 0;
    float savings_pct = (float)savings / base_power * 100.0f;

    printf("  Savings: %u uW (%.1f%%)\n", savings, savings_pct);

    /* Energy for a 1-second operation */
    /* 1秒操作的能耗 */
    uint32_t base_energy = lp_calc_energy(base_power, 1000);
    uint32_t optimized_energy = lp_calc_energy(optimized_power, 1000);

    printf("\n  For 1 second of operation:\n");
    printf("  For 1秒操作：\n");
    printf("    Baseline energy:     %u uJ = %.2f mJ\n",
           base_energy, (float)base_energy / 1000.0f);
    printf("    Optimized energy:    %u uJ = %.2f mJ\n",
           optimized_energy, (float)optimized_energy / 1000.0f);
    printf("    Energy saved:        %u uJ = %.2f mJ\n",
           base_energy - optimized_energy,
           (float)(base_energy - optimized_energy) / 1000.0f);
    printf("\n");

    printf("Demo complete! / 演示完成！\n");
    return 0;
}
