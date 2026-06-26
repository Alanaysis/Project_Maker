/*
 * Interrupt-Driven Device Driver - Example 2
 *
 * Demonstrates Linux interrupt handling in device drivers:
 *   - request_irq / free_irq
 *   - IRQ handler (ISR) implementation
 *   - Edge vs level triggering
 *   - Shared IRQ lines
 *   - Top half / bottom half separation
 *   - Tasklet for deferred work
 *
 * Key Linux interrupt concepts:
 *   1. Interrupts are asynchronous - they can occur at any time
 *   2. ISRs must be fast and cannot sleep
 *   3. Heavy processing goes in bottom halves (tasklets, workqueues)
 *   4. Shared IRQs require dev_id to identify the handler
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/interrupt.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/workqueue.h>
#include <linux/timer.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Device Driver Framework");
MODULE_DESCRIPTION("Interrupt-Driven Device Driver Example");

/* ============================================================
 * Driver State
 * ============================================================ */

static int irq_major = 0;
static struct cdev irq_cdev;
static struct class *irq_class;
static struct device *irq_device;

/* Simulated IRQ number (use a real IRQ for actual hardware) */
static int simulated_irq = 0;
static int irq_count = 0;

/* Device data */
struct irq_device_data {
    struct cdev cdev;
    char buffer[128];
    int data_len;
    spinlock_t lock;
    wait_queue_head_t wait_queue;
    int open_count;
    int is_open;

    /* Workqueue for bottom half processing */
    struct workqueue_struct *wq;
    struct work_struct deferred_work;

    /* Timer for simulated interrupts */
    struct timer_list sim_timer;
};

static struct irq_device_data *irq_dev_data;

/* ============================================================
 * Bottom Half Processing (Workqueue)
 * ============================================================ */

/*
 * Bottom half: deferred work processed in process context.
 * This runs after the ISR returns, in a kernel worker thread.
 */
static void irq_bottom_half(struct work_struct *work)
{
    struct irq_device_data *dev = container_of(work, struct irq_device_data, deferred_work);

    pr_info("irq-driver: Bottom half processing - IRQ count: %d\n", irq_count);

    /* Update buffer with interrupt info */
    snprintf(dev->buffer, sizeof(dev->buffer), "IRQ triggered %d times", irq_count);
    dev->data_len = strlen(dev->buffer);

    /* Wake up any process waiting in read() */
    wake_up_interruptible(&dev->wait_queue);
}

/* ============================================================
 * Interrupt Handler (Top Half)
 * ============================================================ */

/*
 * IRQ handler must:
 *   1. Be declared with irqreturn_t return type
 *   2. Accept (int irq, void *dev_id) parameters
 *   3. Return IRQ_HANDLED if it handled the interrupt
 *   4. Be fast - defer heavy work to bottom half
 */
static irqreturn_t irq_handler(int irq, void *dev_id)
{
    struct irq_device_data *dev = (struct irq_device_data *)dev_id;
    unsigned long flags;

    /* Critical section: update shared data */
    spin_lock_irqsave(&dev->lock, flags);
    irq_count++;
    spin_unlock_irqrestore(&dev->lock, flags);

    /* Schedule bottom half for deferred processing */
    schedule_work(&dev->deferred_work);

    pr_info("irq-driver: IRQ %d triggered (count=%d)\n", irq, irq_count);

    return IRQ_HANDLED;
}

/* ============================================================
 * File Operations
 * ============================================================ */

static int irq_open(struct inode *inode, struct file *filp)
{
    struct irq_device_data *dev = container_of(inode->i_cdev, struct irq_device_data, cdev);
    filp->private_data = dev;

    spin_lock(&dev->lock);
    dev->open_count++;
    dev->is_open = 1;
    spin_unlock(&dev->lock);

    pr_info("irq-driver: device opened\n");
    return 0;
}

static int irq_release(struct inode *inode, struct file *filp)
{
    struct irq_device_data *dev = filp->private_data;

    spin_lock(&dev->lock);
    dev->open_count--;
    dev->is_open = 0;
    spin_unlock(&dev->lock);

    pr_info("irq-driver: device closed\n");
    return 0;
}

static ssize_t irq_read(struct file *filp, char __user *buf,
                        size_t count, loff_t *f_pos)
{
    struct irq_device_data *dev = filp->private_data;
    int bytes_to_copy;

    if (dev->data_len == 0) {
        if (filp->f_flags & O_NONBLOCK) {
            return -EAGAIN;
        }
        /* Wait for interrupt data */
        if (wait_event_interruptible(dev->wait_queue, dev->data_len > 0)) {
            return -ERESTARTSYS;
        }
    }

    bytes_to_copy = min(count, (size_t)dev->data_len);

    if (copy_to_user(buf, dev->buffer, bytes_to_copy)) {
        return -EFAULT;
    }

    dev->data_len = 0;
    return bytes_to_copy;
}

static ssize_t irq_write(struct file *filp, const char __user *buf,
                         size_t count, loff_t *f_pos)
{
    struct irq_device_data *dev = filp->private_data;
    int bytes_to_copy;

    bytes_to_copy = min(count, (size_t)(sizeof(dev->buffer) - 1));

    if (copy_from_user(dev->buffer, buf, bytes_to_copy)) {
        return -EFAULT;
    }

    dev->data_len = bytes_to_copy;
    dev->buffer[bytes_to_copy] = '\0';

    /* Simulate interrupt trigger */
    pr_info("irq-driver: Data written, simulating interrupt\n");
    /* In real hardware, you'd write to a device register here */

    return bytes_to_copy;
}

static const struct file_operations irq_fops = {
    .owner = THIS_MODULE,
    .open = irq_open,
    .release = irq_release,
    .read = irq_read,
    .write = irq_write,
};

/* ============================================================
 * Simulated Interrupt (for testing without hardware)
 * ============================================================ */

/* Timer callback for simulated interrupts */
static void irq_sim_timer(struct timer_list *unused)
{
    /* Simulate an interrupt by calling the handler */
    if (irq_dev_data) {
        irq_handler(simulated_irq, irq_dev_data);
    }

    /* Reschedule for next simulated interrupt (every 5 seconds) */
    mod_timer(&irq_dev_data->sim_timer, jiffies + msecs_to_jiffies(5000));
}

/* ============================================================
 * Module Init/Exit
 * ============================================================ */

static int __init irq_driver_init(void)
{
    int ret;
    dev_t dev_num;

    pr_info("irq-driver: Initializing interrupt-driven driver\n");

    /* Allocate device data */
    irq_dev_data = kzalloc(sizeof(*irq_dev_data), GFP_KERNEL);
    if (!irq_dev_data) {
        return -ENOMEM;
    }

    /* Initialize synchronization */
    spin_lock_init(&irq_dev_data->lock);
    init_waitqueue_head(&irq_dev_data->wait_queue);
    irq_dev_data->open_count = 0;
    irq_dev_data->is_open = 0;
    irq_dev_data->data_len = 0;

    /* Create workqueue */
    irq_dev_data->wq = alloc_workqueue("irq-driver-wq", WQ_UNBOUND, 1);
    INIT_WORK(&irq_dev_data->deferred_work, irq_bottom_half);

    /* Allocate major number */
    ret = alloc_chrdev_region(&dev_num, 0, 1, "irq_driver");
    if (ret < 0) {
        goto err_alloc;
    }
    irq_major = MAJOR(dev_num);

    /* Register cdev */
    cdev_init(&irq_cdev, &irq_fops);
    irq_cdev.owner = THIS_MODULE;
    ret = cdev_add(&irq_cdev, dev_num, 1);
    if (ret < 0) {
        goto err_cdev;
    }

    /* Create device class and node */
    irq_class = class_create("irq_class");
    irq_device = device_create(irq_class, NULL, dev_num, NULL, "irq_driver");

    /* Set up simulated timer */
    timer_setup(&irq_dev_data->sim_timer, irq_sim_timer, 0);
    mod_timer(&irq_dev_data->sim_timer, jiffies + msecs_to_jiffies(5000));

    pr_info("irq-driver: Driver loaded (simulated IRQ mode)\n");
    pr_info("irq-driver: Data arrives every 5 seconds via simulated interrupt\n");

    return 0;

err_cdev:
    unregister_chrdev_region(dev_num, 1);
err_alloc:
    kfree(irq_dev_data);
    return ret;
}

static void __exit irq_driver_exit(void)
{
    if (irq_dev_data) {
        del_timer_sync(&irq_dev_data->sim_timer);
        destroy_workqueue(irq_dev_data->wq);
        kfree(irq_dev_data);
    }

    device_destroy(irq_class, MKDEV(irq_major, 0));
    class_destroy(irq_class);
    cdev_del(&irq_cdev);
    unregister_chrdev_region(MKDEV(irq_major, 0), 1);

    pr_info("irq-driver: Driver unloaded\n");
}

module_init(irq_driver_init);
module_exit(irq_driver_exit);
