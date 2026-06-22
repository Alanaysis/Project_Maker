#ifndef RULES_H
#define RULES_H

#include <stdint.h>
#include <stddef.h>
#include "packet.h"
#include "firewall.h"

// 规则结构
typedef struct {
    uint32_t id;            // 规则 ID

    // 匹配条件
    uint32_t src_ip;        // 源 IP (0 表示任意)
    uint32_t src_mask;      // 源 IP 掩码
    uint32_t dst_ip;        // 目的 IP
    uint32_t dst_mask;      // 目的 IP 掩码
    uint16_t src_port;      // 源端口 (0 表示任意)
    uint16_t dst_port;      // 目的端口
    uint8_t  protocol;      // 协议类型 (PROTO_ALL 表示任意)

    // 状态匹配
    uint8_t  match_state;   // 是否匹配状态
    uint8_t  established;   // 匹配已建立的连接

    // 动作
    action_t action;        // 动作类型

    // 日志
    uint8_t  log;           // 是否记录日志

    // 描述
    char description[128];  // 规则描述
} rule_t;

// 规则链
typedef struct {
    rule_t *rules;          // 规则数组
    size_t  count;          // 规则数量
    size_t  capacity;       // 规则容量
    action_t default_action; // 默认动作
} rule_chain_t;

// 初始化规则引擎
rule_chain_t *rules_init(void);

// 加载规则文件
int rules_load(rule_chain_t *chain, const char *filename);

// 添加规则
int rules_add(rule_chain_t *chain, const rule_t *rule);

// 删除规则
int rules_delete(rule_chain_t *chain, uint32_t rule_id);

// 匹配规则
rule_t *rules_match(rule_chain_t *chain, const packet_t *pkt);

// 获取规则数量
size_t rules_count(const rule_chain_t *chain);

// 打印规则
void rules_print(const rule_chain_t *chain);

// 清理资源
void rules_cleanup(rule_chain_t *chain);

// 辅助函数：解析 IP 地址和掩码
int rules_parse_cidr(const char *cidr, uint32_t *ip, uint32_t *mask);

// 辅助函数：解析端口范围
int rules_parse_port(const char *port_str, uint16_t *port);

// 辅助函数：解析协议
int rules_parse_protocol(const char *proto_str, uint8_t *protocol);

#endif /* RULES_H */
