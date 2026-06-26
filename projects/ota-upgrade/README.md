/**
 * OTA Firmware Upgrade System
 * ===========================
 *
 * 一个用于学习 OTA（空中下载）固件升级系统的 C 语言项目。
 *
 * An educational C project implementing an OTA (Over-The-Air)
 * Firmware Upgrade System for learning embedded firmware update concepts.
 *
 * ============================================================
 *
 * ## English
 *
 * ### Overview
 *
 * This project implements a complete OTA firmware upgrade system from
 * scratch, covering all key concepts used in real embedded devices:
 *
 * - **Firmware Image Format**: Header with magic number, version, CRC32,
 *   SHA256 hash, and RSA signature
 * - **Chunked Download**: Download firmware in small chunks for memory
 *   efficiency and progress tracking
 * - **Signature Verification**: RSA/ECDSA signature verification to ensure
 *   firmware authenticity
 * - **Checksum Validation**: CRC32 for fast integrity check, SHA256 for
 *   cryptographic verification
 * - **Dual-bank A/B Update**: Two firmware partitions for safe updates
 *   without bricking
 * - **Rollback Mechanism**: Automatic recovery from failed updates
 * - **Delta Update**: Binary diff/patch to reduce download size
 * - **Bootloader Simulation**: Simulated bootloader with secure boot
 *
 * ### Learning Objectives
 *
 * 1. Understand OTA update principles and architecture
 * 2. Master firmware image format and verification
 * 3. Learn dual-bank A/B update mechanism
 * 4. Implement delta update for bandwidth efficiency
 * 5. Understand secure boot and signature verification
 *
 * ### Architecture
 *
 * ```
 *  +-----------+     +-----------+     +-----------+
 *  |  OTA Server|    |  Network  |    |  Device   |
 *  | (Firmware |---->| (HTTP/    |---->|  Bootloader|
 *  |  Host)     |    |  MQTT)    |     |           |
 *  +-----------+     +-----------+     +-----+-----+
 *                                              |
 *                    +-----------+     +-------v------+
 *                    |  Delta    |     |  Dual-bank   |
 *                    |  Generator|     |  A/B Update  |
 *                    +-----------+     +-------+------+
 *                                              |
 *                    +-----------+     +-------v------+
 *                    | Signature |     |  Verification|
 *                    |  Verify   |     |  (CRC32 +    |
 *                    +-----------+     |  SHA256 +    |
 *                                      |  RSA)         |
 *                                      +-------+------+
 *                                              |
 *                    +-----------+     +-------v------+
 *                    |  Rollback |<----|  Flash Write |
 *                    +-----------+     +--------------+
 * ```
 *
 * ### How to Build and Run
 *
 * ```bash
 * # Build all targets
 * make
 *
 * # Build individual targets
 * make basic-ota          # Basic OTA update flow demo
 * make firmware-verify    # Firmware verification demo
 * make delta-update       # Delta update demo
 * make rollback           # Rollback mechanism demo
 * make test               # Run all unit tests
 *
 * # Run examples
 * ./build/basic_ota
 * ./build/firmware_verify
 * ./build/delta_update
 * ./build/rollback
 *
 * # Run tests
 * ./build/test_crc32
 * ./build/test_sha256
 * ./build/test_firmware_image
 * ./build/test_dualbank
 * ./build/test_delta
 * ./build/test_signature
 *
 * # Clean
 * make clean
 * ```
 *
 * ### Project Structure
 *
 * ```
 * ota-upgrade/
 * ├── include/
 * │   └── ota_firmware.h      # Core header with all type definitions
 * ├── src/
 * │   ├── ota_crc32.c         # CRC32 checksum implementation
 * │   ├── ota_sha256.c        # SHA256 hash implementation
 * │   ├── ota_signature.c     # Simulated RSA/ECDSA signature
 * │   ├── ota_download.c      # Chunked download module
 * │   ├── ota_image.c         # Firmware image builder/serializer
 * │   ├── ota_dualbank.c      # Dual-bank A/B update mechanism
 * │   ├── ota_delta.c         # Delta update (binary diff/patch)
 * │   ├── ota_bootloader.c    # Bootloader simulation
 * │   └── ota_state_machine.c # OTA update state machine
 * ├── examples/
 * │   ├── example_basic_ota.c       # Complete OTA update flow
 * │   ├── example_firmware_verify.c # Verification methods demo
 * │   ├── example_delta_update.c    # Delta update demo
 * │   └── example_rollback.c        # Rollback mechanism demo
 * ├── tests/
 * │   ├── test_crc32.c              # CRC32 unit tests
 * │   ├── test_sha256.c             # SHA256 unit tests
 * │   ├── test_firmware_image.c     # Firmware image tests
 * │   ├── test_dualbank.c           # Dual-bank update tests
 * │   ├── test_delta.c              # Delta update tests
 * │   └── test_signature.c          # Signature verification tests
 * ├── Makefile
 * └── README.md
 * ```
 *
 * ---
 *
 * ## Chinese / 中文
 *
 * ### 项目概述
 *
 * 本项目从零实现了一个完整的 OTA 固件升级系统，涵盖嵌入式设备中使用的
 * 所有关键概念：
 *
 * - **固件镜像格式**: 包含魔数、版本号、CRC32、SHA256 哈希和 RSA 签名的头部
 * - **分块下载**: 以小分块下载固件，节省内存并支持进度跟踪
 * - **签名验证**: RSA/ECDSA 签名验证确保固件来源可信
 * - **校验和验证**: CRC32 用于快速完整性检查，SHA256 用于密码学验证
 * - **双区 A/B 更新**: 两个固件分区实现安全更新，不会变砖
 * - **回滚机制**: 从更新失败中自动恢复
 * - **差分更新**: 二进制差分/补丁，减少下载量
 * - **引导加载器模拟**: 带安全启动的模拟引导加载器
 *
 * ### 学习目标
 *
 * 1. 理解 OTA 升级原理和架构
 * 2. 掌握固件镜像格式和验证方法
 * 3. 学习双区 A/B 更新机制
 * 4. 实现差分更新以提高带宽效率
 * 5. 理解安全启动和签名验证
 *
 * ### OTA 更新架构
 *
 * ```
 *  +-----------+     +-----------+     +-----------+
 *  |  OTA 服务器|    |  网络     |    |  设备      |
 *  | (固件托管) |---->| (HTTP/    |---->|  引导加载器|
 *  +-----------+     |  MQTT)    |     +-----+-----+
 *                    +-----------+           |
 *                    +-----------+     +-----v------+
 *                    | 差分生成器 |     | 双区 A/B   |
 *                    +-----------+     | A/B 更新    |
 *                                      +-------+------+
 *                                              |
 *                    +-----------+     +-------v------+
 *                    |  回滚     |<----|  闪存写入     |
 *                    +-----------+     +--------------+
 * ```
 *
 * ### 如何构建和运行
 *
 * ```bash
 * # 构建所有目标
 * make
 *
 * # 构建单个目标
 * make basic-ota          # 基本 OTA 更新流程演示
 * make firmware-verify    # 固件验证演示
 * make delta-update       # 差分更新演示
 * make rollback           # 回滚机制演示
 * make test               # 运行所有单元测试
 *
 * # 运行示例
 * ./build/basic_ota
 * ./build/firmware_verify
 * ./build/delta_update
 * ./build/rollback
 *
 * # 运行测试
 * ./build/test_crc32
 * ./build/test_sha256
 * ./build/test_firmware_image
 * ./build/test_dualbank
 * ./build/test_delta
 * ./build/test_signature
 *
 * # 清理
 * make clean
 * ```
 *
 * ### 项目结构
 *
 * 与上方英文部分的结构相同。
 *
 * ---
 *
 * ## Key OTA Concepts 关键 OTA 概念
 *
 * ### Firmware Image Format 固件镜像格式
 * ```
 * [Header (64 bytes)][Payload (variable)][Signature (256 bytes)]
 *   Magic: 0x4F544131 ("OTA1")
 *   Version: (major<<16)|(minor<<8)|patch
 *   CRC32: Fast integrity check
 *   SHA256: Cryptographic verification
 * ```
 *
 * ### Dual-bank A/B Update 双区 A/B 更新
 * ```
 * Normal:  [Bank A: Running][Bank B: Empty]
 * Update:  [Bank A: Running][Bank B: Writing]
 * Verify:  [Bank A: Running][Bank B: Verified]
 * Switch:  [Bank A: Old][Bank B: Running] <-- Reboot
 * Rollback:[Bank A: Running][Bank B: Old]  <-- Failed
 * ```
 *
 * ### Delta Update 差分更新
 * ```
 * Full download:  1,048,576 bytes (1 MB)
 * Delta patch:        128 bytes
 * Savings:           99.99%
 * ```
 *
 * ### Security Chain 安全链
 * ```
 * Vendor signs --> Device verifies --> Trust established
 * (Private Key)   (Public Key)       (Firmware is authentic)
 * ```
 *
 * ---
 *
 * ## License 许可证
 * MIT License
 */
