#ifndef TYPES_H
#define TYPES_H

// 基本类型定义
typedef unsigned char      uint8_t;
typedef unsigned short     uint16_t;
typedef unsigned int       uint32_t;
typedef unsigned long long uint64_t;

typedef signed char        int8_t;
typedef signed short       int16_t;
typedef signed int         int32_t;
typedef signed long long   int64_t;

typedef uint32_t size_t;
typedef int32_t  ssize_t;

typedef uint32_t pid_t;

// NULL 定义
#define NULL ((void *)0)

// 布尔类型
typedef enum {
    false = 0,
    true = 1
} bool;

// 常用宏
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define MAX(a, b) ((a) > (b) ? (a) : (b))

// 对齐宏
#define ALIGN_UP(x, align)   (((x) + (align) - 1) & ~((align) - 1))
#define ALIGN_DOWN(x, align) ((x) & ~((align) - 1))

// 位操作宏
#define SET_BIT(x, bit)   ((x) |= (1 << (bit)))
#define CLEAR_BIT(x, bit) ((x) &= ~(1 << (bit)))
#define TOGGLE_BIT(x, bit) ((x) ^= (1 << (bit)))
#define IS_SET(x, bit)    ((x) & (1 << (bit)))

// 错误码定义
#define SUCCESS         0
#define ERROR_NOMEM    -1
#define ERROR_INVAL    -2
#define ERROR_NOENT    -3
#define ERROR_EXIST    -4
#define ERROR_PERM     -5
#define ERROR_IO       -6
#define ERROR_NOSYS    -7

#endif /* TYPES_H */
