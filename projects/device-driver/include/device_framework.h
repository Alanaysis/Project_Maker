/*
 * device-driver-framework - Header File
 *
 * Public API and data structures for the Linux device driver framework.
 * This header defines the interfaces between the kernel module and user-space programs.
 */

#ifndef DEVICE_FRAMEWORK_H
#define DEVICE_FRAMEWORK_H

#include <linux/types.h>

/* ============================================================
 * Configuration Constants
 * ============================================================ */

#define DEVICE_FRAMEWORK_MAJOR        0    /* 0 = dynamic allocation */
#define DEVICE_FRAMEWORK_MINOR        0
#define DEVICE_FRAMEWORK_NUM_DEVICES  1
#define DEVICE_FRAMEWORK_BUFFER_SIZE  4096
#define DEVICE_FRAMEWORK_MAX_BUFFER   (1024 * 1024)  /* 1MB max */
#define DEVICE_FRAMEWORK_DEVICE_NAME  "device_framework"
#define DEVICE_FRAMEWORK_CLASS_NAME   "device_framework_class"

/* ============================================================
 * IOCTL Command Definitions
 * ============================================================ */

/* Magic number for IOCTL commands (chosen arbitrarily, check /usr/include/linux/ioctl.h) */
#define DFW_IOC_MAGIC 'k'

/* IOCTL commands: _IO, _IOR, _IOW, _IOWR macros from <linux/ioctl.h> */
#define DFW_CMD_GET_STATUS    _IOR(DFW_IOC_MAGIC, 0, struct dfw_status)
#define DFW_CMD_SET_BUFFER_SIZE  _IOW(DFW_IOC_MAGIC, 1, unsigned long)
#define DFW_CMD_RESET_DEVICE  _IO(DFW_IOC_MAGIC, 2)
#define DFW_CMD_GET_BUFFER_INFO _IOR(DFW_IOC_MAGIC, 3, struct dfw_buffer_info)

/* ============================================================
 * Data Structures for User-Space Communication
 * ============================================================ */

/* Device status - returned via IOCTL */
struct dfw_status {
    int open_count;        /* Number of times device has been opened */
    size_t data_len;       /* Current data length in buffer */
    size_t buffer_size;    /* Total buffer size */
    int irq_number;        /* IRQ number (if configured) */
    int is_open;           /* Whether device is currently open */
    int initialized;       /* Whether device is initialized */
};

/* Buffer information - returned via IOCTL */
struct dfw_buffer_info {
    size_t size;   /* Total buffer size */
    size_t used;   /* Bytes currently used */
    size_t free;   /* Bytes remaining */
};

/* ============================================================
 * Kernel Module API (for internal use)
 * ============================================================ */

/* Request and free IRQ */
int dfw_request_irq(void *dev, int irq_num);
void dfw_free_irq(void *dev);

/* DMA buffer management */
void *dfw_dma_alloc(size_t size, dma_addr_t *handle);
void dfw_dma_free(void *vaddr, dma_addr_t handle, size_t size);

/* ============================================================
 * User-Space Constants
 * ============================================================ */

#define DFW_DEVICE_PATH "/dev/device_framework"

#endif /* DEVICE_FRAMEWORK_H */
