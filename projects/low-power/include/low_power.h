/**
 * low_power.h - Embedded Low-Power Design Framework Header
 *
 * 嵌入式低功耗设计框架头文件
 *
 * This header defines the core data structures, enums, and API for
 * an embedded low-power design learning framework.
 *
 * 本头文件为嵌入式低功耗设计学习框架定义了核心数据结构、枚举和API。
 *
 * Low-Power Design Theory / 低功耗设计理论:
 * =========================================
 *
 * Power consumption in embedded systems has three main components:
 * 嵌入式系统中功耗有三个主要组成部分：
 *
 * 1. Dynamic Power (动态功耗): P_dyn = alpha * C * V^2 * f
 *    - alpha: switching activity factor (翻转活动因子)
 *    - C: load capacitance (负载电容)
 *    - V: supply voltage (供电电压)
 *    - f: clock frequency (时钟频率)
 *
 * 2. Static Power (静态功耗): P_static = I_leakage * V
 *    - I_leakage: leakage current (漏电流)
 *    - Increases with temperature and process variations
 *
 * 3. Battery/Supply Power (电池/电源功耗): P_supply = P_dyn + P_static
 *
 * Key Low-Power Techniques / 关键低功耗技术:
 * ===========================================
 *
 * - Clock Gating (时钟门控): Disable clocks to idle modules
 * - Power Gating (电源门控): Cut power to entire blocks
 * - Voltage Scaling (电压缩放): Reduce Vdd for lower dynamic power
 * - Frequency Scaling (频率缩放): Reduce f for lower dynamic power
 * - Sleep Modes (睡眠模式): Enter low-power states when idle
 * - DVFS (动态电压频率调节): Joint voltage-frequency optimization
 * - Peripheral Power Control (外设电源控制): Power on/off peripherals
 * - Wake-up Sources (唤醒源): Interrupts/events to exit sleep
 */

#ifndef LOW_POWER_H
#define LOW_POWER_H

#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

/* ======================================================================
 * Power Mode Definitions / 功耗模式定义
 *
 * Power modes represent different trade-offs between power consumption
 * and wake-up latency. Deeper sleep modes save more power but take
 * longer to wake up.
 *
 * 功耗模式代表了功耗和唤醒延迟之间的不同权衡。
 * 更深的睡眠模式节省更多功耗但唤醒时间更长。
 * ====================================================================== */

/**
 * Power mode enumeration
 * 功耗模式枚举
 */
typedef enum {
    POWER_MODE_ACTIVE = 0,    /* 活动模式: Full power, all peripherals running
                                 全功耗，所有外设运行 */
    POWER_MODE_IDLE,          /* 空闲模式: CPU halted, peripherals active
                                 CPU暂停，外设活动 */
    POWER_MODE_SLEEP,         /* 睡眠模式: Clocks gated, RAM retained
                                 时钟门控，RAM保留 */
    POWER_MODE_DEEP_SLEEP,    /* 深度睡眠: Minimal power, RAM lost
                                 最小功耗，RAM丢失 */
    POWER_MODE_STANDBY,       /* 待机模式: RTC running, fast wake
                                 实时时钟运行，快速唤醒 */
    POWER_MODE_OFF            /* 关闭模式: No power, requires reset
                                 无电源，需要复位 */
} power_mode_t;

/**
 * Power mode configuration structure
 * 功耗模式配置结构
 */
typedef struct {
    power_mode_t mode;                    /* Current power mode 当前功耗模式 */
    uint32_t voltage_mv;                  /* Supply voltage in mV 供电电压(mV) */
    uint32_t clock_freq_khz;              /* Clock frequency in kHz 时钟频率(kHz) */
    bool ram_retention;                     /* Whether RAM content is preserved RAM内容是否保留 */
    bool rtc_running;                       /* Whether RTC is running 实时时钟是否运行 */
    bool backup_domain_powered;             /* Whether backup domain is powered 备份域是否供电 */
    uint32_t wake_latency_us;               /* Wake-up time in microseconds 唤醒时间(微秒) */
    uint32_t current_uA;                    /* Estimated current draw in microamps 估计电流(微安) */
} power_mode_config_t;

/* ======================================================================
 * Clock Gating Definitions / 时钟门控定义
 *
 * Clock gating reduces dynamic power by disabling the clock signal
 * to idle peripherals and logic blocks. This is one of the most
 * effective low-power techniques.
 *
 * 时钟门控通过禁用空闲外设和逻辑块的时钟信号来降低动态功耗。
 * 这是最有效的低功耗技术之一。
 * ====================================================================== */

/**
 * Peripheral clock enable/disable
 * 外设时钟使能/禁用
 */
typedef enum {
    CLOCK_PERIPH_GPIO = 0,
    CLOCK_PERIPH_SPI,
    CLOCK_PERIPH_I2C,
    CLOCK_PERIPH_UART,
    CLOCK_PERIPH_TIMERS,
    CLOCK_PERIPH_ADC,
    CLOCK_PERIPH_DAC,
    CLOCK_PERIPH_DMA,
    CLOCK_PERIPH_USB,
    CLOCK_PERIPH_CAN,
    CLOCK_PERIPH_RTC,
    CLOCK_PERIPH_WDT,
    CLOCK_PERIPH_MAX
} clock_periph_t;

/**
 * Clock gating state for all peripherals
 * 所有外设的时钟门控状态
 */
typedef struct {
    bool enabled[CLOCK_PERIPH_MAX];
    uint32_t gate_count;          /* Number of clock gates applied 时钟门控数量 */
    uint32_t active_count;        /* Number of active peripherals 活动外设数量 */
    uint32_t estimated_savings_uA; /* Estimated current savings 估计电流节省 */
} clock_gate_state_t;

/* ======================================================================
 * Peripheral Power Control Definitions / 外设电源控制定义
 *
 * Peripheral power control allows turning off power to entire
 * peripheral blocks when not in use, achieving deeper power savings
 * than clock gating alone.
 *
 * 外设电源控制允许在不使用时关闭整个外设块的电源，
 * 实现比单纯时钟门控更深的功耗节省。
 * ====================================================================== */

/**
 * Peripheral power domain
 * 外设电源域
 */
typedef enum {
    POWER_DOMAIN_PERIPH_AON = 0,  /* Always-on domain 常供电域 */
    POWER_DOMAIN_PERIPH_CORE,     /* Core peripherals 核心外设 */
    POWER_DOMAIN_PERIPH_IO,       /* I/O peripherals I/O外设 */
    POWER_DOMAIN_PERIPH_ADC_DAC,  /* ADC/DAC domain ADC/DAC域 */
    POWER_DOMAIN_PERIPH_USB,      /* USB domain USB域 */
    POWER_DOMAIN_PERIPH_MAX
} power_domain_t;

/**
 * Peripheral power control state
 * 外设电源控制状态
 */
typedef struct {
    bool powered[POWER_DOMAIN_PERIPH_MAX];
    uint32_t active_domains;      /* Bitmask of powered domains 供电域位掩码 */
    uint32_t power_reduction_pct; /* Percentage power reduction 功耗降低百分比 */
} peripheral_power_state_t;

/* ======================================================================
 * Wake-up Source Definitions / 唤醒源定义
 *
 * Wake-up sources are events or signals that can cause the MCU
 * to exit a low-power mode and return to an active state.
 *
 * 唤醒源是可以导致MCU退出低功耗模式并返回活动状态的事件或信号。
 * ====================================================================== */

/**
 * Wake-up source type
 * 唤醒源类型
 */
typedef enum {
    WAKEUP_SOURCE_NONE = 0,
    WAKEUP_SOURCE_PIN,            /* External pin interrupt 外部引脚中断 */
    WAKEUP_SOURCE_RTC,            /* Real-time clock alarm 实时时钟报警 */
    WAKEUP_SOURCE_TIMER,          /* General purpose timer 通用定时器 */
    WAKEUP_SOURCE_UART,           /* UART receive 串口接收 */
    WAKEUP_SOURCE_I2C,            /* I2C start condition I2C起始条件 */
    WAKEUP_SOURCE_SPI,            /* SPI CS assertion SPI片选断言 */
    WAKEUP_SOURCE_DMA,            /* DMA completion DMA完成 */
    WAKEUP_SOURCE_WATCHDOG,       /* Watchdog timeout 看门狗超时 */
    WAKEUP_SOURCE_ADC,            /* ADC conversion complete ADC转换完成 */
    WAKEUP_SOURCE_COMPARATOR,     /* Comparator threshold crossing 比较器阈值跨越 */
    WAKEUP_SOURCE_MAX
} wakeup_source_t;

/**
 * Wake-up source configuration
 * 唤醒源配置
 */
typedef struct {
    wakeup_source_t source;
    bool enabled;
    uint32_t configuration;       /* Source-specific config 源特定配置 */
    bool pending;                 /* Whether this source has triggered 是否已触发 */
    bool clear_on_wake;           /* Whether to clear on wake 唤醒时是否清除 */
} wakeup_source_config_t;

/**
 * Wake-up management state
 * 唤醒管理状态
 */
typedef struct {
    wakeup_source_config_t sources[WAKEUP_SOURCE_MAX];
    wakeup_source_t last_wakeup;  /* Last source that triggered wake 上次唤醒源 */
    uint32_t wakeup_count;        /* Total wake-up count 总唤醒次数 */
} wakeup_manager_t;

/* ======================================================================
 * DVFS (Dynamic Voltage Frequency Scaling) Definitions / DVFS定义
 *
 * DVFS dynamically adjusts the supply voltage and clock frequency
 * based on workload to minimize energy per operation.
 *
 * DVFS根据工作负载动态调整供电电压和时钟频率，
 * 以最小化每次操作的能耗。
 *
 * Key insight: Dynamic power scales with V^2 * f, so reducing
 * voltage has a quadratic effect on power reduction.
 * 关键洞察：动态功耗与 V^2 * f 成正比，降低电压对功耗降低有平方效应。
 * ====================================================================== */

/**
 * DVFS operating point
 * DVFS工作点
 */
typedef struct {
    uint32_t voltage_mv;          /* Supply voltage in mV 供电电压(mV) */
    uint32_t frequency_khz;       /* Clock frequency in kHz 时钟频率(kHz) */
    uint32_t current_uA;          /* Estimated current in uA 估计电流(uA) */
    uint32_t power_uW;            /* Estimated power in uW 估计功耗(uW) */
    uint32_t min_safe_freq;       /* Minimum safe frequency at this voltage 此电压下的最低安全频率 */
    bool is_valid;                /* Whether this operating point is valid 是否有效 */
} dvfs_operating_point_t;

/**
 * DVFS policy configuration
 * DVFS策略配置
 */
typedef enum {
    DVFS_POLICY_MANUAL = 0,       /* Manually set voltage/frequency 手动设置电压/频率 */
    DVFS_POLICY_AGGRESSIVE,       /* Max performance, scale down when idle 最大性能，空闲时降频 */
    DVFS_POLICY_BALANCED,         /* Balance between performance and power 平衡性能和功耗 */
    DVFS_POLICY_EFFICIENT         /* Maximize energy efficiency 最大化能效 */
} dvfs_policy_t;

/**
 * DVFS state machine
 * DVFS状态机
 */
typedef struct {
    dvfs_operating_point_t current_point;   /* Current operating point 当前工作点 */
    dvfs_operating_point_t target_point;    /* Target operating point 目标工作点 */
    dvfs_operating_point_t points[8];       /* Available operating points 可用工作点 */
    uint32_t num_points;                    /* Number of available points 可用点数 */
    dvfs_policy_t policy;                   /* Active DVFS policy 活动DVFS策略 */
    uint32_t transition_count;              /* Number of transitions 转换次数 */
    uint32_t last_switch_time;              /* Last switch timestamp 上次切换时间戳 */
} dvfs_manager_t;

/* ======================================================================
 * Power Monitoring Definitions / 功耗监测定义
 *
 * Power monitoring tracks energy consumption over time to help
 * optimize power usage patterns.
 *
 * 功耗监测跟踪随时间变化的能耗，以帮助优化功耗使用模式。
 * ====================================================================== */

/**
 * Power sample data point
 * 功耗采样数据点
 */
typedef struct {
    uint32_t timestamp_ms;      /* Time in milliseconds 时间(毫秒) */
    uint32_t current_uA;        /* Measured current 测量电流 */
    uint32_t voltage_mv;        /* Measured voltage 测量电压 */
    power_mode_t mode;          /* Current power mode 当前功耗模式 */
    uint32_t clock_freq_khz;    /* Current clock frequency 当前时钟频率 */
    uint32_t active_peripherals; /* Bitmask of active peripherals 活动外设位掩码 */
} power_sample_t;

/**
 * Power monitoring buffer
 * 功耗监测缓冲区
 */
typedef struct {
    power_sample_t samples[128];
    uint32_t head;              /* Write index 写入索引 */
    uint32_t tail;              /* Read index 读取索引 */
    uint32_t count;             /* Number of samples 采样数量 */
    bool is_full;               /* Whether buffer is full 缓冲区是否已满 */
} power_monitor_t;

/* ======================================================================
 * Energy Profiling Definitions / 能耗分析定义
 *
 * Energy profiling provides statistics and analysis of power usage
 * patterns to identify optimization opportunities.
 *
 * 能耗分析提供功耗使用模式的统计和分析，以识别优化机会。
 * ====================================================================== */

/**
 * Energy profiling results
 * 能耗分析结果
 */
typedef struct {
    uint32_t total_energy_mJ;       /* Total energy consumed (mJ) 总能耗(mJ) */
    uint32_t avg_current_uA;        /* Average current draw (uA) 平均电流(uA) */
    uint32_t peak_current_uA;       /* Peak current draw (uA) 峰值电流(uA) */
    uint32_t min_current_uA;        /* Minimum current draw (uA) 最小电流(uA) */
    uint32_t active_time_ms;        /* Time in active mode (ms) 活动模式时间(ms) */
    uint32_t idle_time_ms;          /* Time in idle mode (ms) 空闲模式时间(ms) */
    uint32_t sleep_time_ms;         /* Time in sleep mode (ms) 睡眠模式时间(ms) */
    uint32_t deep_sleep_time_ms;    /* Time in deep sleep (ms) 深度睡眠时间(ms) */
    uint32_t mode_switch_count;     /* Number of mode transitions 模式转换次数 */
    uint32_t energy_per_operation;  /* Energy per operation (uJ) 每次操作能耗(uJ) */
} energy_profile_t;

/* ======================================================================
 * Core Framework State / 核心框架状态
 * ====================================================================== */

/**
 * Main low-power framework context
 * 主低功耗框架上下文
 */
typedef struct {
    power_mode_config_t current_mode;   /* Current power mode config 当前功耗模式配置 */
    clock_gate_state_t clock_gating;    /* Clock gating state 时钟门控状态 */
    peripheral_power_state_t periph_power; /* Peripheral power state 外设电源状态 */
    wakeup_manager_t wakeup_mgr;        /* Wake-up manager 唤醒管理器 */
    dvfs_manager_t dvfs;                /* DVFS manager DVFS管理器 */
    power_monitor_t power_monitor;      /* Power monitor 功耗监测器 */
    energy_profile_t profile;           /* Energy profile 能耗分析 */
    bool is_initialized;                /* Framework initialization flag 框架初始化标志 */
} low_power_context_t;

/* ======================================================================
 * API Functions / API函数
 * ====================================================================== */

/* --- Initialization / 初始化 --- */

/**
 * Initialize the low-power framework
 * 初始化低功耗框架
 *
 * Sets up default configurations for all power management subsystems.
 * 为所有电源管理子系统设置默认配置。
 *
 * @param ctx  Framework context 框架上下文
 * @return     0 on success, -1 on failure
 */
int lp_init(low_power_context_t *ctx);

/* --- Power Mode Management / 功耗模式管理 --- */

/**
 * Get the default configuration for a power mode
 * 获取功耗模式的默认配置
 *
 * @param mode  Target power mode 目标功耗模式
 * @param config  Output configuration 输出配置
 */
void lp_get_mode_config(power_mode_t mode, power_mode_config_t *config);

/**
 * Transition to a new power mode
 * 转换到新的功耗模式
 *
 * Simulates the power mode transition process including:
 * - Disabling unnecessary clocks
 * - Disabling peripherals
 * - Saving/restoring context
 * - Voltage/frequency scaling
 * - Entering/exiting sleep state
 *
 * 模拟功耗模式转换过程，包括：
 * - 禁用不必要的时钟
 * - 禁用外设
 * - 保存/恢复上下文
 * - 电压/频率缩放
 * - 进入/退出睡眠状态
 *
 * @param ctx     Framework context 框架上下文
 * @param target  Target power mode 目标功耗模式
 * @return        0 on success, -1 on failure
 */
int lp_switch_mode(low_power_context_t *ctx, power_mode_t target);

/**
 * Get current power mode string name
 * 获取当前功耗模式的字符串名称
 *
 * @param mode  Power mode 功耗模式
 * @return      String name of the mode 模式的字符串名称
 */
const char *lp_mode_name(power_mode_t mode);

/* --- Clock Gating / 时钟门控 --- */

/**
 * Enable or disable clock for a peripheral
 * 启用或禁用外设的时钟
 *
 * @param ctx     Framework context 框架上下文
 * @param periph  Peripheral to control 控制的外设
 * @param enable  True to enable, false to disable 真使能，假禁用
 * @return        0 on success, -1 on failure
 */
int lp_clock_gate(low_power_context_t *ctx, clock_periph_t periph, bool enable);

/**
 * Get all clock gating statistics
 * 获取所有时钟门控统计信息
 *
 * @param ctx     Framework context 框架上下文
 * @return        Clock gate state 时钟门控状态
 */
clock_gate_state_t lp_get_clock_stats(low_power_context_t *ctx);

/* --- Peripheral Power Control / 外设电源控制 --- */

/**
 * Power on or off a peripheral domain
 * 开启或关闭外设电源域
 *
 * @param ctx     Framework context 框架上下文
 * @param domain  Power domain to control 控制的电源域
 * @param enable  True to power on, false to power off 真上电，假断电
 * @return        0 on success, -1 on failure
 */
int lp_peripheral_power(low_power_context_t *ctx, power_domain_t domain, bool enable);

/* --- Wake-up Source Management / 唤醒源管理 --- */

/**
 * Configure a wake-up source
 * 配置唤醒源
 *
 * @param ctx     Framework context 框架上下文
 * @param source  Wake-up source type 唤醒源类型
 * @param config  Wake-up configuration 唤醒配置
 * @return        0 on success, -1 on failure
 */
int lp_configure_wakeup(low_power_context_t *ctx, wakeup_source_t source,
                        const wakeup_source_config_t *config);

/**
 * Check and process pending wake-up sources
 * 检查并处理待处理的唤醒源
 *
 * @param ctx     Framework context 框架上下文
 * @return        Last wake-up source, or WAKEUP_SOURCE_NONE
 */
wakeup_source_t lp_process_wakeups(low_power_context_t *ctx);

/**
 * Check if any wake-up source is pending
 * 检查是否有任何唤醒源待处理
 *
 * @param ctx     Framework context 框架上下文
 * @return        True if any source is pending 如果有源待处理则为真
 */
bool lp_has_pending_wakeup(low_power_context_t *ctx);

/* --- DVFS Management / DVFS管理 --- */

/**
 * Initialize DVFS with available operating points
 * 使用可用工作点初始化DVFS
 *
 * @param ctx     Framework context 框架上下文
 * @param points  Array of operating points 工作点数组
 * @param count   Number of points 点数
 * @param policy  DVFS policy  DVFS策略
 * @return        0 on success, -1 on failure
 */
int lp_dvfs_init(low_power_context_t *ctx, dvfs_operating_point_t *points,
                 uint32_t count, dvfs_policy_t policy);

/**
 * Set DVFS policy
 * 设置DVFS策略
 *
 * @param ctx     Framework context 框架上下文
 * @param policy  New DVFS policy 新DVFS策略
 * @return        0 on success, -1 on failure
 */
int lp_dvfs_set_policy(low_power_context_t *ctx, dvfs_policy_t policy);

/**
 * Apply DVFS transition to an operating point
 * 应用DVFS转换到工作点
 *
 * @param ctx     Framework context 框架上下文
 * @param point   Target operating point index 目标工作点索引
 * @return        0 on success, -1 on failure
 */
int lp_dvfs_switch(low_power_context_t *ctx, uint32_t point);

/* --- Power Monitoring / 功耗监测 --- */

/**
 * Record a power sample
 * 记录功耗采样
 *
 * @param ctx     Framework context 框架上下文
 * @param current_uA  Measured current 测量电流
 * @param voltage_mv  Measured voltage 测量电压
 * @param timestamp_ms  Timestamp 时间戳
 */
void lp_record_sample(low_power_context_t *ctx, uint32_t current_uA,
                      uint32_t voltage_mv, uint32_t timestamp_ms);

/**
 * Get power monitoring statistics
 * 获取功耗监测统计信息
 *
 * @param ctx     Framework context 框架上下文
 * @return        Energy profile 能耗分析
 */
energy_profile_t lp_get_energy_profile(low_power_context_t *ctx);

/* --- Utility Functions / 工具函数 --- */

/**
 * Calculate dynamic power
 * 计算动态功耗
 *
 * P_dyn = alpha * C * V^2 * f
 *
 * @param alpha     Switching activity (0.0 - 1.0) 翻转活动(0.0-1.0)
 * @param capacitance_pF  Load capacitance in pF 负载电容(pF)
 * @param voltage_mv    Supply voltage in mV 供电电压(mV)
 * @param frequency_khz Clock frequency in kHz 时钟频率(kHz)
 * @return              Power in micro-watts 功耗(微瓦)
 */
uint32_t lp_calc_dynamic_power(float alpha, float capacitance_pF,
                               uint32_t voltage_mv, uint32_t frequency_khz);

/**
 * Calculate energy for a duration
 * 计算指定时长的能耗
 *
 * @param power_uW    Power in micro-watts 功耗(微瓦)
 * @param duration_ms Duration in milliseconds 时长(毫秒)
 * @return            Energy in micro-joules 能耗(微焦)
 */
uint32_t lp_calc_energy(uint32_t power_uW, uint32_t duration_ms);

/**
 * Print framework state for debugging
 * 打印框架状态用于调试
 *
 * @param ctx     Framework context 框架上下文
 */
void lp_print_state(low_power_context_t *ctx);

#endif /* LOW_POWER_H */
