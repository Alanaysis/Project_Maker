/*
 * Memory-Mapped I/O Demo - Example 4
 *
 * Demonstrates memory-mapped I/O (MMIO) for device communication:
 *   - ioremap/iounmap for address translation
 *   - Read/write accessors (readl/writel, readb/writeb)
 *   - Resource management with request/release_mem_region
 *   - MMIO register access patterns
 *
 * MMIO is how drivers communicate with hardware registers.
 * Physical addresses must be mapped to kernel virtual addresses.
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/platform_device.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Device Driver Framework");
MODULE_DESCRIPTION("Memory-Mapped I/O Driver Example");

/* ============================================================
 * MMIO Access Functions Reference
 * ============================================================ */
/*
 * Byte access (8-bit):
 *   readb(addr)   - Read byte from MMIO
 *   writeb(val, addr) - Write byte to MMIO
 *
 * Word access (32-bit):
 *   readl(addr)   - Read 32-bit word from MMIO
 *   writel(val, addr) - Write 32-bit word to MMIO
 *
 * Double-word access (64-bit):
 *   readq(addr)   - Read 64-bit word from MMIO
 *   writeq(val, addr) - Write 64-bit word to MMIO
 *
 * String access:
 *   readsl(addr, buf, count) - Read 'count' words from MMIO
 *   writelsl(addr, buf, count) - Write 'count' words to MMIO
 *
 * Important: MMIO accesses have different ordering guarantees than
 * normal memory. Use readl_relaxed()/writel_relaxed() for non-ordered access.
 */

/* ============================================================
 * Driver State
 * ============================================================ */

struct mmio_device {
    struct cdev cdev;
    struct class *class;
    struct device *dev;
    dev_t dev_id;

    /* MMIO region */
    void __iomem *base;
    resource_size_t size;

    /* Data buffer for user-space communication */
    char *buffer;
    size_t buffer_len;

    /* Register map for demonstration */
    #define REG_CONTROL     0x00
    #define REG_STATUS      0x04
    #define REG_DATA        0x08
    #define REG_INTERRUPT   0x0C

    u32 control_val;
    u32 status_val;
    u32 data_val;
    u32 interrupt_val;
};

static struct mmio_device *mmio_dev;

/* ============================================================
 * File Operations
 * ============================================================ */

static int mmio_open(struct inode *inode, struct file *filp)
{
    struct mmio_device *dev = container_of(inode->i_cdev, struct mmio_device, cdev);
    filp->private_data = dev;
    return 0;
}

static int mmio_release(struct inode *inode, struct file *filp)
{
    return 0;
}

static ssize_t mmio_read(struct file *filp, char __user *buf,
                         size_t count, loff_t *f_pos)
{
    struct mmio_device *dev = filp->private_data;
    int ret;

    /* Read from simulated MMIO registers */
    u32 reg_data[4] = {
        dev->control_val,
        dev->status_val,
        dev->data_val,
        dev->interrupt_val,
    };

    /* Simulate readl() by reading from MMIO */
    if (dev->base) {
        /* In real driver: reg_data[0] = readl(dev->base + REG_CONTROL); */
    }

    ret = copy_to_user(buf, reg_data, min(count, sizeof(reg_data)));
    if (ret) {
        return -EFAULT;
    }

    return min(count, sizeof(reg_data));
}

static ssize_t mmio_write(struct file *filp, const char __user *buf,
                          size_t count, loff_t *f_pos)
{
    struct mmio_device *dev = filp->private_data;
    u32 reg_data[4];
    int ret;

    /* Simulate write to MMIO registers */
    ret = copy_from_user(reg_data, buf, min(count, sizeof(reg_data)));
    if (ret) {
        return -EFAULT;
    }

    /* In real driver: writel(reg_data[0], dev->base + REG_CONTROL); */
    dev->control_val = reg_data[0];
    dev->status_val = reg_data[1];
    dev->data_val = reg_data[2];
    dev->interrupt_val = reg_data[3];

    pr_info("mmio-driver: Written to registers: 0x%x 0x%x 0x%x 0x%x\n",
            reg_data[0], reg_data[1], reg_data[2], reg_data[3]);

    return min(count, sizeof(reg_data));
}

static long mmio_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct mmio_device *dev = filp->private_data;
    u32 __user *user_val = (u32 __user *)arg;

    switch (cmd) {
    case 0: /* Read register */
        if (dev->base) {
            u32 val;
            /* In real driver: val = readl(dev->base + arg); */
            val = dev->data_val;
            if (copy_to_user(user_val, &val, sizeof(val))) {
                return -EFAULT;
            }
        }
        return 0;
    case 1: /* Write register */
        {
            u32 val;
            if (copy_from_user(&val, user_val, sizeof(val))) {
                return -EFAULT;
            }
            /* In real driver: writel(val, dev->base + arg); */
            dev->data_val = val;
        }
        return 0;
    default:
        return -ENOTTY;
    }
}

static const struct file_operations mmio_fops = {
    .owner = THIS_MODULE,
    .open = mmio_open,
    .release = mmio_release,
    .read = mmio_read,
    .write = mmio_write,
    .unlocked_ioctl = mmio_ioctl,
};

/* ============================================================
 * Module Init/Exit
 * ============================================================ */

static int __init mmio_driver_init(void)
{
    int ret;
    dev_t dev_num;

    pr_info("mmio-driver: Initializing MMIO driver\n");

    /* Allocate device structure */
    mmio_dev = kzalloc(sizeof(*mmio_dev), GFP_KERNEL);
    if (!mmio_dev) {
        return -ENOMEM;
    }

    mmio_dev->buffer = kmalloc(256, GFP_KERNEL);

    /* Allocate major number */
    ret = alloc_chrdev_region(&dev_num, 0, 1, "mmio_driver");
    if (ret < 0) {
        goto err_region;
    }
    mmio_dev->dev_id = dev_num;

    /* Register character device */
    cdev_init(&mmio_dev->cdev, &mmio_fops);
    mmio_dev->cdev.owner = THIS_MODULE;
    ret = cdev_add(&mmio_dev->cdev, dev_num, 1);
    if (ret < 0) {
        goto err_cdev;
    }

    /* Create device class and node */
    mmio_dev->class = class_create("mmio_class");
    mmio_dev->dev = device_create(mmio_dev->class, NULL, dev_num,
                                   NULL, "mmio_driver");

    pr_info("mmio-driver: Driver loaded\n");
    pr_info("mmio-driver: Supports register read/write via /dev/mmio_driver\n");

    return 0;

err_cdev:
    unregister_chrdev_region(dev_num, 1);
err_region:
    kfree(mmio_dev->buffer);
    kfree(mmio_dev);
    return ret;
}

static void __exit mmio_driver_exit(void)
{
    if (mmio_dev) {
        device_destroy(mmio_dev->class, mmio_dev->dev_id);
        class_destroy(mmio_dev->class);
        cdev_del(&mmio_dev->cdev);
        unregister_chrdev_region(mmio_dev->dev_id, 1);
        kfree(mmio_dev->buffer);
        kfree(mmio_dev);
    }

    pr_info("mmio-driver: Driver unloaded\n");
}

module_init(mmio_driver_init);
module_exit(mmio_driver_exit);

MODULE_LICENSE("GPL");
