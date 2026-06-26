/*
 * Simple Character Device Driver - Example 1
 *
 * This is the simplest form of a Linux character device driver.
 * It demonstrates:
 *   - Module lifecycle (init/exit)
 *   - Dynamic major number allocation
 *   - cdev registration
 *   - Device class and node creation
 *   - Basic file operations
 *
 * This is the entry point for learning Linux device drivers.
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Device Driver Framework");
MODULE_DESCRIPTION("Simple Character Device Driver Example");

/* Driver state */
static int simple_major = 0;
static struct cdev simple_cdev;
static struct class *simple_class;
static struct device *simple_device;

/* Data buffer */
static char simple_buffer[256];
static int buffer_count = 0;

/* ============================================================
 * File Operations
 * ============================================================ */

static int simple_open(struct inode *inode, struct file *filp)
{
    pr_info("simple-driver: device opened\n");
    return 0;
}

static int simple_release(struct inode *inode, struct file *filp)
{
    pr_info("simple-driver: device closed\n");
    return 0;
}

static ssize_t simple_read(struct file *filp, char __user *buf,
                           size_t count, loff_t *f_pos)
{
    int bytes_to_copy;

    if (*f_pos >= buffer_count) {
        return 0;  /* EOF */
    }

    bytes_to_copy = min(count, buffer_count - *f_pos);

    if (copy_to_user(buf, simple_buffer + *f_pos, bytes_to_copy)) {
        return -EFAULT;
    }

    *f_pos += bytes_to_copy;
    pr_info("simple-driver: read %d bytes\n", bytes_to_copy);
    return bytes_to_copy;
}

static ssize_t simple_write(struct file *filp, const char __user *buf,
                            size_t count, loff_t *f_pos)
{
    int bytes_to_copy;

    bytes_to_copy = min(count, (size_t)(sizeof(simple_buffer) - 1));

    if (copy_from_user(simple_buffer, buf, bytes_to_copy)) {
        return -EFAULT;
    }

    simple_buffer[bytes_to_copy] = '\0';
    buffer_count = bytes_to_copy;
    *f_pos = 0;  /* Reset position for next write */

    pr_info("simple-driver: wrote %d bytes: \"%s\"\n", bytes_to_copy, simple_buffer);
    return bytes_to_copy;
}

static const struct file_operations simple_fops = {
    .owner = THIS_MODULE,
    .open = simple_open,
    .release = simple_release,
    .read = simple_read,
    .write = simple_write,
};

/* ============================================================
 * Module Init/Exit
 * ============================================================ */

static int __init simple_driver_init(void)
{
    int ret;
    dev_t dev_num;

    /* Allocate major/minor numbers dynamically */
    ret = alloc_chrdev_region(&dev_num, 0, 1, "simple_driver");
    if (ret < 0) {
        pr_err("simple-driver: Failed to allocate major number\n");
        return ret;
    }
    simple_major = MAJOR(dev_num);
    pr_info("simple-driver: Registered with major %d\n", simple_major);

    /* Initialize cdev */
    cdev_init(&simple_cdev, &simple_fops);
    simple_cdev.owner = THIS_MODULE;

    /* Add cdev to kernel */
    ret = cdev_add(&simple_cdev, dev_num, 1);
    if (ret < 0) {
        pr_err("simple-driver: Failed to add cdev\n");
        goto err_cdev;
    }

    /* Create device class */
    simple_class = class_create("simple_class");
    if (IS_ERR(simple_class)) {
        ret = PTR_ERR(simple_class);
        pr_err("simple-driver: Failed to create class\n");
        goto err_class;
    }

    /* Create device node at /dev/simple_driver */
    simple_device = device_create(simple_class, NULL, dev_num, NULL, "simple_driver");
    if (IS_ERR(simple_device)) {
        ret = PTR_ERR(simple_device);
        pr_err("simple-driver: Failed to create device\n");
        goto err_device;
    }

    pr_info("simple-driver: Driver loaded successfully\n");
    pr_info("simple-driver: Use: echo hello > /dev/simple_driver\n");
    pr_info("simple-driver: Use: cat /dev/simple_driver\n");

    return 0;

err_device:
    class_destroy(simple_class);
err_class:
    cdev_del(&simple_cdev);
err_cdev:
    unregister_chrdev_region(dev_num, 1);
    return ret;
}

static void __exit simple_driver_exit(void)
{
    dev_t dev_num = MKDEV(simple_major, 0);

    device_destroy(simple_class, dev_num);
    class_destroy(simple_class);
    cdev_del(&simple_cdev);
    unregister_chrdev_region(dev_num, 1);

    pr_info("simple-driver: Driver unloaded\n");
}

module_init(simple_driver_init);
module_exit(simple_driver_exit);
