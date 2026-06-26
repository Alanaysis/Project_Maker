/**
 * test_low_power.c - Unit Tests for Low-Power Framework
 *
 * 低功耗框架单元测试
 *
 * This file contains unit tests for all low-power framework modules.
 * 本文件包含所有低功耗框架模块的单元测试。
 */

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "../include/low_power.h"

/* Test counters */
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  Test: %s ... ", #name)
#define PASS() do { printf("PASS\n"); tests_passed++; } while(0)
#define FAIL(msg) do { printf("FAIL: %s\n", msg); tests_failed++; } while(0)

/* ======================================================================
 * Initialization Tests / 初始化测试
 * ====================================================================== */

void test_init(void) {
    TEST(lp_init);

    low_power_context_t ctx;
    int ret = lp_init(&ctx);
    if (ret != 0) { FAIL("init returned non-zero"); return; }
    if (!ctx.is_initialized) { FAIL("not initialized"); return; }
    if (ctx.current_mode.mode != POWER_MODE_ACTIVE) { FAIL("wrong default mode"); return; }
    if (ctx.current_mode.voltage_mv != 3300) { FAIL("wrong default voltage"); return; }
    if (ctx.current_mode.clock_freq_khz != 72000) { FAIL("wrong default freq"); return; }
    PASS();
}

void test_init_null(void) {
    TEST(lp_init_null);

    int ret = lp_init(NULL);
    if (ret != -1) { FAIL("should return -1 for null"); return; }
    PASS();
}

/* ======================================================================
 * Power Mode Tests / 功耗模式测试
 * ====================================================================== */

void test_mode_config(void) {
    TEST(lp_get_mode_config);

    power_mode_config_t config;

    /* Test each mode */
    lp_get_mode_config(POWER_MODE_ACTIVE, &config);
    if (config.voltage_mv != 3300) { FAIL("active voltage"); return; }
    if (config.clock_freq_khz != 72000) { FAIL("active freq"); return; }
    if (!config.ram_retention) { FAIL("active ram retain"); return; }

    lp_get_mode_config(POWER_MODE_IDLE, &config);
    if (config.current_uA >= 20000) { FAIL("idle too high"); return; }

    lp_get_mode_config(POWER_MODE_SLEEP, &config);
    if (config.clock_freq_khz != 0) { FAIL("sleep should have 0 freq"); return; }
    if (!config.ram_retention) { FAIL("sleep should retain RAM"); return; }

    lp_get_mode_config(POWER_MODE_DEEP_SLEEP, &config);
    if (config.ram_retention) { FAIL("deep sleep should not retain RAM"); return; }
    if (config.current_uA >= 100) { FAIL("deep sleep too high"); return; }

    lp_get_mode_config(POWER_MODE_STANDBY, &config);
    if (!config.rtc_running) { FAIL("standby should have RTC"); return; }

    lp_get_mode_config(POWER_MODE_OFF, &config);
    if (config.current_uA != 0) { FAIL("off should have 0 current"); return; }

    PASS();
}

void test_mode_name(void) {
    TEST(lp_mode_name);

    if (strcmp(lp_mode_name(POWER_MODE_ACTIVE), "ACTIVE") != 0) { FAIL("active name"); return; }
    if (strcmp(lp_mode_name(POWER_MODE_IDLE), "IDLE") != 0) { FAIL("idle name"); return; }
    if (strcmp(lp_mode_name(POWER_MODE_SLEEP), "SLEEP") != 0) { FAIL("sleep name"); return; }
    if (strcmp(lp_mode_name(POWER_MODE_DEEP_SLEEP), "DEEP_SLEEP") != 0) { FAIL("deep name"); return; }
    if (strcmp(lp_mode_name(POWER_MODE_STANDBY), "STANDBY") != 0) { FAIL("standby name"); return; }
    if (strcmp(lp_mode_name(POWER_MODE_OFF), "OFF") != 0) { FAIL("off name"); return; }

    PASS();
}

void test_mode_switch(void) {
    TEST(lp_switch_mode);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Test switching to each mode */
    int ret = lp_switch_mode(&ctx, POWER_MODE_ACTIVE);
    if (ret != 0) { FAIL("switch to active"); return; }

    ret = lp_switch_mode(&ctx, POWER_MODE_IDLE);
    if (ret != 0) { FAIL("switch to idle"); return; }
    if (ctx.current_mode.mode != POWER_MODE_IDLE) { FAIL("mode not updated"); return; }

    ret = lp_switch_mode(&ctx, POWER_MODE_SLEEP);
    if (ret != 0) { FAIL("switch to sleep"); return; }

    ret = lp_switch_mode(&ctx, POWER_MODE_DEEP_SLEEP);
    if (ret != 0) { FAIL("switch to deep sleep"); return; }

    ret = lp_switch_mode(&ctx, POWER_MODE_STANDBY);
    if (ret != 0) { FAIL("switch to standby"); return; }

    ret = lp_switch_mode(&ctx, POWER_MODE_OFF);
    if (ret != 0) { FAIL("switch to off"); return; }

    /* Test invalid mode */
    ret = lp_switch_mode(&ctx, (power_mode_t)99);
    if (ret != -1) { FAIL("should reject invalid mode"); return; }

    PASS();
}

/* ======================================================================
 * Clock Gating Tests / 时钟门控测试
 * ====================================================================== */

void test_clock_gate(void) {
    TEST(lp_clock_gate);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* All should be enabled initially */
    if (ctx.clock_gating.active_count != CLOCK_PERIPH_MAX) {
        FAIL("should start with all clocks enabled"); return;
    }

    /* Disable some clocks */
    int ret = lp_clock_gate(&ctx, CLOCK_PERIPH_SPI, false);
    if (ret != 0) { FAIL("gate SPI"); return; }

    ret = lp_clock_gate(&ctx, CLOCK_PERIPH_USB, false);
    if (ret != 0) { FAIL("gate USB"); return; }

    if (ctx.clock_gating.gate_count != 2) { FAIL("wrong gate count"); return; }
    if (ctx.clock_gating.active_count != CLOCK_PERIPH_MAX - 2) {
        FAIL("wrong active count"); return;
    }

    /* Re-enable */
    ret = lp_clock_gate(&ctx, CLOCK_PERIPH_SPI, true);
    if (ret != 0) { FAIL("ungate SPI"); return; }

    if (ctx.clock_gating.gate_count != 1) { FAIL("gate count after ungate"); return; }

    /* Test invalid peripheral */
    ret = lp_clock_gate(&ctx, (clock_periph_t)99, true);
    if (ret != -1) { FAIL("should reject invalid peripheral"); return; }

    PASS();
}

void test_clock_stats(void) {
    TEST(lp_get_clock_stats);

    low_power_context_t ctx;
    lp_init(&ctx);

    clock_gate_state_t stats = lp_get_clock_stats(&ctx);
    if (stats.active_count != CLOCK_PERIPH_MAX) { FAIL("stats active count"); return; }
    if (stats.gate_count != 0) { FAIL("stats gate count"); return; }

    PASS();
}

/* ======================================================================
 * Peripheral Power Tests / 外设电源测试
 * ====================================================================== */

void test_peripheral_power(void) {
    TEST(lp_peripheral_power);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* All domains powered initially */
    if (ctx.periph_power.active_domains != ((1 << POWER_DOMAIN_PERIPH_MAX) - 1)) {
        FAIL("should start with all domains powered"); return;
    }

    /* Power off a domain */
    int ret = lp_peripheral_power(&ctx, POWER_DOMAIN_PERIPH_USB, false);
    if (ret != 0) { FAIL("power off USB"); return; }

    if (ctx.periph_power.powered[POWER_DOMAIN_PERIPH_USB] != false) {
        FAIL("USB should be powered off"); return;
    }

    /* Power back on */
    ret = lp_peripheral_power(&ctx, POWER_DOMAIN_PERIPH_USB, true);
    if (ret != 0) { FAIL("power on USB"); return; }

    /* Test invalid domain */
    ret = lp_peripheral_power(&ctx, (power_domain_t)99, true);
    if (ret != -1) { FAIL("should reject invalid domain"); return; }

    PASS();
}

/* ======================================================================
 * Wake-up Source Tests / 唤醒源测试
 * ====================================================================== */

void test_wakeup_configure(void) {
    TEST(lp_configure_wakeup);

    low_power_context_t ctx;
    lp_init(&ctx);

    wakeup_source_config_t config = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x01,
        .pending = false,
        .clear_on_wake = true
    };

    int ret = lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &config);
    if (ret != 0) { FAIL("configure pin wakeup"); return; }

    if (!ctx.wakeup_mgr.sources[WAKEUP_SOURCE_PIN].enabled) {
        FAIL("pin wakeup not enabled"); return;
    }

    /* Test null config */
    ret = lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, NULL);
    if (ret != -1) { FAIL("should reject null config"); return; }

    /* Test invalid source */
    ret = lp_configure_wakeup(&ctx, (wakeup_source_t)99, &config);
    if (ret != -1) { FAIL("should reject invalid source"); return; }

    PASS();
}

void test_wakeup_process(void) {
    TEST(lp_process_wakeup);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Configure a pending wake-up source */
    wakeup_source_config_t config = {
        .source = WAKEUP_SOURCE_RTC,
        .enabled = true,
        .configuration = 1000,
        .pending = true,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_RTC, &config);

    /* Process wake-ups */
    wakeup_source_t woke = lp_process_wakeups(&ctx);
    if (woke != WAKEUP_SOURCE_RTC) { FAIL("wrong wake source"); return; }
    if (ctx.wakeup_mgr.wakeup_count != 1) { FAIL("wakeup count"); return; }

    /* Should not be pending anymore (clear_on_wake = true) */
    if (ctx.wakeup_mgr.sources[WAKEUP_SOURCE_RTC].pending) {
        FAIL("should be cleared"); return;
    }

    PASS();
}

void test_has_pending_wakeup(void) {
    TEST(lp_has_pending_wakeup);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* No pending initially */
    if (lp_has_pending_wakeup(&ctx) != false) { FAIL("should have no pending"); return; }

    /* Configure a pending source */
    wakeup_source_config_t config = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x01,
        .pending = true,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &config);

    if (lp_has_pending_wakeup(&ctx) != true) { FAIL("should have pending"); return; }

    PASS();
}

/* ======================================================================
 * DVFS Tests / DVFS测试
 * ====================================================================== */

void test_dvfs_init(void) {
    TEST(lp_dvfs_init);

    low_power_context_t ctx;
    lp_init(&ctx);

    dvfs_operating_point_t points[4];
    memset(points, 0, sizeof(points));

    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;
    points[1].voltage_mv = 2700; points[1].frequency_khz = 36000;
    points[2].voltage_mv = 2200; points[2].frequency_khz = 12000;
    points[3].voltage_mv = 1800; points[3].frequency_khz = 4000;

    int ret = lp_dvfs_init(&ctx, points, 4, DVFS_POLICY_BALANCED);
    if (ret != 0) { FAIL("dvfs init"); return; }

    if (ctx.dvfs.num_points != 4) { FAIL("wrong point count"); return; }
    if (ctx.dvfs.policy != DVFS_POLICY_BALANCED) { FAIL("wrong policy"); return; }
    if (!ctx.dvfs.current_point.is_valid) { FAIL("current point invalid"); return; }

    PASS();
}

void test_dvfs_init_invalid(void) {
    TEST(lp_dvfs_init_invalid);

    low_power_context_t ctx;
    lp_init(&ctx);

    dvfs_operating_point_t points[4];
    memset(points, 0, sizeof(points));
    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;

    /* Too many points */
    int ret = lp_dvfs_init(&ctx, points, 9, DVFS_POLICY_BALANCED);
    if (ret != -1) { FAIL("should reject too many points"); return; }

    /* Null points */
    ret = lp_dvfs_init(&ctx, NULL, 4, DVFS_POLICY_BALANCED);
    if (ret != -1) { FAIL("should reject null points"); return; }

    /* Zero points */
    ret = lp_dvfs_init(&ctx, points, 0, DVFS_POLICY_BALANCED);
    if (ret != -1) { FAIL("should reject zero points"); return; }

    PASS();
}

void test_dvfs_switch(void) {
    TEST(lp_dvfs_switch);

    low_power_context_t ctx;
    lp_init(&ctx);

    dvfs_operating_point_t points[4];
    memset(points, 0, sizeof(points));

    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;
    points[1].voltage_mv = 2700; points[1].frequency_khz = 36000;
    points[2].voltage_mv = 2200; points[2].frequency_khz = 12000;
    points[3].voltage_mv = 1800; points[3].frequency_khz = 4000;

    lp_dvfs_init(&ctx, points, 4, DVFS_POLICY_BALANCED);

    /* Switch to different points */
    int ret = lp_dvfs_switch(&ctx, 0);
    if (ret != 0) { FAIL("switch to point 0"); return; }
    if (ctx.dvfs.current_point.voltage_mv != 3300) { FAIL("wrong voltage"); return; }

    ret = lp_dvfs_switch(&ctx, 3);
    if (ret != 0) { FAIL("switch to point 3"); return; }
    if (ctx.dvfs.current_point.voltage_mv != 1800) { FAIL("wrong voltage"); return; }

    /* Invalid point index */
    ret = lp_dvfs_switch(&ctx, 10);
    if (ret != -1) { FAIL("should reject invalid index"); return; }

    PASS();
}

/* ======================================================================
 * Power Monitoring Tests / 功耗监测测试
 * ====================================================================== */

void test_power_monitor(void) {
    TEST(lp_record_sample);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Record samples */
    lp_record_sample(&ctx, 20000, 3300, 0);
    lp_record_sample(&ctx, 15000, 3300, 10);
    lp_record_sample(&ctx, 10000, 3300, 20);

    energy_profile_t profile = lp_get_energy_profile(&ctx);
    if (profile.avg_current_uA != 15000) { FAIL("wrong avg current"); return; }
    if (profile.peak_current_uA != 20000) { FAIL("wrong peak current"); return; }
    if (profile.min_current_uA != 10000) { FAIL("wrong min current"); return; }

    PASS();
}

void test_power_monitor_overflow(void) {
    TEST(lp_record_sample_overflow);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Fill buffer to capacity */
    for (int i = 0; i < 200; i++) {
        lp_record_sample(&ctx, 10000 + i, 3300, i);
    }

    /* Buffer should handle overflow gracefully */
    energy_profile_t profile = lp_get_energy_profile(&ctx);
    if (profile.avg_current_uA == 0) { FAIL("profile should not be empty"); return; }

    PASS();
}

/* ======================================================================
 * Utility Function Tests / 工具函数测试
 * ====================================================================== */

void test_dynamic_power_calculation(void) {
    TEST(lp_calc_dynamic_power);

    /* P = alpha * C * V^2 * f
     * alpha=0.1, C=50pF, V=3.3V, f=72MHz
     * P = 0.1 * 50e-12 * 3.3^2 * 72e6 * 1e6 = 0.1 * 50e-12 * 10.89 * 72e6 * 1e6
     * = 0.1 * 50e-12 * 10.89 * 72e12 = 0.1 * 50 * 10.89 * 72 = 3920.4 uW
     */
    uint32_t power = lp_calc_dynamic_power(0.1f, 50.0f, 3300, 72000);

    /* Allow some tolerance for floating point */
    if (power < 3900 || power > 4000) {
        char msg[64];
        snprintf(msg, sizeof(msg), "wrong power: %u (expected ~3920)", power);
        FAIL(msg); return;
    }

    /* Test with zero voltage */
    uint32_t zero_power = lp_calc_dynamic_power(0.1f, 50.0f, 0, 72000);
    if (zero_power != 0) { FAIL("zero voltage should give zero power"); return; }

    /* Test with zero frequency */
    zero_power = lp_calc_dynamic_power(0.1f, 50.0f, 3300, 0);
    if (zero_power != 0) { FAIL("zero frequency should give zero power"); return; }

    PASS();
}

void test_energy_calculation(void) {
    TEST(lp_calc_energy);

    /* E = P * t
     * P = 1000 uW, t = 1000 ms
     * E = 1,000,000 uJ
     */
    uint32_t energy = lp_calc_energy(1000, 1000);
    if (energy != 1000000) {
        char msg[64];
        snprintf(msg, sizeof(msg), "wrong energy: %u (expected 1000000)", energy);
        FAIL(msg); return;
    }

    /* Test with zero power */
    uint32_t zero_energy = lp_calc_energy(0, 1000);
    if (zero_energy != 0) { FAIL("zero power should give zero energy"); return; }

    PASS();
}

/* ======================================================================
 * Integration Test / 集成测试
 * ====================================================================== */

void test_full_workflow(void) {
    TEST(lp_full_workflow);

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Set up DVFS */
    dvfs_operating_point_t points[4];
    memset(points, 0, sizeof(points));
    points[0].voltage_mv = 3300; points[0].frequency_khz = 72000;
    points[1].voltage_mv = 2700; points[1].frequency_khz = 36000;
    points[2].voltage_mv = 2200; points[2].frequency_khz = 12000;
    points[3].voltage_mv = 1800; points[3].frequency_khz = 4000;
    lp_dvfs_init(&ctx, points, 4, DVFS_POLICY_BALANCED);

    /* Configure wake-up sources */
    wakeup_source_config_t pin_cfg = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x01,
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &pin_cfg);

    /* Clock gating */
    lp_clock_gate(&ctx, CLOCK_PERIPH_SPI, false);
    lp_clock_gate(&ctx, CLOCK_PERIPH_USB, false);

    /* Power domain control */
    lp_peripheral_power(&ctx, POWER_DOMAIN_PERIPH_USB, false);

    /* Mode switching cycle */
    lp_switch_mode(&ctx, POWER_MODE_ACTIVE);
    lp_record_sample(&ctx, 18000, 3300, 0);

    lp_switch_mode(&ctx, POWER_MODE_DEEP_SLEEP);
    lp_record_sample(&ctx, 10, 0, 100);

    /* DVFS switching */
    lp_dvfs_switch(&ctx, 0);
    lp_dvfs_switch(&ctx, 3);

    /* Process wake-ups */
    wakeup_source_t woke = lp_process_wakeups(&ctx);
    (void)woke;

    /* Get profile */
    energy_profile_t profile = lp_get_energy_profile(&ctx);
    if (profile.avg_current_uA == 0) { FAIL("profile should have data"); return; }

    PASS();
}

/* ======================================================================
 * Main / 主函数
 * ====================================================================== */

int main(void) {
    printf("========================================\n");
    printf("  Low-Power Framework Unit Tests\n");
    printf("  低功耗框架单元测试\n");
    printf("========================================\n\n");

    /* Run all tests */
    printf("[Initialization / 初始化]\n");
    test_init();
    test_init_null();

    printf("\n[Power Modes / 功耗模式]\n");
    test_mode_config();
    test_mode_name();
    test_mode_switch();

    printf("\n[Clock Gating / 时钟门控]\n");
    test_clock_gate();
    test_clock_stats();

    printf("\n[Peripheral Power / 外设电源]\n");
    test_peripheral_power();

    printf("\n[Wake-up Sources / 唤醒源]\n");
    test_wakeup_configure();
    test_wakeup_process();
    test_has_pending_wakeup();

    printf("\n[DVFS / DVFS]\n");
    test_dvfs_init();
    test_dvfs_init_invalid();
    test_dvfs_switch();

    printf("\n[Power Monitoring / 功耗监测]\n");
    test_power_monitor();
    test_power_monitor_overflow();

    printf("\n[Utility Functions / 工具函数]\n");
    test_dynamic_power_calculation();
    test_energy_calculation();

    printf("\n[Integration / 集成]\n");
    test_full_workflow();

    /* Summary */
    printf("\n========================================\n");
    printf("  Test Results / 测试结果\n");
    printf("========================================\n");
    printf("  Passed: %d\n", tests_passed);
    printf("  Failed: %d\n", tests_failed);
    printf("  Total:  %d\n", tests_passed + tests_failed);
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
