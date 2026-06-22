/**
 * 规则引擎模块
 *
 * 本模块负责：
 * 1. 加载和解析规则文件
 * 2. 管理规则链
 * 3. 匹配数据包和规则
 *
 * ⭐ 重点：理解规则匹配的顺序性
 *    规则按顺序匹配，第一个匹配的规则生效
 *    因此规则的顺序非常重要
 *
 * 💡 思考：如何优化规则匹配性能？
 *    - 使用哈希表加速端口查找
 *    - 使用 Trie 树加速 IP 匹配
 *    - 使用规则分组减少匹配次数
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <ctype.h>

#include "rules.h"

// 规则文件最大行长度
#define MAX_LINE_LEN 1024

// 默认规则容量
#define DEFAULT_RULES_CAPACITY 64

/**
 * 初始化规则引擎
 *
 * @return 规则链指针，失败返回 NULL
 */
rule_chain_t *rules_init(void) {
    rule_chain_t *chain;

    chain = (rule_chain_t *)calloc(1, sizeof(rule_chain_t));
    if (!chain) {
        return NULL;
    }

    // 分配规则数组
    chain->rules = (rule_t *)calloc(DEFAULT_RULES_CAPACITY, sizeof(rule_t));
    if (!chain->rules) {
        free(chain);
        return NULL;
    }

    chain->count = 0;
    chain->capacity = DEFAULT_RULES_CAPACITY;
    chain->default_action = ACTION_DROP;  // 默认拒绝

    return chain;
}

/**
 * 扩展规则数组
 *
 * @param chain 规则链
 * @return 0 成功，-1 失败
 */
static int rules_expand(rule_chain_t *chain) {
    size_t new_capacity = chain->capacity * 2;
    rule_t *new_rules;

    new_rules = (rule_t *)realloc(chain->rules, new_capacity * sizeof(rule_t));
    if (!new_rules) {
        return -1;
    }

    // 清空新分配的内存
    memset(new_rules + chain->capacity, 0,
           (new_capacity - chain->capacity) * sizeof(rule_t));

    chain->rules = new_rules;
    chain->capacity = new_capacity;

    return 0;
}

/**
 * 解析 CIDR 表示法
 *
 * 示例：192.168.1.0/24
 *
 * @param cidr CIDR 字符串
 * @param ip 输出 IP 地址（网络字节序）
 * @param mask 输出掩码（网络字节序）
 * @return 0 成功，-1 失败
 */
int rules_parse_cidr(const char *cidr, uint32_t *ip, uint32_t *mask) {
    char *slash;
    char ip_str[64];
    struct in_addr addr;

    // 复制字符串（因为我们需要修改它）
    strncpy(ip_str, cidr, sizeof(ip_str) - 1);
    ip_str[sizeof(ip_str) - 1] = '\0';

    // 查找斜杠
    slash = strchr(ip_str, '/');
    if (slash) {
        *slash = '\0';
        int prefix_len = atoi(slash + 1);

        if (prefix_len < 0 || prefix_len > 32) {
            return -1;
        }

        // 计算掩码
        if (prefix_len == 0) {
            *mask = 0;
        } else {
            *mask = htonl(~((1 << (32 - prefix_len)) - 1));
        }
    } else {
        // 没有斜杠，使用精确匹配
        *mask = htonl(0xFFFFFFFF);
    }

    // 解析 IP 地址
    if (inet_pton(AF_INET, ip_str, &addr) != 1) {
        return -1;
    }
    *ip = addr.s_addr;

    return 0;
}

/**
 * 解析端口
 *
 * @param port_str 端口字符串
 * @param port 输出端口（主机字节序）
 * @return 0 成功，-1 失败
 */
int rules_parse_port(const char *port_str, uint16_t *port) {
    // 检查是否是数字
    for (const char *p = port_str; *p; p++) {
        if (!isdigit(*p)) {
            return -1;
        }
    }

    int val = atoi(port_str);
    if (val < 0 || val > 65535) {
        return -1;
    }

    *port = (uint16_t)val;
    return 0;
}

/**
 * 解析协议
 *
 * @param proto_str 协议字符串
 * @param protocol 输出协议号
 * @return 0 成功，-1 失败
 */
int rules_parse_protocol(const char *proto_str, uint8_t *protocol) {
    if (strcasecmp(proto_str, "tcp") == 0) {
        *protocol = PROTO_TCP;
    } else if (strcasecmp(proto_str, "udp") == 0) {
        *protocol = PROTO_UDP;
    } else if (strcasecmp(proto_str, "icmp") == 0) {
        *protocol = PROTO_ICMP;
    } else if (strcasecmp(proto_str, "all") == 0 || strcasecmp(proto_str, "any") == 0) {
        *protocol = PROTO_ALL;
    } else {
        return -1;
    }
    return 0;
}

/**
 * 解析动作
 *
 * @param action_str 动作字符串
 * @param action 输出动作
 * @return 0 成功，-1 失败
 */
static int parse_action(const char *action_str, action_t *action) {
    if (strcasecmp(action_str, "accept") == 0 || strcasecmp(action_str, "allow") == 0) {
        *action = ACTION_ACCEPT;
    } else if (strcasecmp(action_str, "drop") == 0 || strcasecmp(action_str, "deny") == 0) {
        *action = ACTION_DROP;
    } else if (strcasecmp(action_str, "reject") == 0) {
        *action = ACTION_REJECT;
    } else if (strcasecmp(action_str, "log") == 0) {
        *action = ACTION_LOG;
    } else {
        return -1;
    }
    return 0;
}

/**
 * 解析单行规则
 *
 * 规则格式：
 * ACTION PROTOCOL [条件...]
 *
 * 示例：
 * ACCEPT tcp dst_port 80
 * DROP tcp src_ip 192.168.1.100
 * ACCEPT tcp ESTABLISHED
 *
 * @param line 规则行
 * @param rule 输出规则
 * @return 0 成功，-1 失败
 */
static int parse_rule_line(const char *line, rule_t *rule) {
    char *tokens[16];
    int token_count = 0;
    char *line_copy;
    char *token;

    // 跳过空行和注释
    if (line[0] == '\0' || line[0] == '#') {
        return -1;
    }

    // 复制行（因为 strtok 会修改字符串）
    line_copy = strdup(line);
    if (!line_copy) {
        return -1;
    }

    // 分割 tokens
    token = strtok(line_copy, " \t\n");
    while (token && token_count < 16) {
        tokens[token_count++] = token;
        token = strtok(NULL, " \t\n");
    }

    // 至少需要动作和协议
    if (token_count < 2) {
        free(line_copy);
        return -1;
    }

    // 清空规则
    memset(rule, 0, sizeof(rule_t));

    // 解析动作
    if (parse_action(tokens[0], &rule->action) != 0) {
        free(line_copy);
        return -1;
    }

    // 解析协议
    if (rules_parse_protocol(tokens[1], &rule->protocol) != 0) {
        free(line_copy);
        return -1;
    }

    // 解析其他条件
    for (int i = 2; i < token_count; i++) {
        if (strcasecmp(tokens[i], "src_ip") == 0 || strcasecmp(tokens[i], "src") == 0) {
            // 源 IP
            if (i + 1 < token_count) {
                if (rules_parse_cidr(tokens[i + 1], &rule->src_ip, &rule->src_mask) != 0) {
                    free(line_copy);
                    return -1;
                }
                i++;
            }
        } else if (strcasecmp(tokens[i], "dst_ip") == 0 || strcasecmp(tokens[i], "dst") == 0) {
            // 目的 IP
            if (i + 1 < token_count) {
                if (rules_parse_cidr(tokens[i + 1], &rule->dst_ip, &rule->dst_mask) != 0) {
                    free(line_copy);
                    return -1;
                }
                i++;
            }
        } else if (strcasecmp(tokens[i], "src_port") == 0) {
            // 源端口
            if (i + 1 < token_count) {
                if (rules_parse_port(tokens[i + 1], &rule->src_port) != 0) {
                    free(line_copy);
                    return -1;
                }
                i++;
            }
        } else if (strcasecmp(tokens[i], "dst_port") == 0 || strcasecmp(tokens[i], "port") == 0) {
            // 目的端口
            if (i + 1 < token_count) {
                if (rules_parse_port(tokens[i + 1], &rule->dst_port) != 0) {
                    free(line_copy);
                    return -1;
                }
                i++;
            }
        } else if (strcasecmp(tokens[i], "ESTABLISHED") == 0) {
            // 匹配已建立的连接
            rule->match_state = 1;
            rule->established = 1;
        } else if (strcasecmp(tokens[i], "log") == 0) {
            // 记录日志
            rule->log = 1;
        }
    }

    free(line_copy);
    return 0;
}

/**
 * 加载规则文件
 *
 * @param chain 规则链
 * @param filename 规则文件名
 * @return 0 成功，-1 失败
 */
int rules_load(rule_chain_t *chain, const char *filename) {
    FILE *fp;
    char line[MAX_LINE_LEN];
    int line_num = 0;
    rule_t rule;

    if (!chain || !filename) {
        return -1;
    }

    fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open rule file: %s\n", filename);
        return -1;
    }

    while (fgets(line, sizeof(line), fp)) {
        line_num++;

        // 去除换行符
        line[strcspn(line, "\n")] = '\0';

        // 跳过空行和注释
        if (line[0] == '\0' || line[0] == '#') {
            continue;
        }

        // 解析规则
        if (parse_rule_line(line, &rule) == 0) {
            rule.id = chain->count + 1;

            // 检查是否需要记录日志
            if (rule.log == 0) {
                // 默认记录所有规则的日志
                rule.log = 1;
            }

            // 添加规则
            if (rules_add(chain, &rule) != 0) {
                fprintf(stderr, "Error: Failed to add rule at line %d\n", line_num);
                fclose(fp);
                return -1;
            }
        } else {
            fprintf(stderr, "Warning: Invalid rule at line %d: %s\n", line_num, line);
        }
    }

    fclose(fp);

    printf("[INFO] Loaded %zu rules from %s\n", chain->count, filename);
    return 0;
}

/**
 * 添加规则
 *
 * @param chain 规则链
 * @param rule 规则
 * @return 0 成功，-1 失败
 */
int rules_add(rule_chain_t *chain, const rule_t *rule) {
    if (!chain || !rule) {
        return -1;
    }

    // 检查是否需要扩展
    if (chain->count >= chain->capacity) {
        if (rules_expand(chain) != 0) {
            return -1;
        }
    }

    // 复制规则
    chain->rules[chain->count] = *rule;
    chain->count++;

    return 0;
}

/**
 * 删除规则
 *
 * @param chain 规则链
 * @param rule_id 规则 ID
 * @return 0 成功，-1 失败
 */
int rules_delete(rule_chain_t *chain, uint32_t rule_id) {
    if (!chain) {
        return -1;
    }

    for (size_t i = 0; i < chain->count; i++) {
        if (chain->rules[i].id == rule_id) {
            // 移动后续规则
            for (size_t j = i; j < chain->count - 1; j++) {
                chain->rules[j] = chain->rules[j + 1];
            }
            chain->count--;
            return 0;
        }
    }

    return -1;
}

/**
 * 匹配规则
 *
 * ⭐ 重点：理解规则匹配的顺序性
 *    规则按顺序匹配，第一个匹配的规则生效
 *    因此，更具体的规则应该放在前面
 *
 * @param chain 规则链
 * @param pkt 数据包
 * @return 匹配的规则，未匹配返回 NULL
 */
rule_t *rules_match(rule_chain_t *chain, const packet_t *pkt) {
    if (!chain || !pkt) {
        return NULL;
    }

    for (size_t i = 0; i < chain->count; i++) {
        rule_t *rule = &chain->rules[i];

        // 检查协议
        if (rule->protocol != PROTO_ALL && rule->protocol != pkt->protocol) {
            continue;
        }

        // 检查源 IP
        if (rule->src_ip != 0) {
            if ((pkt->src_ip & rule->src_mask) != (rule->src_ip & rule->src_mask)) {
                continue;
            }
        }

        // 检查目的 IP
        if (rule->dst_ip != 0) {
            if ((pkt->dst_ip & rule->dst_mask) != (rule->dst_ip & rule->dst_mask)) {
                continue;
            }
        }

        // 检查源端口
        if (rule->src_port != 0 && rule->src_port != pkt->src_port) {
            continue;
        }

        // 检查目的端口
        if (rule->dst_port != 0 && rule->dst_port != pkt->dst_port) {
            continue;
        }

        // 检查状态
        if (rule->match_state) {
            // 这里需要结合状态管理模块来判断
            // 暂时跳过
        }

        // 匹配成功
        return rule;
    }

    // 未匹配任何规则，返回 NULL（使用默认动作）
    return NULL;
}

/**
 * 获取规则数量
 *
 * @param chain 规则链
 * @return 规则数量
 */
size_t rules_count(const rule_chain_t *chain) {
    return chain ? chain->count : 0;
}

/**
 * 打印规则
 *
 * @param chain 规则链
 */
void rules_print(const rule_chain_t *chain) {
    if (!chain) return;

    printf("\n=== Firewall Rules ===\n");
    printf("Total rules: %zu\n", chain->count);
    printf("Default action: %s\n",
           chain->default_action == ACTION_ACCEPT ? "ACCEPT" :
           chain->default_action == ACTION_DROP ? "DROP" : "REJECT");
    printf("\n");

    for (size_t i = 0; i < chain->count; i++) {
        const rule_t *rule = &chain->rules[i];
        char src_ip[INET_ADDRSTRLEN];
        char dst_ip[INET_ADDRSTRLEN];

        // 格式化 IP 地址
        if (rule->src_ip == 0) {
            strcpy(src_ip, "any");
        } else {
            struct in_addr addr;
            addr.s_addr = rule->src_ip;
            strcpy(src_ip, inet_ntoa(addr));
        }

        if (rule->dst_ip == 0) {
            strcpy(dst_ip, "any");
        } else {
            struct in_addr addr;
            addr.s_addr = rule->dst_ip;
            strcpy(dst_ip, inet_ntoa(addr));
        }

        printf("Rule %u: ", rule->id);
        printf("%s ", rule->action == ACTION_ACCEPT ? "ACCEPT" :
               rule->action == ACTION_DROP ? "DROP" :
               rule->action == ACTION_REJECT ? "REJECT" : "LOG");
        printf("%s ", packet_proto_name(rule->protocol));
        printf("%s:%d → %s:%d",
               src_ip, rule->src_port,
               dst_ip, rule->dst_port);

        if (rule->match_state && rule->established) {
            printf(" ESTABLISHED");
        }

        printf("\n");
    }

    printf("========================\n\n");
}

/**
 * 清理资源
 *
 * @param chain 规则链
 */
void rules_cleanup(rule_chain_t *chain) {
    if (chain) {
        free(chain->rules);
        free(chain);
    }
}
