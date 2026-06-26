/**
 * wakeup_demo.c - Wake-up Source Handling Demo
 *
 * 唤醒源处理演示
 *
 * This demo demonstrates wake-up source configuration and handling:
 * 本演示说明唤醒源配置和处理：
 *
 * 1. Configuring multiple wake-up sources
 *    配置多个唤醒源
 * 2. Simulating wake-up events
 *    模拟唤醒事件
 * 3. Priority-based wake-up selection
 *    基于优先级的唤醒选择
 * 4. Context save/restore during wake-up
 *    唤醒期间的上下文保存/恢复
 */

#include <stdio.h>
#include <string.h>
#include "../include/low_power.h"

/**
 * Simulate a periodic task that goes to sleep between iterations
 * 模拟在迭代之间进入睡眠的周期任务
 */
void periodic_task(low_power_context_t *ctx, int iterations) {
    printf("\n--- Periodic Task: %d iterations\n", iterations);
    printf("--- 周期任务：%d 次迭代\n", iterations);

    for (int i = 0; i < iterations; i++) {
        /* Active phase: do work */
        /* 活动阶段：工作 */
        printf("\n  [Iteration %d] ACTIVE PHASE\n", i + 1);
        printf("  [迭代 %d] 活动阶段\n", i + 1);

        /* Simulate work */
        /* 模拟工作 */
        lp_record_sample(ctx, 15000, 3300, i * 100);
        printf("    Processing sensor data... (15000 uA)\n");
        printf("    处理传感器数据...\n");

        /* Sleep phase: enter deep sleep with wake-up configured */
        /* 睡眠阶段：进入已配置唤醒的深度睡眠 */
        printf("    Entering deep sleep...\n");
        printf("    进入深度睡眠...\n");

        /* Configure RTC wake-up for next iteration */
        /* 为下次迭代配置实时时钟唤醒 */
        wakeup_source_config_t rtc_cfg = {
            .source = WAKEUP_SOURCE_RTC,
            .enabled = true,
            .configuration = (i + 2) * 1000,  /* Wake every N seconds */
            .pending = (i < iterations - 1),   /* Only pending for next iterations */
            .clear_on_wake = true
        };
        lp_configure_wakeup(ctx, WAKEUP_SOURCE_RTC, &rtc_cfg);

        /* Enter deep sleep */
        /* 进入深度睡眠 */
        lp_switch_mode(ctx, POWER_MODE_DEEP_SLEEP);
    printf("    Deep sleep current: %u uA\n", ctx->current_mode.current_uA);
    printf("    深度睡眠电流： %u uA\n", ctx->current_mode.current_uA);

        /* Simulate wake-up */
        /* 模拟唤醒 */
        if (lp_has_pending_wakeup(ctx)) {
            wakeup_source_t woke = lp_process_wakeups(ctx);
            printf("    Woke up from: ");
            switch (woke) {
                case WAKEUP_SOURCE_RTC:
                    printf("RTC Alarm\n");
                    break;
                case WAKEUP_SOURCE_PIN:
                    printf("Pin Interrupt\n");
                    break;
                default:
                    printf("Unknown\n");
                    break;
            }
            printf("    从...唤醒：");

            switch (woke) {
                case WAKEUP_SOURCE_RTC:
                    printf("实时时钟报警\n");
                    break;
                case WAKEUP_SOURCE_PIN:
                    printf("引脚中断\n");
                    break;
                default:
                    printf("未知\n");
                    break;
            }

            /* Return to active */
            /* 返回活动状态 */
            lp_switch_mode(ctx, POWER_MODE_ACTIVE);
            printf("    Active current: %u uA\n", ctx->current_mode.current_uA);
            printf("    活动电流： %u uA\n", ctx->current_mode.current_uA);
        }
    }
}

/**
 * Demo multiple wake-up sources
 * 演示多个唤醒源
 */
int main(void) {
    printf("========================================\n");
    printf("  Wake-up Source Handling Demo\n");
    printf("  唤醒源处理演示\n");
    printf("========================================\n\n");

    low_power_context_t ctx;
    lp_init(&ctx);

    /* Configure multiple wake-up sources */
    /* 配置多个唤醒源 */
    printf("[1] Configuring Wake-up Sources\n");
    printf("[1] 配置唤醒源\n");
    printf("----------------------------------------\n");

    /* Pin interrupt wake-up (fastest) */
    /* 引脚中断唤醒（最快） */
    wakeup_source_config_t pin_cfg = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x03,  /* Pin 3, falling edge */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &pin_cfg);
    printf("  [OK] Pin Interrupt (fastest wake: ~2us)\n");
    printf("  [已配置] 引脚中断（最快唤醒：~2us）\n");

    /* RTC wake-up (precise timing) */
    /* 实时时钟唤醒（精确定时） */
    wakeup_source_config_t rtc_cfg = {
        .source = WAKEUP_SOURCE_RTC,
        .enabled = true,
        .configuration = 32768,  /* 32.768 kHz */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_RTC, &rtc_cfg);
    printf("  [OK] RTC Alarm (precise timing)\n");
    printf("  [已配置] 实时时钟报警（精确定时）\n");

    /* UART wake-up (data-driven) */
    /* 串口唤醒（数据驱动） */
    wakeup_source_config_t uart_cfg = {
        .source = WAKEUP_SOURCE_UART,
        .enabled = true,
        .configuration = 0x01,  /* UART0, any character */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_UART, &uart_cfg);
    printf("  [OK] UART Receive (data-driven wake)\n");
    printf("  [已配置] 串口接收（数据驱动唤醒）\n");

    /* Timer wake-up (flexible) */
    /* 定时器唤醒（灵活） */
    wakeup_source_config_t timer_cfg = {
        .source = WAKEUP_SOURCE_TIMER,
        .enabled = true,
        .configuration = 1000000,  /* 1 second at 1MHz */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_TIMER, &timer_cfg);
    printf("  [OK] Timer (flexible interval)\n");
    printf("  [已配置] 定时器（灵活间隔）\n");

    /* Comparator wake-up (event-driven) */
    /* 比较器唤醒（事件驱动） */
    wakeup_source_config_t comp_cfg = {
        .source = WAKEUP_SOURCE_COMPARATOR,
        .enabled = true,
        .configuration = 0x01,  /* Comparator 0 */
        .pending = false,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_COMPARATOR, &comp_cfg);
    printf("  [OK] Comparator (event-driven)\n");
    printf("  [已配置] 比较器（事件驱动）\n");

    printf("\n  Total configured sources: 5\n");
    printf("  总配置源数：5\n");
    printf("\n");

    /* Demo 1: RTC-based periodic wake-up */
    /* 演示1：基于实时时钟的周期唤醒 */
    printf("[2] Demo: RTC Periodic Wake-up\n");
    printf("[2] 演示：实时时钟周期唤醒\n");
    printf("----------------------------------------\n");
    periodic_task(&ctx, 3);

    /* Demo 2: Pin interrupt wake-up */
    /* 演示2：引脚中断唤醒 */
    printf("\n[3] Demo: Pin Interrupt Wake-up\n");
    printf("[3] 演示：引脚中断唤醒\n");
    printf("----------------------------------------\n");

    /* Clear previous wake-ups */
    /* 清除之前的唤醒 */
    ctx.wakeup_mgr.wakeup_count = 0;
    memset(ctx.wakeup_mgr.sources, 0, sizeof(ctx.wakeup_mgr.sources));

    /* Re-enable only pin interrupt */
    /* 仅重新启用引脚中断 */
    wakeup_source_config_t pin_only = {
        .source = WAKEUP_SOURCE_PIN,
        .enabled = true,
        .configuration = 0x01,
        .pending = true,  /* Simulate pin going high */
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_PIN, &pin_only);

    /* Enter sleep */
    /* 进入睡眠 */
    lp_switch_mode(&ctx, POWER_MODE_SLEEP);
    printf("  In sleep mode, current: %u uA\n", ctx.current_mode.current_uA);
    printf("  在睡眠模式，电流： %u uA\n", ctx.current_mode.current_uA);

    /* Simulate pin interrupt */
    /* 模拟引脚中断 */
    printf("  [Simulated] Pin 1 goes HIGH...\n");
    printf("  [模拟] 引脚1变高...\n");

    if (lp_has_pending_wakeup(&ctx)) {
        lp_process_wakeups(&ctx);
        printf("  Woke up from pin interrupt!\n");
        printf("  从引脚中断唤醒！\n");
    }

    lp_switch_mode(&ctx, POWER_MODE_ACTIVE);
    printf("  Back to active, current: %u uA\n", ctx.current_mode.current_uA);
    printf("  返回活动，电流： %u uA\n", ctx.current_mode.current_uA);
    printf("\n");

    /* Demo 3: Multiple simultaneous wake-up sources */
    /* 演示3：多个同时唤醒源 */
    printf("[4] Demo: Multiple Simultaneous Wake-up Sources\n");
    printf("[4] 演示：多个同时唤醒源\n");
    printf("----------------------------------------\n");

    /* Clear and configure multiple sources */
    /* 清除并配置多个源 */
    ctx.wakeup_mgr.wakeup_count = 0;
    memset(ctx.wakeup_mgr.sources, 0, sizeof(ctx.wakeup_mgr.sources));

    wakeup_source_config_t multi_rtc = {
        .source = WAKEUP_SOURCE_RTC,
        .enabled = true,
        .configuration = 1000,
        .pending = true,
        .clear_on_wake = false
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_RTC, &multi_rtc);

    wakeup_source_config_t multi_uart = {
        .source = WAKEUP_SOURCE_UART,
        .enabled = true,
        .configuration = 0x01,
        .pending = true,
        .clear_on_wake = false
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_UART, &multi_uart);

    wakeup_source_config_t multi_timer = {
        .source = WAKEUP_SOURCE_TIMER,
        .enabled = true,
        .configuration = 500000,
        .pending = true,
        .clear_on_wake = true
    };
    lp_configure_wakeup(&ctx, WAKEUP_SOURCE_TIMER, &multi_timer);

    /* Enter sleep with multiple wake sources */
    /* 使用多个唤醒源进入睡眠 */
    lp_switch_mode(&ctx, POWER_MODE_DEEP_SLEEP);
    printf("  In deep sleep with 3 wake-up sources...\n");
    printf("  在深度睡眠中有3个唤醒源...\n");
    printf("  Current: %u uA\n", ctx.current_mode.current_uA);
    printf("  电流： %u uA\n", ctx.current_mode.current_uA);

    /* Process all wake-up sources */
    /* 处理所有唤醒源 */
    wakeup_source_t last = lp_process_wakeups(&ctx);
    printf("\n  Processed wake-up sources:\n");
    printf("  已处理的唤醒源：\n");

    for (int i = WAKEUP_SOURCE_PIN; i < WAKEUP_SOURCE_MAX; i++) {
        if (ctx.wakeup_mgr.sources[i].enabled) {
            printf("    - ");
            switch ((wakeup_source_t)i) {
                case WAKEUP_SOURCE_PIN:        printf("Pin Interrupt"); break;
                case WAKEUP_SOURCE_RTC:        printf("RTC Alarm"); break;
                case WAKEUP_SOURCE_UART:       printf("UART"); break;
                case WAKEUP_SOURCE_TIMER:      printf("Timer"); break;
                default:                       printf("Unknown"); break;
            }
            printf(" (pending: %s)\n",
                   ctx.wakeup_mgr.sources[i].pending ? "YES" : "no");
        }
    }

    printf("\n  Last wake-up source (highest priority): ");
    switch (last) {
        case WAKEUP_SOURCE_PIN:        printf("Pin Interrupt\n"); break;
        case WAKEUP_SOURCE_RTC:        printf("RTC Alarm\n"); break;
        case WAKEUP_SOURCE_UART:       printf("UART\n"); break;
        case WAKEUP_SOURCE_TIMER:      printf("Timer\n"); break;
        default:                       printf("None\n"); break;
    }

    printf("  Total wake-ups: %u\n", ctx.wakeup_mgr.wakeup_count);
    printf("  总唤醒次数： %u\n", ctx.wakeup_mgr.wakeup_count);
    printf("\n");

    /* Summary */
    printf("[5] Wake-up Source Summary\n");
    printf("[5] 唤醒源摘要\n");
    printf("----------------------------------------\n");
    printf("  Wake-up Source          | Latency    | Power Impact\n");
    printf("  ------------------------|------------|-------------\n");
    printf("  Pin Interrupt           | ~2 us      | Minimal\n");
    printf("  RTC Alarm               | ~5 us      | Low\n");
    printf("  Timer                   | ~10 us     | Medium\n");
    printf("  UART / I2C / SPI        | ~20 us     | Medium\n");
    printf("  Comparator              | ~5 us      | Low\n");
    printf("\n  Note: Latencies are approximate and depend on hardware.\n");
    printf("  注意：延迟是近似值，取决于硬件。\n");
    printf("\nDemo complete! / 演示完成！\n");
    return 0;
}
