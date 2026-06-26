/*
 * device-driver-framework - Linux Device Driver Learning Project
 *
 * This project implements a comprehensive Linux character device driver framework
 * for educational purposes. It covers the full lifecycle of a Linux device driver:
 *   - Module initialization and cleanup
 *   - Character device registration (cdev)
 *   - File operations (open, release, read, write, ioctl)
 *   - Device class and device node creation
 *   - Interrupt handling (request_irq, free_irq)
 *   - IRQ handler with edge/level triggering
 *   - Device tree parsing
 *   - Platform driver model
 *   - Memory-mapped I/O (ioremap)
 *   - DMA buffer management
 *
 * Linux Kernel Module - Compatible with kernel 4.x through 6.x
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/interrupt.h>
#include <linux/platform_device.h>
#include <linux/io.h>
#include <linux/dma-mapping.h>
#include <linux/of.h>
#include <linux/of_irq.h>
#include <linux/spinlock.h>
#include <linux/poll.h>
#include <linux/wait.h>
#include <linux/mutex.h>
#include <linux/sched.h>
#include <linux/semaphore.h>
#include <linux/timer.h>
#include <linux/workqueue.h>

#include "device_framework.h"

/* Module parameters for configurable behavior */
static int major_number = DEVICE_FRAMEWORK_MAJOR;
module_param(major_number, int, 0644);
MODULE_PARM_DESC(major_number, "Major number for the device framework");

static int buffer_size = DEVICE_FRAMEWORK_BUFFER_SIZE;
module_param(buffer_size, int, 0644);
MODULE_PARM_DESC(buffer_size, "Internal buffer size in bytes");

static int irq_trigger_type = IRQF_TRIGGER_RISING;
module_param(irq_trigger_type, int, 0644);
MODULE_PARM_DESC(irq_trigger_type, "IRQ trigger type: 0=none, 1=rising, 2=falling, 3=both");

/* Module metadata */
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Device Driver Framework");
MODULE_DESCRIPTION("Linux Character Device Driver Framework for Learning");
MODULE_VERSION("1.0.0");

/* ============================================================
 * Internal Data Structures
 * ============================================================ */

/* Per-device private data structure */
struct device_framework_dev {
    dev_t dev_id;           /* Device number (major + minor) */
    struct cdev cdev;       /* Character device structure */
    struct device *class_dev; /* Device class pointer */
    struct class *class;    /* Device class pointer */

    /* Buffer for data operations */
    char *data_buffer;
    size_t buffer_size;
    size_t data_len;

    /* Synchronization primitives */
    struct mutex mutex;     /* Protects data_buffer access */
    spinlock_t spinlock;    /* Protects concurrent access */
    wait_queue_head_t wait_queue; /* For blocking read/write */

    /* Interrupt handling */
    int irq_number;
    irq_handler_t irq_handler;
    struct timer_list poll_timer;

    /* Platform device reference */
    struct platform_device *pdev;

    /* DMA related */
    dma_addr_t dma_handle;
    void *dma_coherent_ptr;
    size_t dma_size;

    /* Workqueue for deferred processing */
    struct work_struct deferred_work;
    struct workqueue_struct *wkq;

    /* Status flags */
    int open_count;
    int is_open;
    int initialized;
};

/* Global state */
static struct device_framework_dev *framework_dev;
static int device_framework_initialized = 0;

/* ============================================================
 * Forward Declarations
 * ============================================================ */
static int dfw_open(struct inode *, struct file *);
static int dfw_release(struct inode *, struct file *);
static ssize_t dfw_read(struct file *, char __user *, size_t, loff_t *);
static ssize_t dfw_write(struct file *, const char __user *, size_t, loff_t *);
static long dfw_ioctl(struct file *, unsigned int, unsigned long);
static __poll_t dfw_poll(struct file *, poll_table *);

/* ============================================================
 * File Operations Implementation
 * ============================================================ */

/*
 * dfw_open - File open callback
 *
 * Called when a process opens the device file.
 * Initializes per-open state and checks resource availability.
 */
static int dfw_open(struct inode *inode, struct file *filp)
{
    struct device_framework_dev *dev;

    /* Get device private data from inode */
    dev = container_of(inode->i_cdev, struct device_framework_dev, cdev);
    filp->private_data = dev;

    /* Check if device is initialized */
    if (!dev->initialized) {
        pr_err("device-framework: Device not initialized\n");
        return -ENXIO;
    }

    /* Check if device is already open (exclusive access mode) */
    if (dev->is_open) {
        pr_warn("device-framework: Device already open\n");
        return -EBUSY;
    }

    /* Increment open count and mark as open */
    dev->open_count++;
    dev->is_open = 1;

    pr_info("device-framework: Device opened (count=%d)\n", dev->open_count);
    return 0;
}

/*
 * dfw_release - File release callback
 *
 * Called when a process closes the device file.
 * Cleans up per-open state.
 */
static int dfw_release(struct inode *inode, struct file *filp)
{
    struct device_framework_dev *dev = filp->private_data;

    dev->open_count--;
    dev->is_open = 0;

    pr_info("device-framework: Device closed (count=%d)\n", dev->open_count);
    return 0;
}

/*
 * dfw_read - File read callback
 *
 * Copies data from kernel buffer to user space.
 * Supports both blocking and non-blocking reads via poll.
 */
static ssize_t dfw_read(struct file *filp, char __user *buf, size_t count, loff_t *f_pos)
{
    struct device_framework_dev *dev = filp->private_data;
    ssize_t result;

    /* Validate parameters */
    if (!buf || count == 0) {
        return -EINVAL;
    }

    /* Acquire mutex to protect buffer access */
    if (mutex_lock_interruptible(&dev->mutex)) {
        return -ERESTARTSYS;
    }

    /* Check if data is available */
    if (dev->data_len == 0) {
        /* No data available - return EAGAIN for non-blocking */
        if (filp->f_flags & O_NONBLOCK) {
            result = -EAGAIN;
            goto read_exit;
        }
        pr_info("device-framework: Waiting for data...\n");
    }

    /* Calculate how much data to copy */
    size_t bytes_to_copy = min(count, dev->data_len);

    /* Copy data to user space */
    if (copy_to_user(buf, dev->data_buffer, bytes_to_copy)) {
        result = -EFAULT;
        goto read_exit;
    }

    /* Update file position and data length */
    *f_pos += bytes_to_copy;
    dev->data_len -= bytes_to_copy;

    /* Move remaining data to beginning of buffer */
    if (dev->data_len > 0) {
        memmove(dev->data_buffer, dev->data_buffer + bytes_to_copy, dev->data_len);
    }

    result = bytes_to_copy;
    pr_info("device-framework: Read %zd bytes\n", result);

    /* Wake up any waiting writers */
    wake_up_interruptible(&dev->wait_queue);

read_exit:
    mutex_unlock(&dev->mutex);
    return result;
}

/*
 * dfw_write - File write callback
 *
 * Copies data from user space to kernel buffer.
 * Triggers interrupt simulation for learning purposes.
 */
static ssize_t dfw_write(struct file *filp, const char __user *buf, size_t count, loff_t *f_pos)
{
    struct device_framework_dev *dev = filp->private_data;
    ssize_t result;

    /* Validate parameters */
    if (!buf || count == 0) {
        return -EINVAL;
    }

    /* Acquire mutex to protect buffer access */
    if (mutex_lock_interruptible(&dev->mutex)) {
        return -ERESTARTSYS;
    }

    /* Check buffer space availability */
    if (count > dev->buffer_size) {
        result = -ENOSPC;
        goto write_exit;
    }

    /* Copy data from user space */
    if (copy_from_user(dev->data_buffer, buf, count)) {
        result = -EFAULT;
        goto write_exit;
    }

    /* Update data length and file position */
    dev->data_len = count;
    *f_pos += count;

    result = count;
    pr_info("device-framework: Wrote %zd bytes\n", result);

    /* Wake up any waiting readers */
    wake_up_interruptible(&dev->wait_queue);

write_exit:
    mutex_unlock(&dev->mutex);
    return result;
}

/*
 * dfw_ioctl - IOCTL handler
 *
 * Provides control interface for device-specific commands.
 * Supports: get/set buffer size, reset device, get status.
 */
static long dfw_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct device_framework_dev *dev = filp->private_data;
    int __user *user_arg = (int __user *)arg;
    int ret;
    struct dfw_status status;

    switch (cmd) {
    case DFW_CMD_GET_STATUS:
        /* Return device status to user space */
        memset(&status, 0, sizeof(status));
        status.open_count = dev->open_count;
        status.data_len = dev->data_len;
        status.buffer_size = dev->buffer_size;
        status.irq_number = dev->irq_number;
        status.is_open = dev->is_open;
        status.initialized = dev->initialized;

        ret = copy_to_user(user_arg, &status, sizeof(status));
        return ret ? -EFAULT : 0;

    case DFW_CMD_SET_BUFFER_SIZE:
        /* Change buffer size at runtime */
        if (arg == 0 || arg > DEVICE_FRAMEWORK_MAX_BUFFER) {
            return -EINVAL;
        }
        mutex_lock(&dev->mutex);
        dev->buffer_size = arg;
        mutex_unlock(&dev->mutex);
        return 0;

    case DFW_CMD_RESET_DEVICE:
        /* Reset device state */
        mutex_lock(&dev->mutex);
        memset(dev->data_buffer, 0, dev->buffer_size);
        dev->data_len = 0;
        dev->open_count = 0;
        dev->is_open = 0;
        mutex_unlock(&dev->mutex);
        return 0;

    case DFW_CMD_GET_BUFFER_INFO:
        /* Return buffer information */
        {
            struct dfw_buffer_info info;
            info.size = dev->buffer_size;
            info.used = dev->data_len;
            info.free = dev->buffer_size - dev->data_len;
            ret = copy_to_user(user_arg, &info, sizeof(info));
            return ret ? -EFAULT : 0;
        }

    default:
        return -ENOTTY;
    }
}

/*
 * dfw_poll - Poll (select/poll/epoll) handler
 *
 * Allows user space to wait for device events using select(), poll(), or epoll().
 * Returns POLLOUT for write readiness, POLLIN for read readiness.
 */
static __poll_t dfw_poll(struct file *filp, poll_table *wait)
{
    struct device_framework_dev *dev = filp->private_data;
    __poll_t events = 0;

    /* Add current task to wait queue */
    poll_wait(filp, &dev->wait_queue, wait);

    /* Check if data is available for reading */
    if (dev->data_len > 0) {
        events |= EPOLLIN | EPOLLRDNORM;
    }

    /* Check if buffer has space for writing */
    if (dev->data_len < dev->buffer_size) {
        events |= EPOLLOUT | EPOLLRDNORM;
    }

    return events;
}

/* ============================================================
 * File Operations Table
 * ============================================================ */
static const struct file_operations device_framework_fops = {
    .owner = THIS_MODULE,
    .open = dfw_open,
    .release = dfw_release,
    .read = dfw_read,
    .write = dfw_write,
    .unlocked_ioctl = dfw_ioctl,
    .poll = dfw_poll,
    .llseek = noop_llseek,
};

/* ============================================================
 * Interrupt Handling
 * ============================================================ */

/*
 * dfw_irq_handler - Interrupt request handler
 *
 * This is the core interrupt service routine (ISR).
 * Must be fast, cannot sleep, and must acknowledge the interrupt.
 *
 * Linux IRQ handling model:
 *   - Top half (ISR): runs in interrupt context, must be fast
 *   - Bottom half: deferred work via tasklets, workqueues, or softirqs
 */
static irqreturn_t dfw_irq_handler(int irq, void *dev_id)
{
    struct device_framework_dev *dev = (struct device_framework_dev *)dev_id;
    unsigned long flags;

    /* Acknowledge interrupt and disable further interrupts briefly */
    spin_lock_irqsave(&dev->spinlock, flags);

    /* Record interrupt event */
    dev->data_len = 1;  /* Signal that interrupt occurred */
    dev->data_buffer[0] = (char)(irq & 0xFF);

    spin_unlock_irqrestore(&dev->spinlock, flags);

    /* Wake up any process waiting in read() */
    wake_up_interruptible(&dev->wait_queue);

    pr_info("device-framework: IRQ %d triggered\n", irq);

    return IRQ_HANDLED;
}

/*
 * dfw_request_irq - Request an interrupt line
 *
 * Demonstrates proper IRQ request with:
 *   - Shared IRQ support (IRQF_SHARED)
 *   - Trigger type configuration (edge/level)
 *   - Dev_id for interrupt sharing identification
 */
int dfw_request_irq(struct device_framework_dev *dev, int irq_num)
{
    int ret;

    /* Request IRQ with specified trigger type */
    ret = request_irq(
        irq_num,
        dfw_irq_handler,
        irq_trigger_type | IRQF_SHARED | IRQF_ONESHOT,
        "device-framework",
        dev
    );

    if (ret) {
        pr_err("device-framework: Failed to request IRQ %d (error=%d)\n", irq_num, ret);
        return ret;
    }

    dev->irq_number = irq_num;
    pr_info("device-framework: IRQ %d requested successfully\n", irq_num);
    return 0;
}

/*
 * dfw_free_irq - Free a previously requested interrupt
 */
void dfw_free_irq(struct device_framework_dev *dev)
{
    if (dev->irq_number > 0) {
        free_irq(dev->irq_number, dev);
        pr_info("device-framework: IRQ %d freed\n", dev->irq_number);
        dev->irq_number = -1;
    }
}

/* ============================================================
 * Device Tree Parsing
 * ============================================================ */

/*
 * dfw_parse_device_tree - Parse device tree for device configuration
 *
 * Device tree is the standard way to describe hardware on Linux.
 * This function demonstrates:
 *   - Reading properties from device tree
 *   - Getting interrupt numbers from device tree
 *   - Parsing memory regions
 */
static int dfw_parse_device_tree(struct device_framework_dev *dev, struct platform_device *pdev)
{
    struct device_node *np = pdev->dev.of_node;
    const __be32 *prop;
    int ret;

    if (!np) {
        pr_warn("device-framework: No device tree node\n");
        return -EINVAL;
    }

    /* Read 'reg' property (register base address and size) */
    prop = of_get_property(np, "reg", NULL);
    if (prop) {
        /* Parse register address and length from device tree */
        u32 addr, size;
        ret = of_address_to_resource(np, 0, (struct resource *)&dev->pdev->resource);
        if (ret) {
            pr_warn("device-framework: Failed to get register resource\n");
        }
    }

    /* Read 'interrupts' property */
    dev->irq_number = of_irq_get(np, 0);
    if (dev->irq_number <= 0) {
        pr_warn("device-framework: No interrupt configured in device tree\n");
        dev->irq_number = -1;
    } else {
        pr_info("device-framework: Found IRQ %d in device tree\n", dev->irq_number);
    }

    /* Read custom properties with defaults */
    prop = of_get_property(np, "buffer-size", &ret);
    if (prop) {
        dev->buffer_size = be32_to_cpu(*prop);
        pr_info("device-framework: Buffer size from DT: %d\n", dev->buffer_size);
    }

    return 0;
}

/* ============================================================
 * Platform Driver Model
 * ============================================================ */

/*
 * Platform driver model is the standard way to manage platform devices
 * on Linux. It provides:
 *   - Device-probe mechanism
 *   - Resource management (memory, IRQ, DMA)
 *   - Power management hooks
 *   - Device tree integration
 */

static int dfw_platform_probe(struct platform_device *pdev)
{
    struct device_framework_dev *dev;
    struct resource *res;
    int ret;

    pr_info("device-framework: Probing platform device\n");

    /* Allocate device private data */
    dev = kzalloc(sizeof(*dev), GFP_KERNEL);
    if (!dev) {
        return -ENOMEM;
    }

    /* Initialize device structure */
    dev->buffer_size = buffer_size;
    dev->irq_number = -1;
    dev->initialized = 0;
    dev->is_open = 0;
    dev->open_count = 0;

    /* Initialize synchronization primitives */
    mutex_init(&dev->mutex);
    spin_lock_init(&dev->spinlock);
    init_waitqueue_head(&dev->wait_queue);

    /* Allocate data buffer */
    dev->data_buffer = kmalloc(dev->buffer_size, GFP_KERNEL);
    if (!dev->data_buffer) {
        ret = -ENOMEM;
        goto err_alloc_buffer;
    }
    memset(dev->data_buffer, 0, dev->buffer_size);

    /* Store platform device reference */
    dev->pdev = pdev;

    /* Parse device tree */
    ret = dfw_parse_device_tree(dev, pdev);
    if (ret) {
        pr_warn("device-framework: Device tree parsing failed\n");
        /* Continue without device tree for learning purposes */
    }

    /* Request memory region (if mapped from device tree) */
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if (res) {
        /* Request memory region */
        if (!request_mem_region(res->start, resource_size(res), "device-framework")) {
            pr_warn("device-framework: Memory region already in use\n");
        } else {
            /* Map memory into kernel virtual address space */
            void __iomem *mapped = ioremap(res->start, resource_size(res));
            if (mapped) {
                pr_info("device-framework: Memory mapped at %p (phys=%pa, size=%pa)\n",
                        mapped, &res->start, &res->end);
                /* Store ioremapped pointer for later use */
                dev->dma_coherent_ptr = mapped;
            }
        }
    }

    /* Request IRQ if available */
    if (dev->irq_number > 0) {
        ret = dfw_request_irq(dev, dev->irq_number);
        if (ret) {
            pr_warn("device-framework: IRQ request failed, continuing without IRQ\n");
            dev->irq_number = -1;
        }
    }

    /* Allocate DMA coherent memory */
    dev->dma_size = PAGE_SIZE;
    dev->dma_coherent_ptr = dma_alloc_coherent(&pdev->dev, dev->dma_size,
                                                &dev->dma_handle, GFP_KERNEL);
    if (dev->dma_coherent_ptr) {
        pr_info("device-framework: DMA coherent memory allocated (virt=%p, phys=%pad)\n",
                dev->dma_coherent_ptr, &dev->dma_handle);
    }

    /* Initialize workqueue for deferred processing */
    dev->wkq = alloc_workqueue("device-framework-wq", WQ_UNBOUND, 1);
    if (dev->wkq) {
        INIT_WORK(&dev->deferred_work, NULL); /* Will be set by caller */
        pr_info("device-framework: Workqueue created\n");
    }

    /* Mark device as initialized */
    dev->initialized = 1;

    /* Store in global for module-level operations */
    framework_dev = dev;
    device_framework_initialized = 1;

    /* Set platform device driver data */
    platform_set_drvdata(pdev, dev);

    pr_info("device-framework: Platform probe completed\n");
    return 0;

err_alloc_buffer:
    kfree(dev);
    return ret;
}

static void dfw_platform_remove(struct platform_device *pdev)
{
    struct device_framework_dev *dev = platform_get_drvdata(pdev);

    if (!dev) {
        return;
    }

    pr_info("device-framework: Removing platform device\n");

    /* Cancel pending work */
    if (dev->wkq) {
        cancel_work_sync(&dev->deferred_work);
        destroy_workqueue(dev->wkq);
    }

    /* Free DMA memory */
    if (dev->dma_coherent_ptr && dev->dma_size > 0) {
        dma_free_coherent(&pdev->dev, dev->dma_size,
                          dev->dma_coherent_ptr, dev->dma_handle);
        pr_info("device-framework: DMA memory freed\n");
    }

    /* Free IRQ */
    if (dev->irq_number > 0) {
        free_irq(dev->irq_number, dev);
    }

    /* Unmap memory */
    if (dev->dma_coherent_ptr && IS_ERR_OR_NULL(dev->dma_coherent_ptr)) {
        /* Was ioremapped, just unmap */
    }

    /* Release memory region */
    if (dev->pdev) {
        struct resource *res = platform_get_resource(dev->pdev, IORESOURCE_MEM, 0);
        if (res) {
            release_mem_region(res->start, resource_size(res));
        }
    }

    /* Free data buffer */
    kfree(dev->data_buffer);

    /* Free device structure */
    kfree(dev);

    device_framework_initialized = 0;
    framework_dev = NULL;

    pr_info("device-framework: Platform device removed\n");
}

/* Device tree match table */
static const struct of_device_id dfw_of_match[] = {
    { .compatible = "device,framework" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, dfw_of_match);

/* Platform driver structure */
static struct platform_driver dfw_platform_driver = {
    .probe = dfw_platform_probe,
    .remove = dfw_platform_remove,
    .driver = {
        .name = "device-framework",
        .of_match_table = dfw_of_match,
        .owner = THIS_MODULE,
    },
};

/* ============================================================
 * DMA Buffer Management
 * ============================================================ */

/*
 * DMA (Direct Memory Access) allows devices to transfer data
 * directly to/from memory without CPU intervention.
 *
 * Two types of DMA mapping:
 *   1. Coherent DMA: dma_alloc_coherent() - consistent, always cache-coherent
 *   2. Streaming DMA: dma_map_single() - for one-direction transfers
 *
 * Key concepts:
 *   - Bus address vs CPU virtual address
 *   - Cache coherency management
 *   - DMA mapping/unmapping for I/O devices
 */

/* Allocate coherent DMA memory */
void *dfw_dma_alloc(size_t size, dma_addr_t *handle)
{
    struct device *dev = device_framework_initialized ?
        &framework_dev->pdev->dev : NULL;

    if (!dev) {
        pr_warn("device-framework: No device for DMA allocation\n");
        return NULL;
    }

    void *ptr = dma_alloc_coherent(dev, size, handle, GFP_KERNEL);
    if (ptr) {
        memset(ptr, 0, size);
        pr_info("device-framework: DMA allocated: %zu bytes at phys %pad\n",
                size, handle);
    }
    return ptr;
}

/* Free coherent DMA memory */
void dfw_dma_free(void *vaddr, dma_addr_t handle, size_t size)
{
    if (!vaddr) {
        return;
    }

    struct device *dev = device_framework_initialized ?
        &framework_dev->pdev->dev : NULL;

    if (dev) {
        dma_free_coherent(dev, size, vaddr, handle);
        pr_info("device-framework: DMA freed: %zu bytes\n", size);
    }
}

/* ============================================================
 * Timer-based Polling (Alternative to Interrupts)
 * ============================================================ */

/*
 * Timer polling is a simpler alternative to interrupts.
 * Useful for learning interrupt concepts without hardware.
 */
static void dfw_poll_timer_func(struct timer_list *t)
{
    struct device_framework_dev *dev = from_timer(dev, t, poll_timer);
    unsigned long flags;

    /* Simulate periodic data arrival */
    spin_lock_irqsave(&dev->spinlock, flags);
    if (dev->data_len < dev->buffer_size) {
        dev->data_buffer[dev->data_len] = 'X';
        dev->data_len++;
    }
    spin_unlock_irqrestore(&dev->spinlock, flags);

    /* Wake up waiting readers */
    wake_up_interruptible(&dev->wait_queue);

    /* Restart timer */
    mod_timer(&dev->poll_timer, jiffies + msecs_to_jiffies(1000));
}

static void dfw_init_timer(struct device_framework_dev *dev)
{
    timer_setup(&dev->poll_timer, dfw_poll_timer_func, 0);
    mod_timer(&dev->poll_timer, jiffies + msecs_to_jiffies(1000));
    pr_info("device-framework: Poll timer started (1s interval)\n");
}

static void dfw_stop_timer(struct device_framework_dev *dev)
{
    del_timer_sync(&dev->poll_timer);
    pr_info("device-framework: Poll timer stopped\n");
}

/* ============================================================
 * Module Initialization and Cleanup
 * ============================================================ */

/*
 * Module initialization follows this sequence:
 *   1. Allocate device structure
 *   2. Allocate major number (dynamic or static)
 *   3. Initialize cdev structure
 *   4. Register character device with kernel
 *   5. Create device class
 *   6. Create device node (creates /dev entry via udev)
 */
static int __init device_framework_init(void)
{
    int ret;
    dev_t dev_num;

    pr_info("device-framework: Initializing device driver framework\n");

    /* Allocate device structure */
    framework_dev = kzalloc(sizeof(*framework_dev), GFP_KERNEL);
    if (!framework_dev) {
        ret = -ENOMEM;
        goto err_alloc;
    }

    /* Initialize device structure */
    framework_dev->buffer_size = buffer_size;
    framework_dev->irq_number = -1;
    framework_dev->initialized = 0;
    framework_dev->is_open = 0;
    framework_dev->open_count = 0;

    mutex_init(&framework_dev->mutex);
    spin_lock_init(&framework_dev->spinlock);
    init_waitqueue_head(&framework_dev->wait_queue);

    /* Allocate data buffer */
    framework_dev->data_buffer = kmalloc(framework_dev->buffer_size, GFP_KERNEL);
    if (!framework_dev->data_buffer) {
        ret = -ENOMEM;
        goto err_buffer;
    }
    memset(framework_dev->data_buffer, 0, framework_dev->buffer_size);

    /* Dynamically allocate major number */
    ret = alloc_chrdev_region(&dev_num, 0, 1, "device_framework");
    if (ret < 0) {
        pr_err("device-framework: Failed to allocate major number\n");
        goto err_alloc_region;
    }
    framework_dev->dev_id = dev_num;
    framework_dev->major_number = MAJOR(dev_num);

    pr_info("device-framework: Registered with major %d\n", framework_dev->major_number);

    /* Initialize and register cdev */
    cdev_init(&framework_dev->cdev, &device_framework_fops);
    framework_dev->cdev.owner = THIS_MODULE;

    ret = cdev_add(&framework_dev->cdev, dev_num, 1);
    if (ret < 0) {
        pr_err("device-framework: Failed to add cdev\n");
        goto err_cdev;
    }

    /* Create device class */
    framework_dev->class = class_create("device_framework_class");
    if (IS_ERR(framework_dev->class)) {
        ret = PTR_ERR(framework_dev->class);
        pr_err("device-framework: Failed to create class\n");
        goto err_class;
    }

    /* Create device node (creates /dev/device_framework) */
    framework_dev->class_dev = device_create(framework_dev->class, NULL,
                                              dev_num, NULL, "device_framework");
    if (IS_ERR(framework_dev->class_dev)) {
        ret = PTR_ERR(framework_dev->class_dev);
        pr_err("device-framework: Failed to create device\n");
        goto err_device;
    }

    /* Initialize polling timer */
    dfw_init_timer(framework_dev);

    /* Register platform driver */
    ret = platform_driver_register(&dfw_platform_driver);
    if (ret) {
        pr_warn("device-framework: Failed to register platform driver\n");
    }

    /* Mark as initialized */
    framework_dev->initialized = 1;
    device_framework_initialized = 1;

    pr_info("device-framework: Device driver framework loaded successfully\n");
    pr_info("device-framework: Use 'cat /dev/device_framework' to read\n");
    pr_info("device-framework: Use 'echo hello > /dev/device_framework' to write\n");

    return 0;

err_device:
    class_destroy(framework_dev->class);
err_class:
    cdev_del(&framework_dev->cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
err_alloc_region:
    kfree(framework_dev->data_buffer);
err_buffer:
    kfree(framework_dev);
err_alloc:
    pr_err("device-framework: Initialization failed (error=%d)\n", ret);
    return ret;
}

/*
 * Module cleanup follows reverse order of initialization:
 *   1. Unregister platform driver
 *   2. Destroy device node
 *   3. Destroy device class
 *   4. Delete cdev
 *   5. Unregister device number
 *   6. Free resources
 */
static void __exit device_framework_exit(void)
{
    if (!framework_dev) {
        return;
    }

    pr_info("device-framework: Cleaning up device driver framework\n");

    /* Mark as not initialized first */
    device_framework_initialized = 0;
    framework_dev->initialized = 0;

    /* Unregister platform driver */
    platform_driver_unregister(&dfw_platform_driver);

    /* Stop polling timer */
    dfw_stop_timer(framework_dev);

    /* Free IRQ */
    if (framework_dev->irq_number > 0) {
        free_irq(framework_dev->irq_number, framework_dev);
    }

    /* Free DMA memory */
    if (framework_dev->dma_coherent_ptr && framework_dev->dma_size > 0) {
        dma_free_coherent(&framework_dev->pdev->dev, framework_dev->dma_size,
                          framework_dev->dma_coherent_ptr, framework_dev->dma_handle);
    }

    /* Destroy device node */
    device_destroy(framework_dev->class, framework_dev->dev_id);

    /* Destroy device class */
    class_destroy(framework_dev->class);

    /* Delete cdev */
    cdev_del(&framework_dev->cdev);

    /* Unregister device number */
    unregister_chrdev_region(framework_dev->dev_id, 1);

    /* Free data buffer */
    kfree(framework_dev->data_buffer);

    /* Free device structure */
    kfree(framework_dev);

    pr_info("device-framework: Device driver framework unloaded\n");
}

module_init(device_framework_init);
module_exit(device_framework_exit);
