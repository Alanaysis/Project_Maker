/**
 * @file market_maker.h
 * @brief 做市策略
 *
 * 实现经典的做市策略，通过在买卖双边提供流动性来赚取价差。
 */

#pragma once

#include "strategy.h"
#include "order/order_manager.h"
#include "market_data/order_book.h"
#include "core/logger.h"

#include <cmath>
#include <random>

namespace hft {

/**
 * @struct MarketMakerConfig
 * @brief 做市策略配置
 */
struct MarketMakerConfig {
    double base_spread = 0.001;       ///< 基础价差（百分比）
    double skew_factor = 0.0001;      ///< 库存偏移系数
    double volatility_factor = 0.5;   ///< 波动率调整系数
    int64_t quote_size = 100;         ///< 报价数量
    int64_t max_position = 1000;      ///< 最大持仓
    double max_loss = 10000.0;        ///< 最大亏损
    int quote_interval_ms = 100;      ///< 报价间隔（毫秒）
    bool use_inventory_skew = true;   ///< 是否使用库存偏移
};

/**
 * @class MarketMaker
 * @brief 做市策略
 *
 * 策略逻辑：
 * 1. 计算中间价
 * 2. 根据库存调整报价（库存多则降低卖价，库存少则提高买价）
 * 3. 根据波动率调整价差
 * 4. 提交买卖报价
 * 5. 监控成交，调整库存
 */
class MarketMaker : public Strategy {
public:
    /**
     * @brief 构造函数
     * @param config 策略配置
     * @param order_manager 订单管理器
     */
    MarketMaker(const MarketMakerConfig& config, OrderManager& order_manager)
        : Strategy("MarketMaker"), config_(config), order_manager_(order_manager),
          inventory_(0), realized_pnl_(0), unrealized_pnl_(0),
          total_trades_(0), winning_trades_(0) {}

    /**
     * @brief 析构函数
     */
    ~MarketMaker() override = default;

    // ==================== 生命周期 ====================

    void on_init() override {
        LOG_INFO("MarketMaker initialized");
        set_state(StrategyState::INITED);
    }

    void on_start() override {
        LOG_INFO("MarketMaker started");
        set_state(StrategyState::RUNNING);
    }

    void on_stop() override {
        LOG_INFO("MarketMaker stopped");
        cancel_all_quotes();
        set_state(StrategyState::STOPPED);
    }

    // ==================== 数据回调 ====================

    void on_tick(const Tick& tick) override {
        if (!is_running()) return;

        // 更新最新价格
        last_price_ = tick.last_price;
        mid_price_ = tick.mid_price();

        // 更新波动率
        update_volatility(tick);

        // 更新未实现盈亏
        update_unrealized_pnl();

        // 检查风险限制
        if (!check_risk_limits()) {
            LOG_WARN("Risk limit exceeded, cancelling quotes");
            cancel_all_quotes();
            return;
        }

        // 生成报价
        generate_quotes(tick.symbol);
    }

    void on_order(const Order& order) override {
        // 订单状态更新
        if (order.is_filled()) {
            LOG_INFO("Order filled: " + order.to_string());
        }
    }

    void on_trade(const Trade& trade) override {
        // 更新库存
        update_inventory(trade);

        // 更新盈亏
        update_pnl(trade);

        total_trades_++;

        LOG_INFO("Trade: " + trade.to_string() +
                 " Inventory: " + std::to_string(inventory_) +
                 " PnL: " + std::to_string(realized_pnl_));
    }

    // ==================== 配置 ====================

    void set_params(const StrategyParams& params) override {
        if (params.has("base_spread")) {
            config_.base_spread = params.get_double("base_spread");
        }
        if (params.has("skew_factor")) {
            config_.skew_factor = params.get_double("skew_factor");
        }
        if (params.has("quote_size")) {
            config_.quote_size = params.get_int("quote_size");
        }
        if (params.has("max_position")) {
            config_.max_position = params.get_int("max_position");
        }
    }

    StrategyParams get_params() const override {
        StrategyParams params;
        params.set("base_spread", config_.base_spread);
        params.set("skew_factor", config_.skew_factor);
        params.set("quote_size", config_.quote_size);
        params.set("max_position", config_.max_position);
        return params;
    }

    // ==================== 查询 ====================

    /**
     * @brief 获取当前库存
     * @return 库存数量
     */
    int64_t inventory() const { return inventory_; }

    /**
     * @brief 获取已实现盈亏
     * @return 已实现盈亏
     */
    double realized_pnl() const { return realized_pnl_; }

    /**
     * @brief 获取未实现盈亏
     * @return 未实现盈亏
     */
    double unrealized_pnl() const { return unrealized_pnl_; }

    /**
     * @brief 获取总盈亏
     * @return 总盈亏
     */
    double total_pnl() const { return realized_pnl_ + unrealized_pnl_; }

    /**
     * @brief 获取胜率
     * @return 胜率
     */
    double win_rate() const {
        if (total_trades_ == 0) return 0.0;
        return static_cast<double>(winning_trades_) / total_trades_;
    }

private:
    /**
     * @brief 计算库存偏移
     * @return 偏移量
     */
    double calculate_inventory_skew() const {
        if (!config_.use_inventory_skew) return 0.0;

        // 库存多则降低卖价（负偏移），库存少则提高买价（正偏移）
        return -inventory_ * config_.skew_factor;
    }

    /**
     * @brief 计算波动率调整
     * @return 调整量
     */
    double calculate_volatility_adjustment() const {
        // 波动率大则扩大价差
        return volatility_ * config_.volatility_factor;
    }

    /**
     * @brief 更新波动率
     * @param tick Tick 数据
     */
    void update_volatility(const Tick& tick) {
        // 使用简单的价格变化标准差
        double price_change = tick.last_price - last_price_;
        price_changes_.push_back(price_change);

        // 保留最近 100 个价格变化
        if (price_changes_.size() > 100) {
            price_changes_.erase(price_changes_.begin());
        }

        // 计算标准差
        if (price_changes_.size() >= 10) {
            double mean = 0;
            for (double change : price_changes_) {
                mean += change;
            }
            mean /= price_changes_.size();

            double variance = 0;
            for (double change : price_changes_) {
                variance += (change - mean) * (change - mean);
            }
            variance /= price_changes_.size();

            volatility_ = std::sqrt(variance);
        }
    }

    /**
     * @brief 更新库存
     * @param trade 成交记录
     */
    void update_inventory(const Trade& trade) {
        if (trade.side == Side::BUY) {
            inventory_ += trade.quantity;
        } else {
            inventory_ -= trade.quantity;
        }
    }

    /**
     * @brief 更新盈亏
     * @param trade 成交记录
     */
    void update_pnl(const Trade& trade) {
        // 做市策略的盈亏计算
        // 买入后卖出，或卖出后买入
        if (inventory_ == 0) {
            // 库存清零，计算已实现盈亏
            // 简化计算
        }
    }

    /**
     * @brief 更新未实现盈亏
     */
    void update_unrealized_pnl() {
        if (inventory_ != 0 && last_price_ > 0) {
            // 简化的未实现盈亏计算
            unrealized_pnl_ = inventory_ * (last_price_ - avg_cost_);
        }
    }

    /**
     * @brief 检查风险限制
     * @return 通过返回 true
     */
    bool check_risk_limits() const {
        // 检查持仓限制
        if (std::abs(inventory_) >= config_.max_position) {
            return false;
        }

        // 检查亏损限制
        if (total_pnl() < -config_.max_loss) {
            return false;
        }

        return true;
    }

    /**
     * @brief 生成报价
     * @param symbol 品种代码
     */
    void generate_quotes(const std::string& symbol) {
        if (mid_price_ <= 0) return;

        // 计算价差
        double spread = config_.base_spread;
        spread += calculate_volatility_adjustment();

        // 计算库存偏移
        double skew = calculate_inventory_skew();

        // 计算买卖价格
        double bid_price = mid_price_ * (1.0 - spread / 2.0 + skew);
        double ask_price = mid_price_ * (1.0 + spread / 2.0 + skew);

        // 确保买价低于卖价
        if (bid_price >= ask_price) {
            bid_price = mid_price_ * (1.0 - spread / 2.0);
            ask_price = mid_price_ * (1.0 + spread / 2.0);
        }

        // 取消旧报价
        cancel_all_quotes();

        // 提交新报价
        auto buy_order = order_manager_.create_order(
            symbol, Side::BUY, OrderType::LIMIT,
            bid_price, config_.quote_size
        );
        order_manager_.send_order(buy_order.order_id);

        auto sell_order = order_manager_.create_order(
            symbol, Side::SELL, OrderType::LIMIT,
            ask_price, config_.quote_size
        );
        order_manager_.send_order(sell_order.order_id);

        // 记录报价
        active_bid_ = buy_order.order_id;
        active_ask_ = sell_order.order_id;
    }

    /**
     * @brief 取消所有报价
     */
    void cancel_all_quotes() {
        if (!active_bid_.empty()) {
            order_manager_.cancel_order(active_bid_);
            active_bid_.clear();
        }
        if (!active_ask_.empty()) {
            order_manager_.cancel_order(active_ask_);
            active_ask_.clear();
        }
    }

    MarketMakerConfig config_;           ///< 策略配置
    OrderManager& order_manager_;        ///< 订单管理器

    int64_t inventory_ = 0;             ///< 当前库存
    double realized_pnl_ = 0.0;         ///< 已实现盈亏
    double unrealized_pnl_ = 0.0;       ///< 未实现盈亏
    double avg_cost_ = 0.0;             ///< 平均成本

    double last_price_ = 0.0;           ///< 最新价格
    double mid_price_ = 0.0;            ///< 中间价
    double volatility_ = 0.0;           ///< 波动率
    std::vector<double> price_changes_;  ///< 价格变化历史

    std::string active_bid_;            ///< 当前买盘订单
    std::string active_ask_;            ///< 当前卖盘订单

    int64_t total_trades_ = 0;          ///< 总成交次数
    int64_t winning_trades_ = 0;        ///< 盈利次数
};

} // namespace hft
