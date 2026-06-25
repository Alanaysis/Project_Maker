# 需求分析

## 功能需求

### 1. 模板基础模块

#### 1.1 函数模板
- 基本函数模板定义与使用
- 多模板参数
- 默认模板参数
- 函数模板重载
- 模板参数推导
- 完美转发

#### 1.2 类模板
- 基本类模板定义与使用
- 嵌套类模板
- 成员函数模板
- 静态成员
- CRTP 模式
- CTAD (C++17)

#### 1.3 模板特化
- 函数模板全特化
- 类模板全特化
- 类模板偏特化
- 特化匹配规则

#### 1.4 非类型模板参数
- 整数参数
- 枚举参数
- 指针/引用参数
- 布尔参数
- 编译期断言

#### 1.5 模板模板参数
- 基本用法
- 策略选择
- 工厂模式

### 2. 类型萃取模块

#### 2.1 基础类型判断
- is_integral
- is_floating_point
- is_pointer
- is_reference
- is_void
- is_array
- is_const
- is_function

#### 2.2 类型转换
- remove_const
- remove_reference
- remove_cv
- add_pointer
- add_reference
- decay
- conditional
- enable_if

#### 2.3 类型关系
- is_same
- is_base_of
- is_convertible
- is_invocable
- is_assignable
- is_constructible

### 3. SFINAE 模块

#### 3.1 enable_if
- 返回类型约束
- 模板参数约束
- 类模板特化

#### 3.2 void_t 技巧
- 成员类型检测
- 成员函数检测
- 操作符检测
- 容器检测

#### 3.3 表达式检测
- 自定义检测器
- 复合条件检测
- 编译期分发

### 4. 参数包模块

#### 4.1 可变参数模板
- 基本用法
- sizeof... 运算符
- 递归展开

#### 4.2 折叠表达式
- 四种折叠形式
- 逻辑折叠
- 编译期折叠

### 5. 编译期数据结构模块

#### 5.1 TypeList
- 基本操作 (front, pop_front, push_back)
- 访问操作 (get, index_of, contains)
- 变换操作 (transform, filter, reverse)
- 折叠操作 (fold_left)

#### 5.2 integer_sequence
- 基本定义
- 生成序列
- 访问操作
- 变换操作

#### 5.3 编译期字符串
- 基本定义
- 字符串操作
- 编译期哈希

### 6. 实用案例模块

#### 6.1 编译期计算
- factorial
- fibonacci
- GCD
- 素数检测
- 查找表生成

#### 6.2 类型擦除
- Drawable 示例
- Any 容器
- Function 包装器

#### 6.3 访问者模式
- Overloaded 模式
- 表达式树访问
- variant 访问

#### 6.4 依赖注入
- DI 容器
- 自动注入
- 编译期类型安全 DI

## 知识点清单

### 基础知识点

1. 模板参数推导规则
2. 引用折叠规则
3. 完美转发原理
4. SFINAE 原理
5. 模板实例化时机
6. 特化匹配优先级

### 进阶知识点

1. CRTP 模式
2. 表达式模板
3. 策略模式 (Policy-based Design)
4. 类型擦除技术
5. 编译期数据结构
6. 递归模板展开

### 高级知识点

1. 模板模板参数
2. 折叠表达式
3. if constexpr
4. 编译期字符串
5. 概念 (Concepts)
6. 反射 (Reflection)

## 技术要求

### 编译器要求

- **GCC**: 7.0+
- **Clang**: 5.0+
- **MSVC**: 2017+

### C++ 标准

- **最低要求**: C++17
- **推荐**: C++20 (支持 Concepts)

### 依赖项

- 无外部依赖，仅使用标准库
