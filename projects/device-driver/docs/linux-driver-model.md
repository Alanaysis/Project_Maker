/*
 * Linux Driver Model Architecture Reference
 *
 * This document provides an overview of the Linux device driver model
 * and how it relates to the device-framework project.
 *
 * See also: Documentation/driver-api/index.rst in kernel source
 */

#ifndef DOXYGEN
/* This file is for documentation purposes only */
#endif

/*
 * ============================================================================
 * L1: Linux Device Driver Model Layers
 * ============================================================================
 *
 * 1. Device Model Layer
 *    - struct device: represents a physical device
 *    - struct device_driver: represents a driver
 *    - struct bus_type: represents a bus (platform, pci, usb, etc.)
 *    - Kobject/Kref: reference counting and sysfs integration
 *
 * 2. Character Device Layer
 *    - struct cdev: character device structure
 *    - struct file_operations: callback function table
 *    - Major/Minor numbers: device identification
 *    - VFS (Virtual File System): abstracts device access
 *
 * 3. Interrupt Layer
 *    - IRQ numbers: hardware interrupt identification
 *    - irq_handler_t: interrupt service routine type
 *    - Top half (ISR): fast, runs in interrupt context
 *    - Bottom half: deferred work (tasklets, workqueues, softirqs)
 *
 * 4. Platform Bus Layer
 *    - Platform devices: describe hardware resources
 *    - Platform drivers: match with devices via compatible strings
 *    - Device tree: hardware description in DTB format
 *
 * 5. Memory Management Layer
 *    - ioremap: map physical MMIO to virtual address
 *    - DMA mapping: coherent/streaming DMA for devices
 *    - Resource management: request_mem_region/release_mem_region
 *
 * ============================================================================
 * L2: Character Device Driver Lifecycle
 * ============================================================================
 *
 *   [Module Init]                          [Module Exit]
 *        │                                       │
 *        ▼                                       ▼
 *   alloc_chrdev_region          ──────►   unregister_chrdev_region
 *        │                                       │
 *        ▼                                       │
 *   cdev_init                                │
 *        │                                       │
 *        ▼                                       │
 *   cdev_add                                 │
 *        │                                       │
 *        ▼                                       │
 *   class_create                               │
 *        │                                       │
 *        ▼                                       │
 *   device_create                              │
 *        │                                       │
 *        ▼                                       ▼
 *   /dev/xxx created                ──────►   device_destroy
 *                                                 │
 *                                                 ▼
 *                                             class_destroy
 *                                                 │
 *                                                 ▼
 *                                             cdev_del
 *
 * ============================================================================
 * L3: File Operations Flow
 * ============================================================================
 *
 *   User Space                    Kernel Space
 *        │                              │
 *        │  open("/dev/xxx")           │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->open()
 *        │                              │
 *        │  write(buf, n)              │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->write()
 *        │                              │     ├─► copy_from_user()
 *        │                              │     └─► driver processing
 *        │                              │
 *        │  read(buf, n)               │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->read()
 *        │                              │     ├─► driver processing
 *        │                              │     └─► copy_to_user()
 *        │◄─────────────────────────────┤
 *        │  (data)                     │
 *        │                              │
 *        │  ioctl(cmd, arg)            │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->unlocked_ioctl()
 *        │                              │
 *        │  poll()                     │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->poll()
 *        │                              │     └─► poll_wait()
 *        │                              │
 *        │  close()                    │
 *        ├─────────────────────────────►│
 *        │                              ├─► file_operations->release()
 *
 * ============================================================================
 * L4: Interrupt Handling Flow
 * ============================================================================
 *
 *   Hardware              Kernel                    Process Context
 *     │                       │                           │
 *     │  ┌───────────┐       │                           │
 *     ├─►│ Interrupt │───────┤                           │
 *     │  └───────────┘       │                           │
 *     │                       │                           │
 *     │                       ▼                           │
 *     │              ┌───────────────┐                   │
 *     │              │  Top Half     │                   │
 *     │              │  (ISR)        │                   │
 *     │              │  - Fast       │                   │
 *     │              │  - No sleep   │                   │
 *     │              └───────────────┘                   │
 *     │                       │                           │
 *     │                       ▼                           │
 *     │              ┌───────────────┐                   │
 *     │              │ Schedule BH   │                   │
 *     │              └───────────────┘                   │
 *     │                       │                           │
 *     │                       ▼                           ▼
 *     │              ┌───────────────┐           ┌───────────────┐
 *     │              │ Bottom Half   │──────────►│ Process       │
 *     │              │ - Workqueue   │           │ Context       │
 *     │              │ - Tasklet     │           │ - Sleep OK    │
 *     │              └───────────────┘           └───────────────┘
 *
 * ============================================================================
 * L5: Device Tree Integration
 * ============================================================================
 *
 *   Device Tree Source (.dts)     Kernel Driver
 *        │                              │
 *        │  compatible = "vendor,dev"   │
 *        ├─────────────────────────────►│
 *        │                              │
 *        │  reg = <addr size>           │
 *        ├─────────────────────────────►│
 *        │                              ├─► of_address_to_resource()
 *        │                              │     └─► ioremap()
 *        │                              │
 *        │  interrupts = <spec>         │
 *        ├─────────────────────────────►│
 *        │                              ├─► of_irq_get()
 *        │                              │     └─► request_irq()
 *        │                              │
 *        │  custom-property = <val>     │
 *        ├─────────────────────────────►│
 *        │                              ├─► of_get_property()
 *
 * ============================================================================
 * L6: DMA Memory Management
 * ============================================================================
 *
 *   CPU Memory              DMA Buffer              Hardware
 *        │                        │                       │
 *        │                        │                       │
 *        │  dma_alloc_coherent()  │                       │
 *        ├───────────────────────►│                       │
 *        │   virt_addr            │                       │
 *        │   phys_addr (handle)   │                       │
 *        │                        │                       │
 *        │                        │  DMA transfer         │
 *        │                        ├──────────────────────►│
 *        │                        │                       │
 *        │                        │                       │
 *        │  dma_free_coherent()   │                       │
 *        │◄───────────────────────┤                       │
 *        │                        │                       │
 *
 * Coherent DMA guarantees:
 *   - CPU and device see same data (always cache-coherent)
 *   - Higher cost, smaller allocations
 *   - Use dma_alloc_coherent()
 *
 * Streaming DMA (not in this project):
 *   - One-direction transfers (map before, unmap after)
 *   - Lower cost, larger allocations
 *   - Use dma_map_single() / dma_unmap_single()
 *
 * ============================================================================
 * L7: Synchronization Primitives
 * ============================================================================
 *
 *   Mutex (struct mutex):
 *     - Can sleep
 *     - Use in process context (file operations, probe)
 *     - Examples: mutex_lock(), mutex_unlock(), mutex_lock_interruptible()
 *
 *   Spinlock (spinlock_t):
 *     - Cannot sleep (busy-wait)
 *     - Use in interrupt context (ISRs, bottom halves)
 *     - Examples: spin_lock_irqsave(), spin_unlock_irqrestore()
 *
 *   Semaphore:
 *     - Counting mutex
 *     - Can sleep
 *     - Use when multiple resources available
 *
 *   Wait Queue (wait_queue_head_t):
 *     - Block process until condition met
 *     - Examples: wake_up_interruptible(), wait_event_interruptible()
 *
 *   Timer (timer_list):
 *     - Execute function after delay
 *     - Examples: mod_timer(), del_timer_sync()
 *
 * ============================================================================
 * L8: Key Kernel APIs Reference
 * ============================================================================
 *
 *   Category          API                              Purpose
 *   ──────────        ───                              ───────
 *   Device Number     alloc_chrdev_region()            Dynamic major
 *                     register_chrdev_region()          Static major
 *                     unregister_chrdev_region()        Release
 *
 *   Character Dev     cdev_init()                      Initialize cdev
 *                     cdev_add()                       Register cdev
 *                     cdev_del()                       Unregister cdev
 *
 *   Device Class      class_create()                   Create class
 *                     class_destroy()                  Destroy class
 *
 *   Device Node       device_create()                  Create node
 *                     device_destroy()                 Destroy node
 *
 *   Memory            kmalloc()/kfree()                Kernel heap
 *                     kzalloc()                        Zeroed alloc
 *                     ioremap()/iounmap()              MMIO mapping
 *
 *   DMA               dma_alloc_coherent()             Coherent DMA
 *                     dma_free_coherent()              Free coherent DMA
 *
 *   Interrupt         request_irq()                    Request IRQ
 *                     free_irq()                       Free IRQ
 *
 *   Synchronization   mutex_init()/mutex_lock()        Mutex
 *                     spin_lock_init()/spin_lock()     Spinlock
 *                     init_waitqueue_head()            Wait queue
 *                     timer_setup()/mod_timer()        Timer
 *
 *   Device Tree       of_get_property()                Read property
 *                     of_irq_get()                     Get IRQ
 *                     of_address_to_resource()         Get memory
 *                     of_device_is_compatible()        Check compatible
 *
 *   Platform          platform_driver_register()        Register driver
 *                     platform_get_resource()          Get resource
 *                     platform_set_drvdata()           Store driver data
 *
 * ============================================================================
 */
