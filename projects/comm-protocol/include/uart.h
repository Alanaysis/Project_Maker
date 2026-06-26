/**
 * @file uart.h
 * @brief UART (Universal Asynchronous Receiver-Transmitter) Driver
 *
 * UART is a serial communication protocol that transmits data one bit at a time
 * asynchronously (without a shared clock signal). Key concepts:
 *
 * - Baud Rate: Symbol rate (bits per second). Common values: 9600, 115200
 * - Frame Format: Start bit (always 0) + data bits (5-9) + optional parity + stop bits (1, 1.5, 2)
 * - FIFO: First-In-First-Out buffer to handle bursts of data
 * - Interrupt-driven: Events trigger ISR (Interrupt Service Routine) for efficient CPU usage
 *
 * Protocol Theory:
 *   Idle line = HIGH (mark state, logical 1)
 *   Start bit  = LOW  (transition to space state, logical 0) - signals start of frame
 *   Data bits  = LSB first (bit 0 transmitted first)
 *   Parity     = Even or odd check bit for error detection
 *   Stop bit   = HIGH (returns line to idle state)
 *
 * Timing diagram:
 *   Line:  _____|‾‾‾‾|DDDD|CC|BBBB|AAAA|______|‾‾‾‾|EEEE|FF|GGGG|HHHH|______
 *          Idle  Start  P  D3  D2   D1   Idle  Start  D3  D2  D1   D0   Idle
 *
 * Where D0-D7 = data bits (LSB first), P = parity bit
 */

#ifndef UART_H
#define UART_H

#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>

/* ==================== Configuration ==================== */

/** Maximum FIFO depth for UART TX and RX buffers */
#define UART_FIFO_SIZE 256

/** Maximum UART instances */
#define UART_MAX_INSTANCES 4

/** Default baud rate */
#define UART_DEFAULT_BAUD 115200

/** UART timeout in milliseconds for blocking operations */
#define UART_TIMEOUT_MS 1000

/* ==================== Baud Rate Configuration ==================== */

/** Supported baud rates for UART communication */
typedef enum {
    UART_BAUD_9600    = 9600,
    UART_BAUD_19200   = 19200,
    UART_BAUD_38400   = 38400,
    UART_BAUD_57600   = 57600,
    UART_BAUD_115200  = 115200,
    UART_BAUD_230400  = 230400,
    UART_BAUD_460800  = 460800,
    UART_BAUD_921600  = 921600
} uart_baud_t;

/* ==================== Frame Format ==================== */

/** Number of data bits in a UART frame */
typedef enum {
    UART_DATA_BITS_5 = 5,  /**< 5 data bits (rare, used with teleprinters) */
    UART_DATA_BITS_6 = 6,  /**< 6 data bits (ASCII extended) */
    UART_DATA_BITS_7 = 7,  /**< 7 data bits (standard ASCII) */
    UART_DATA_BITS_8 = 8   /**< 8 data bits (most common, binary data) */
} uart_data_bits_t;

/** Parity mode for error detection in UART frames */
typedef enum {
    UART_PARITY_NONE = 0,  /**< No parity bit (most common in modern systems) */
    UART_PARITY_EVEN,      /**< Parity bit makes total 1-bits even */
    UART_PARITY_ODD        /**< Parity bit makes total 1-bits odd */
} uart_parity_t;

/** Number of stop bits (marks end of frame, returns line to idle) */
typedef enum {
    UART_STOP_BITS_1  = 1,  /**< 1 stop bit (most common, fastest) */
    UART_STOP_BITS_15 = 2,  /**< 1.5 stop bits (obsolete, teleprinters) */
    UART_STOP_BITS_2  = 2   /**< 2 stop bits (reliable, noisy environments) */
} uart_stop_bits_t;

/* ==================== Error Types ==================== */

/** UART error flags for detecting communication issues */
typedef enum {
    UART_ERROR_NONE       = 0,   /**< No error */
    UART_ERROR_PARITY     = 1 << 0,  /**< Parity error: received parity doesn't match */
    UART_ERROR_FRAMING    = 1 << 1,  /**< Framing error: stop bit not HIGH */
    UART_ERROR_OVERRUN    = 1 << 2,  /**< Overrun: new data before previous read */
    UART_ERROR_BREAK      = 1 << 3,  /**< Break condition: line low for > 1 frame */
    UART_ERROR_BUFFER_FULL = 1 << 4, /**< RX FIFO overflow */
    UART_ERROR_TIMEOUT    = 1 << 5   /**< Operation timed out */
} uart_error_t;

/* ==================== Flow Control ==================== */

/** Hardware flow control modes for managing data flow between devices */
typedef enum {
    UART_FLOW_CONTROL_NONE  = 0,  /**< No flow control (simplest, may lose data) */
    UART_FLOW_CONTROL_RTS_CTS = 1,  /**< Request To Send / Clear To Send (hardware) */
    UART_FLOW_CONTROL_XON_XOFF = 2  /**< Software flow control characters (XON=17, XOFF=19) */
} uart_flow_control_t;

/* ==================== Callback Types ==================== */

/** RX complete callback function type */
typedef void (*uart_rx_callback_t)(void *context, const uint8_t *data, size_t length);

/** TX complete callback function type */
typedef void (*uart_tx_callback_t)(void *context);

/** Error callback function type */
typedef void (*uart_error_callback_t)(void *context, uart_error_t error);

/* ==================== DMA Transfer ==================== */

/** DMA transfer mode for high-speed UART data movement */
typedef enum {
    UART_DMA_OFF    = 0,  /**< No DMA, use polling/interrupts */
    UART_DMA_TX_ONLY,     /**< DMA for TX, interrupts for RX */
    UART_DMA_RX_ONLY,     /**< Interrupts for TX, DMA for RX */
    UART_DMA_FULL         /**< DMA for both TX and RX (highest throughput) */
} uart_dma_mode_t;

/** DMA descriptor for UART transfers */
typedef struct {
    uint8_t *buffer;      /**< Data buffer for DMA transfer */
    size_t   length;      /**< Number of bytes to transfer via DMA */
    size_t   transferred; /**< Bytes actually transferred */
    bool     circular;    /**< Circular buffer mode for continuous streaming */
} uart_dma_desc_t;

/* ==================== UART Instance State ==================== */

/** Complete UART driver state structure */
typedef struct {
    /* Hardware configuration */
    uint8_t   instance;           /**< UART instance number (0, 1, 2...) */
    uint32_t  base_addr;          /**< Memory-mapped I/O base address */
    uart_baud_t baud_rate;        /**< Communication speed */
    uart_data_bits_t data_bits;   /**< Frame data width */
    uart_parity_t parity;         /**< Parity checking mode */
    uart_stop_bits_t stop_bits;   /**< Stop bits count */
    uart_flow_control_t flow_control; /**< Hardware/software flow control */

    /* FIFO buffers - circular buffers for TX/RX data */
    uint8_t  tx_fifo[UART_FIFO_SIZE];  /**< TX FIFO ring buffer */
    uint8_t  rx_fifo[UART_FIFO_SIZE];  /**< RX FIFO ring buffer */
    size_t   tx_head;         /**< TX write pointer (next to write) */
    size_t   tx_tail;         /**< TX read pointer (next to read) */
    size_t   tx_count;        /**< Current bytes in TX FIFO */
    size_t   rx_head;         /**< RX write pointer (next to write) */
    size_t   rx_tail;         /**< RX read pointer (next to read) */
    size_t   rx_count;        /**< Current bytes in RX FIFO */

    /* DMA configuration */
    uart_dma_mode_t dma_mode; /**< DMA transfer mode */
    uart_dma_desc_t dma_tx;   /**< TX DMA descriptor */
    uart_dma_desc_t dma_rx;   /**< RX DMA descriptor */

    /* Interrupt configuration */
    bool irq_rx_enabled;      /**< RX interrupt enabled flag */
    bool irq_tx_enabled;      /**< TX interrupt enabled flag */
    bool irq_error_enabled;   /**< Error interrupt enabled flag */

    /* Callbacks for event-driven programming */
    void *rx_context;         /**< User context for RX callback */
    uart_rx_callback_t rx_cb; /**< Called when RX data available */
    void *tx_context;         /**< User context for TX callback */
    uart_tx_callback_t tx_cb; /**< Called when TX complete */
    void *error_context;      /**< User context for error callback */
    uart_error_callback_t error_cb; /**< Called on error */

    /* Status and error tracking */
    uart_error_t errors;      /**< Accumulated error flags */
    bool enabled;             /**< UART peripheral enabled */
    bool busy;                /**< TX busy flag (for flow control) */
} uart_t;

/* ==================== Public API ==================== */

/**
 * Initialize a UART instance with specified configuration.
 *
 * Sets up frame format, baud rate, and enables the peripheral.
 * This is the first function to call before any UART operation.
 *
 * @param uart    Pointer to UART structure to initialize
 * @param instance UART instance number
 * @param baud     Desired baud rate
 * @param data_bits Number of data bits per frame
 * @param parity   Parity mode
 * @param stop_bits Number of stop bits
 * @return true on success, false on failure
 */
bool uart_init(uart_t *uart, uint8_t instance, uart_baud_t baud,
               uart_data_bits_t data_bits, uart_parity_t parity,
               uart_stop_bits_t stop_bits);

/**
 * Enable or disable the UART peripheral.
 *
 * @param uart    Pointer to UART instance
 * @param enable  true to enable, false to disable
 */
void uart_enable(uart_t *uart, bool enable);

/**
 * Configure hardware flow control (RTS/CTS).
 *
 * RTS (Request To Send): UART asserts this line when it has data to send
 * CTS (Clear To Send): Remote device asserts this to indicate it can receive
 *
 * @param uart    Pointer to UART instance
 * @param flow_control Flow control mode
 */
void uart_set_flow_control(uart_t *uart, uart_flow_control_t flow_control);

/**
 * Configure DMA transfer mode for high-throughput operations.
 *
 * DMA (Direct Memory Access) transfers data without CPU intervention,
 * freeing the CPU for other tasks during communication.
 *
 * @param uart    Pointer to UART instance
 * @param mode    DMA mode (off, TX only, RX only, full)
 */
void uart_set_dma_mode(uart_t *uart, uart_dma_mode_t mode);

/**
 * Set the baud rate for UART communication.
 *
 * Baud rate determines how fast bits are transmitted. Both sides
 * must agree on the baud rate (with some tolerance, typically ±2%).
 *
 * @param uart    Pointer to UART instance
 * @param baud    Desired baud rate
 * @return true on success
 */
bool uart_set_baud(uart_t *uart, uart_baud_t baud);

/**
 * Write data to UART TX FIFO.
 *
 * For interrupt-driven operation, call uart_enable_irq() after this.
 * For DMA operation, configure DMA descriptor and start DMA transfer.
 *
 * @param uart    Pointer to UART instance
 * @param data    Data buffer to transmit
 * @param length  Number of bytes to transmit
 * @return Number of bytes actually enqueued to TX FIFO
 */
size_t uart_write(uart_t *uart, const uint8_t *data, size_t length);

/**
 * Read data from UART RX FIFO.
 *
 * In interrupt-driven mode, this is called from the RX callback
 * or polled in the main loop.
 *
 * @param uart    Pointer to UART instance
 * @param buf     Buffer to receive data into
 * @param max_len Maximum bytes to read
 * @return Number of bytes actually read from RX FIFO
 */
size_t uart_read(uart_t *uart, uint8_t *buf, size_t max_len);

/**
 * Blocking write with timeout.
 *
 * Waits until all data is transmitted or timeout expires.
 * Useful for simple synchronous communication patterns.
 *
 * @param uart    Pointer to UART instance
 * @param data    Data to transmit
 * @param length  Number of bytes
 * @param timeout_ms Timeout in milliseconds
 * @return true if all data transmitted before timeout
 */
bool uart_write_blocking(uart_t *uart, const uint8_t *data, size_t length,
                         uint32_t timeout_ms);

/**
 * Enable or disable UART interrupts.
 *
 * Interrupts allow the UART to notify the CPU of events
 * (RX data ready, TX empty, errors) without polling.
 *
 * @param uart    Pointer to UART instance
 * @param irq_type Which interrupt to control
 * @param enable  true to enable, false to disable
 */
void uart_enable_irq(uart_t *uart, uint8_t irq_type, bool enable);

/**
 * Register a callback for RX events.
 *
 * Callback is invoked when RX data is available or RX complete.
 * Use context pointer to pass user data to the callback.
 *
 * @param uart    Pointer to UART instance
 * @param cb      Callback function
 * @param context User context pointer
 */
void uart_set_rx_callback(uart_t *uart, uart_rx_callback_t cb, void *context);

/**
 * Register a callback for TX events.
 *
 * Callback is invoked when TX FIFO is empty or DMA TX complete.
 *
 * @param uart    Pointer to UART instance
 * @param cb      Callback function
 * @param context User context pointer
 */
void uart_set_tx_callback(uart_t *uart, uart_tx_callback_t cb, void *context);

/**
 * Register a callback for error events.
 *
 * Callback is invoked on parity, framing, overrun, or break errors.
 *
 * @param uart    Pointer to UART instance
 * @param cb      Callback function
 * @param context User context pointer
 */
void uart_set_error_callback(uart_t *uart, uart_error_callback_t cb, void *context);

/**
 * Clear accumulated error flags.
 *
 * Call after handling errors to reset the error state.
 *
 * @param uart    Pointer to UART instance
 */
void uart_clear_errors(uart_t *uart);

/**
 * Get accumulated error flags.
 *
 * @param uart    Pointer to UART instance
 * @return Error flag bitmap (uart_error_t)
 */
uart_error_t uart_get_errors(uart_t *uart);

/**
 * Get current RX FIFO byte count.
 *
 * @param uart    Pointer to UART instance
 * @return Number of bytes available in RX FIFO
 */
size_t uart_rx_count(uart_t *uart);

/**
 * Get current TX FIFO byte count.
 *
 * @param uart    Pointer to UART instance
 * @return Number of bytes pending in TX FIFO
 */
size_t uart_tx_count(uart_t *uart);

/**
 * Check if TX FIFO is empty.
 *
 * @param uart    Pointer to UART instance
 * @return true if TX FIFO is empty
 */
bool uart_tx_empty(uart_t *uart);

/**
 * Simulate receiving a byte (for testing/demo purposes).
 *
 * In real hardware, this would be called from the RX interrupt handler.
 *
 * @param uart    Pointer to UART instance
 * @param byte    Received byte
 */
void uart_rx_byte(uart_t *uart, uint8_t byte);

/**
 * Simulate TX byte transmission (for testing/demo purposes).
 *
 * In real hardware, this would be called from the TX interrupt handler.
 *
 * @param uart    Pointer to UART instance
 */
void uart_tx_byte_done(uart_t *uart);

#endif /* UART_H */
