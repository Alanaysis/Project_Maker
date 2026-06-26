/*
 * Platform Driver with Device Tree - Example 3
 *
 * Demonstrates the Linux platform driver model with device tree integration:
 *   - Platform driver registration
 *   - Device tree parsing (compatible strings, properties, interrupts)
 *   - Resource management (memory regions, IRQs)
 *   - Probe/remove lifecycle
 *   - Device-probe binding mechanism
 *
 * The platform driver model is the standard for on-SoC devices.
 * It separates driver code from hardware description (device tree).
 */

#include <linux/init.h>
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/of.h>
#include <linux/of_irq.h>
#include <linux/of_address.h>
#include <linux/io.h>
#include <linux/slab.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/uaccess.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Device Driver Framework");
MODULE_DESCRIPTION("Platform Driver with Device Tree Example");

/* ============================================================
 * Driver State
 * ============================================================ */

struct platform_driver_data {
    struct platform_device *pdev;
    struct cdev cdev;
    struct class *class;
    struct device *dev;
    dev_t dev_id;

    /* Memory-mapped I/O */
    void __iomem *mmio_base;
    resource_size_t mmio_size;

    /* Device tree data */
    int irq_line;
    u32 custom_property;

    /* Data buffer */
    char *buffer;
    size_t buffer_len;
};

static struct platform_driver_data *pdata;

/* ============================================================
 * Device Tree Parsing
 * ============================================================ */

/*
 * Device tree parsing demonstrates how Linux drivers discover hardware:
 *   1. Device tree describes hardware layout
 *   2. Driver specifies compatible strings to match
 *   3. OF (Open Firmware) API reads properties
 *
 * Example device tree node:
 *   my_device {
 *       compatible = "example,platform-driver";
 *       reg = <0x12340000 0x1000>;  /* base address, size */
 *       interrupts = <0 42 4>;        /* IRQ spec */
 *       custom-property = <0x1234>;
 *   };
 */
static int platform_parse_dt(struct platform_driver_data *data, struct platform_device *pdev)
{
    struct device_node *np = pdev->dev.of_node;
    const __be32 *prop;
    int ret;

    if (!np) {
        pr_warn("platform-driver: No device tree node\n");
        return -EINVAL;
    }

    /* Check compatible string match */
    if (!of_device_is_compatible(np, "example,platform-driver")) {
        pr_warn("platform-driver: Compatible string mismatch\n");
        return -ENODEV;
    }

    /* Parse 'reg' property for memory-mapped I/O */
    ret = of_address_to_resource(np, 0, &data->mmio_size);
    if (ret) {
        pr_warn("platform-driver: No memory resource\n");
        data->mmio_base = NULL;
    } else {
        pr_info("platform-driver: MMIO region: size=%zu\n", data->mmio_size);
    }

    /* Get IRQ number from device tree */
    data->irq_line = of_irq_get(np, 0);
    if (data->irq_line > 0) {
        pr_info("platform-driver: IRQ from DT: %d\n", data->irq_line);
    }

    /* Read custom property */
    prop = of_get_property(np, "custom-property", &ret);
    if (prop) {
        data->custom_property = be32_to_cpu(*prop);
        pr_info("platform-driver: Custom property: 0x%x\n", data->custom_property);
    }

    return 0;
}

/* ============================================================
 * Platform Probe/Remove
 * ============================================================ */

static int platform_driver_probe(struct platform_device *pdev)
{
    int ret;
    struct resource *res;

    pr_info("platform-driver: Probing device\n");

    /* Allocate driver data */
    pdata = kzalloc(sizeof(*pdata), GFP_KERNEL);
    if (!pdata) {
        return -ENOMEM;
    }

    pdata->pdev = pdev;
    pdata->buffer_len = 256;
    pdata->buffer = kmalloc(pdata->buffer_len, GFP_KERNEL);

    /* Parse device tree for hardware configuration */
    ret = platform_parse_dt(pdata, pdev);
    if (ret) {
        pr_warn("platform-driver: DT parsing failed, using defaults\n");
    }

    /* Request memory region */
    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    if (res) {
        /* Map physical memory to kernel virtual address */
        pdata->mmio_base = ioremap(res->start, resource_size(res));
        if (pdata->mmio_base) {
            /* Write to MMIO register (example: clear a register) */
            iowrite32(0, pdata->mmio_base);
            pr_info("platform-driver: MMIO mapped at %p\n", pdata->mmio_base);
        }
    }

    /* Allocate major number and register character device */
    ret = alloc_chrdev_region(&pdata->dev_id, 0, 1, "platform_driver");
    if (ret < 0) {
        goto err_chrdev;
    }

    cdev_init(&pdata->cdev, &platform_fops);  /* Defined below */
    pdata->cdev.owner = THIS_MODULE;
    ret = cdev_add(&pdata->cdev, pdata->dev_id, 1);
    if (ret < 0) {
        goto err_cdev;
    }

    pdata->class = class_create("platform_class");
    pdata->dev = device_create(pdata->class, &pdev->dev, pdata->dev_id,
                                pdata, "platform_driver");

    pr_info("platform-driver: Probe completed\n");
    return 0;

err_cdev:
    unregister_chrdev_region(pdata->dev_id, 1);
err_chrdev:
    if (pdata->mmio_base) {
        iounmap(pdata->mmio_base);
    }
    kfree(pdata->buffer);
    kfree(pdata);
    return ret;
}

static int platform_driver_remove(struct platform_device *pdev)
{
    pr_info("platform-driver: Removing device\n");

    device_destroy(pdata->class, pdata->dev_id);
    class_destroy(pdata->class);
    cdev_del(&pdata->cdev);
    unregister_chrdev_region(pdata->dev_id, 1);

    if (pdata->mmio_base) {
        iounmap(pdata->mmio_base);
    }
    kfree(pdata->buffer);
    kfree(pdata);

    pr_info("platform-driver: Remove completed\n");
    return 0;
}

/* ============================================================
 * Platform Driver Registration
 * ============================================================ */

static const struct of_device_id platform_of_match[] = {
    { .compatible = "example,platform-driver" },
    { /* sentinel */ }
};
MODULE_DEVICE_TABLE(of, platform_of_match);

static struct platform_driver platform_example_driver = {
    .probe = platform_driver_probe,
    .remove = platform_driver_remove,
    .driver = {
        .name = "example-platform-driver",
        .of_match_table = platform_of_match,
    },
};

/* ============================================================
 * File Operations (simplified for this example)
 * ============================================================ */

/* Forward declaration */
static const struct file_operations platform_fops;

static int __init platform_example_init(void)
{
    pr_info("platform-driver: Loading platform driver example\n");
    pr_info("platform-driver: Requires device tree node with compatible='example,platform-driver'\n");

    return platform_driver_register(&platform_example_driver);
}

static void __exit platform_example_exit(void)
{
    platform_driver_unregister(&platform_example_driver);
    pr_info("platform-driver: Unloaded\n");
}

module_init(platform_example_init);
module_exit(platform_example_exit);

MODULE_LICENSE("GPL");
