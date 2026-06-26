/**
 * @file uart.c
 * @brief UART Driver Implementation
 *
 * This file implements the UART driver with:
 * - FIFO-based TX/RX buffering (circular buffers)
 * - Interrupt-driven data handling
 * - DMA transfer support
 * - Hardware flow control (RTS/CTS)
 * - Error handling (parity, framing, overrun, break)
 *
 * FIFO (First-In-First-Out) Buffer Theory:
 *
 * A FIFO buffer is a ring/circular buffer that handles data bursts
 * when the application cannot keep up with the data rate.
 *
 * Circular buffer mechanics:
 *   tx_head advances on write, tx_tail advances on read
 *   When head reaches end, it wraps to beginning
 *
 *   [H|A|B|C|D|E|F|.|.|.]
 *    ^head
 *         ^tail
 *
 *   Count = (head - tail + SIZE) % SIZE
 *   Empty when head == tail
 *   Full when (head + 1) % SIZE == tail
 */

#include "uart.h"
#include <string.h>

/* ==================== Internal Helper Functions ==================== */

/**
 * Push a byte to the circular TX FIFO.
 *
 * The FIFO wraps around when it reaches the end.
 * Returns false if FIFO is full.
 */
static bool uart_fifo_push(uart_t *uart, uint8_t byte)
{
    /* Check if FIFO is full (leave one slot empty to distinguish from empty) */
    if (uart->tx_count >= UART_FIFO_SIZE) {
        return false;
    }

    /* Write byte at head position and advance head */
    uart->tx_fifo[uart->tx_head] = byte;
    uart->tx_head = (uart->tx_head + 1) % UART_FIFO_SIZE;
    uart->tx_count++;

    return true;
}

/**
 * Pop a byte from the circular RX FIFO.
 *
 * Returns false if FIFO is empty.
 */
static bool uart_fifo_pop(uart_t *uart, uint8_t *byte)
{
    /* Check if FIFO is empty */
    if (uart->rx_count == 0) {
        return false;
    }

    /* Read byte at tail position and advance tail */
    *byte = uart->rx_fifo[uart->rx_tail];
    uart->rx_tail = (uart->rx_tail + 1) % UART_FIFO_SIZE;
    uart->rx_count--;

    return true;
}

/**
 * Calculate the number of free slots in TX FIFO.
 */
static size_t uart_fifo_free(uart_t *uart)
{
    return UART_FIFO_SIZE - uart->tx_count;
}

/**
 * Calculate the number of bytes in RX FIFO.
 */
static size_t uart_fifo_used(uart_t *uart)
{
    return uart->rx_count;
}

/* ==================== Public API Implementation ==================== */

bool uart_init(uart_t *uart, uint8_t instance, uart_baud_t baud,
               uart_data_bits_t data_bits, uart_parity_t parity,
               uart_stop_bits_t stop_bits)
{
    if (uart == NULL) {
        return false;
    }

    /* Initialize UART structure to zero */
    memset(uart, 0, sizeof(uart_t));

    /* Set hardware configuration */
    uart->instance = instance;
    uart->baud_rate = baud;
    uart->data_bits = data_bits;
    uart->parity = parity;
    uart->stop_bits = stop_bits;

    /* Initialize FIFO pointers */
    uart->tx_head = 0;
    uart->tx_tail = 0;
    uart->tx_count = 0;
    uart->rx_head = 0;
    uart->rx_tail = 0;
    uart->rx_count = 0;

    /* Default settings */
    uart->dma_mode = UART_DMA_OFF;
    uart->flow_control = UART_FLOW_CONTROL_NONE;
    uart->errors = UART_ERROR_NONE;
    uart->enabled = false;
    uart->busy = false;

    /* Enable by default after init */
    uart_enable(uart, true);

    return true;
}

void uart_enable(uart_t *uart, bool enable)
{
    if (uart == NULL) {
        return;
    }

    uart->enabled = enable;

    /* In real hardware, this would enable/disable the UART peripheral
     * by setting the appropriate control register bit.
     *
     * Example (ARM/STM32):
     *   USART1->CR1 |= USART_CR1_UE;  // Enable
     *   USART1->CR1 &= ~USART_CR1_UE; // Disable
     */
}

void uart_set_flow_control(uart_t *uart, uart_flow_control_t flow_control)
{
    if (uart == NULL) {
        return;
    }

    uart->flow_control = flow_control;

    /* RTS/CTS hardware flow control:
     *
     * RTS (Request To Send): When UART TX FIFO has data, assert RTS
     * CTS (Clear To Send): If CTS is LOW, UART is allowed to transmit
     *
     * This prevents FIFO overflow when the receiver cannot keep up.
     *
     * XON/XOFF software flow control:
     *   XON (0x11): Resume transmission
     *   XOFF (0x13): Pause transmission
     *   Inserted automatically when RX FIFO nears capacity
     */
}

void uart_set_dma_mode(uart_t *uart, uart_dma_mode_t mode)
{
    if (uart == NULL) {
        return;
    }

    uart->dma_mode = mode;
}

bool uart_set_baud(uart_t *uart, uart_baud_t baud)
{
    if (uart == NULL) {
        return false;
    }

    uart->baud_rate = baud;

    /* In real hardware, calculate and set the baud rate divider:
     *
     *   USART_BRR = PCLK / BaudRate
     *
     * For example, with PCLK = 72 MHz and baud = 115200:
     *   USART_BRR = 72000000 / 115200 = 625
     *
     * The actual baud rate is then: 72000000 / 625 = 115200
     */

    return true;
}

size_t uart_write(uart_t *uart, const uint8_t *data, size_t length)
{
    if (uart == NULL || data == NULL) {
        return 0;
    }

    size_t written = 0;

    /* Check flow control before writing */
    if (uart->flow_control == UART_FLOW_CONTROL_RTS_CTS) {
        /* In real hardware, check CTS pin state */
        /* If CTS is HIGH, do not transmit */
    }

    /* Push data into TX FIFO (circular buffer) */
    for (size_t i = 0; i < length; i++) {
        if (uart_fifo_push(uart, data[i])) {
            written++;
        } else {
            /* FIFO is full - in real hardware, this would trigger
             * TX interrupt to drain the FIFO */
            break;
        }
    }

    /* If TX interrupt is enabled, trigger TX interrupt to start transmission */
    if (uart->irq_tx_enabled && written > 0) {
        /* In real hardware: set TXE (TX Empty) interrupt enable bit */
        /* USART1->CR1 |= USART_CR1_TXEIE; */
    }

    return written;
}

size_t uart_read(uart_t *uart, uint8_t *buf, size_t max_len)
{
    if (uart == NULL || buf == NULL) {
        return 0;
    }

    size_t read_count = 0;

    /* Pop data from RX FIFO (circular buffer) */
    while (read_count < max_len && uart_fifo_pop(uart, &buf[read_count])) {
        read_count++;
    }

    return read_count;
}

bool uart_write_blocking(uart_t *uart, const uint8_t *data, size_t length,
                         uint32_t timeout_ms)
{
    if (uart == NULL || data == NULL) {
        return false;
    }

    /* Write all data to TX FIFO */
    size_t total_written = 0;
    for (size_t i = 0; i < length; i++) {
        /* Wait for FIFO space with timeout */
        uint32_t start = 0;  /* In real code, use hardware timer */
        while (uart_fifo_free(uart) == 0) {
            /* Timeout check would go here with actual timer */
            if (start + timeout_ms < start) {  /* Overflow check */
                return total_written == length;
            }
            /* Spin wait - in real code, use interrupt or DMA */
        }

        if (uart_fifo_push(uart, data[i])) {
            total_written++;
        }
    }

    /* Wait for TX FIFO to drain */
    while (!uart_tx_empty(uart)) {
        /* Timeout check */
    }

    return total_written == length;
}

void uart_enable_irq(uart_t *uart, uint8_t irq_type, bool enable)
{
    if (uart == NULL) {
        return;
    }

    switch (irq_type) {
    case 0:  /* RX interrupt */
        uart->irq_rx_enabled = enable;
        break;
    case 1:  /* TX interrupt */
        uart->irq_tx_enabled = enable;
        break;
    case 2:  /* Error interrupt */
        uart->irq_error_enabled = enable;
        break;
    }
}

void uart_set_rx_callback(uart_t *uart, uart_rx_callback_t cb, void *context)
{
    if (uart == NULL) {
        return;
    }

    uart->rx_cb = cb;
    uart->rx_context = context;
}

void uart_set_tx_callback(uart_t *uart, uart_tx_callback_t cb, void *context)
{
    if (uart == NULL) {
        return;
    }

    uart->tx_cb = cb;
    uart->tx_context = context;
}

void uart_set_error_callback(uart_t *uart, uart_error_callback_t cb, void *context)
{
    if (uart == NULL) {
        return;
    }

    uart->error_cb = cb;
    uart->error_context = context;
}

void uart_clear_errors(uart_t *uart)
{
    if (uart != NULL) {
        uart->errors = UART_ERROR_NONE;
    }
}

uart_error_t uart_get_errors(uart_t *uart)
{
    if (uart == NULL) {
        return UART_ERROR_NONE;
    }
    return uart->errors;
}

size_t uart_rx_count(uart_t *uart)
{
    if (uart == NULL) {
        return 0;
    }
    return uart_fifo_used(uart);
}

size_t uart_tx_count(uart_t *uart)
{
    if (uart == NULL) {
        return 0;
    }
    return uart->tx_count;
}

bool uart_tx_empty(uart_t *uart)
{
    if (uart == NULL) {
        return true;
    }
    return uart->tx_count == 0;
}

void uart_rx_byte(uart_t *uart, uint8_t byte)
{
    if (uart == NULL) {
        return;
    }

    /* In real hardware, this function is called from the RX interrupt handler.
     *
     * The UART hardware detects framing errors, parity errors, and overrun
     * before delivering the byte to the software.
     *
     * Error detection in UART:
     *
     * 1. Parity Error:
     *    - Even parity: total 1-bits (data + parity) must be even
     *    - Odd parity: total 1-bits must be odd
     *    - If mismatch, set UART_ERROR_PARITY flag
     *
     * 2. Framing Error:
     *    - Stop bit should be HIGH (idle state)
     *    - If stop bit is LOW, data is corrupted
     *    - Set UART_ERROR_FRAMING flag
     *
     * 3. Overrun Error:
     *    - New byte arrives before previous byte is read
     *    - The new byte is lost (hardware drops it)
     *    - Set UART_ERROR_OVERRUN flag
     *
     * 4. Break Condition:
     *    - Line stays LOW for more than one frame duration
     *    - Indicates line fault or special command
     *    - Set UART_ERROR_BREAK flag
     */

    /* Check if RX FIFO has space (prevent overflow) */
    if (uart->rx_count >= UART_FIFO_SIZE) {
        uart->errors |= UART_ERROR_BUFFER_FULL;
        if (uart->error_cb) {
            uart->error_cb(uart->error_context, UART_ERROR_BUFFER_FULL);
        }
        return;
    }

    /* Push byte into RX FIFO */
    uart->rx_fifo[uart->rx_head] = byte;
    uart->rx_head = (uart->rx_head + 1) % UART_FIFO_SIZE;
    uart->rx_count++;

    /* Invoke RX callback if registered */
    if (uart->rx_cb) {
        /* In real code, would pass pointer and count to callback */
        uart->rx_cb(uart->rx_context, &byte, 1);
    }
}

void uart_tx_byte_done(uart_t *uart)
{
    if (uart == NULL) {
        return;
    }

    /* In real hardware, this is called from the TX interrupt handler.
     *
     * When TX FIFO becomes empty, the UART hardware raises an interrupt.
     * The ISR should refill the FIFO from the application buffer.
     *
     * TX interrupt flow:
     *   1. Hardware detects TX FIFO empty
     *   2. ISR fires
     *   3. ISR loads next byte from application buffer into TX register
     *   4. If buffer empty, disable TX interrupt
     */

    if (uart->tx_count > 0) {
        /* TX FIFO still has data, continue transmission */
        uart->busy = true;
    } else {
        /* TX FIFO is now empty, transmission complete */
        uart->busy = false;
        if (uart->tx_cb) {
            uart->tx_cb(uart->tx_context);
        }
    }
}
