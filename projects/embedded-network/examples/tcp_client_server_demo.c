/*
 * tcp_client_server_demo.c - TCP Client/Server Demo
 *
 * Demonstrates TCP connection establishment and data transfer.
 *
 * TCP Three-Way Handshake (TCP 三次握手):
 *   Client                          Server
 *   ------                          ------
 *   [SYN, seq=100] -------------->  LISTEN --> SYN-RECEIVED
 *                          <------  [SYN-ACK, seq=300, ack=101]
 *   [ACK, seq=101, ack=301] ------> ESTABLISHED <-- ESTABLISHED
 *
 *   Now both sides can send data!
 *
 * TCP Connection Termination (TCP 连接终止):
 *   Party A                     Party B
 *   ---------                 ---------
 *   [FIN, seq=1000] -------->
 *                              <------ [ACK, seq=301, ack=1001]
 *   (FIN-WAIT-1)              (CLOSE-WAIT)
 *                              [FIN, seq=301, ack=1001] --->
 *   [ACK, seq=1001, ack=302]->  (TIME-WAIT)
 *
 *   Connection is fully closed after 2*MSL in TIME-WAIT.
 *
 * Learning objectives:
 *   - Understand TCP connection lifecycle
 *   - See SYN/SYN-ACK/ACK handshake
 *   - Understand FIN/ACK teardown
 *   - Learn about sequence numbers and acknowledgments
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Demo configuration */
#define SERVER_PORT 8080
#define CLIENT_PORT 0  /* Ephemeral port */
#define SERVER_IP   "192.168.1.1"
#define CLIENT_IP   "192.168.1.100"
#define SAMPLE_DATA "Hello from TCP Client!\n"

/* Simulated network interface */
static net_interface_t demo_iface;

/* ============================================================================
 * Initialize demo interface
 * ============================================================================ */

static void init_demo_interface(void) {
    memset(&demo_iface, 0, sizeof(demo_iface));

    demo_iface.mac.octet[0] = 0x00;
    demo_iface.mac.octet[1] = 0x1A;
    demo_iface.mac.octet[2] = 0x2B;
    demo_iface.mac.octet[3] = 0x3C;
    demo_iface.mac.octet[4] = 0x4D;
    demo_iface.mac.octet[5] = 0x5E;

    demo_iface.ip_addr = string_to_ip(CLIENT_IP);
    demo_iface.subnet_mask = string_to_ip("255.255.255.0");
    demo_iface.gateway = string_to_ip("192.168.1.1");
    demo_iface.dns_server = string_to_ip("8.8.8.8");
    demo_iface.is_up = 1;
    demo_iface.has_ip = 1;
}

/* ============================================================================
 * Demo: TCP Connection Lifecycle
 *
 * Shows the complete TCP connection lifecycle with state transitions.
 * ============================================================================ */

static void demo_tcp_connection_lifecycle(void) {
    printf("\n=== TCP Connection Lifecycle ===\n\n");

    /* Create a socket */
    int fd = socket_create(SOCK_STREAM);
    printf("1. socket(SOCK_STREAM) = fd=%d\n", fd);

    /* Initialize socket state */
    socket_t *sock = net_get_sockets();
    sock[fd - 1].local_addr.sin_addr = demo_iface.ip_addr;
    sock[fd - 1].is_bound = 1;

    /* Step 1: Connect to server */
    sock_addr_t server_addr = {
        .sin_addr = string_to_ip(SERVER_IP),
        .sin_port = htons(SERVER_PORT),
        .sin_family = 2
    };

    printf("\n--- Initiating TCP Connection ---\n");
    printf("Step 1: Client sends SYN\n");
    printf("  [SYN, seq=100] ----> Server:%d\n", SERVER_PORT);
    printf("  State: CLOSED -> SYN_SENT\n");

    printf("\nStep 2: Server responds with SYN-ACK\n");
    printf("  <---- [SYN-ACK, seq=300, ack=101]\n");
    printf("  State: SYN_SENT -> SYN_RECEIVED\n");

    printf("\nStep 3: Client sends ACK\n");
    printf("  [ACK, seq=101, ack=301] ----> Server:%d\n", SERVER_PORT);
    printf("  State: SYN_RECEIVED -> ESTABLISHED\n");

    printf("\n--- Data Transfer ---\n");
    printf("Step 4: Client sends data\n");
    printf("  [ACK, PSH, seq=101, data='%s'] ----> Server:%d\n",
           SAMPLE_DATA, SERVER_PORT);
    printf("  Bytes sent: %d\n", (int)strlen(SAMPLE_DATA));

    printf("\nStep 5: Server acknowledges\n");
    printf("  <---- [ACK, seq=301, ack=%d]\n", 101 + (int)strlen(SAMPLE_DATA));
    printf("  Server received: '%s'\n", SAMPLE_DATA);

    printf("\n--- Connection Termination ---\n");
    printf("Step 6: Client initiates close (FIN)\n");
    printf("  [FIN, ACK, seq=%d] ----> Server:%d\n",
           101 + (int)strlen(SAMPLE_DATA), SERVER_PORT);
    printf("  State: ESTABLISHED -> FIN_WAIT_1\n");

    printf("\nStep 7: Server acknowledges FIN, sends its own FIN\n");
    printf("  <---- [ACK, seq=301, ack=%d]\n", 101 + (int)strlen(SAMPLE_DATA));
    printf("  [FIN, ACK, seq=301] ----> Client\n");
    printf("  State: FIN_WAIT_1 -> FIN_WAIT_2\n");

    printf("\nStep 8: Client acknowledges server FIN\n");
    printf("  [ACK, seq=%d, ack=302] ----> Server:%d\n",
           101 + (int)strlen(SAMPLE_DATA), SERVER_PORT);
    printf("  State: FIN_WAIT_2 -> TIME_WAIT\n");

    printf("\nStep 9: Server acknowledges client's final ACK\n");
    printf("  <---- [ACK, seq=302, ack=%d]\n", 101 + (int)strlen(SAMPLE_DATA));
    printf("  State: ESTABLISHED -> CLOSED\n");

    printf("\nStep 10: Client waits 2*MSL, then closes\n");
    printf("  State: TIME_WAIT -> CLOSED\n");

    /* Clean up */
    socket_close(fd);
    printf("\nSocket closed. Connection fully terminated.\n");
}

/* ============================================================================
 * Demo: TCP Sequence Numbers
 *
 * Demonstrates how TCP sequence numbers track byte streams.
 * ============================================================================ */

static void demo_tcp_sequence_numbers(void) {
    printf("\n=== TCP Sequence Numbers ===\n\n");

    uint32_t seq = 1000;  /* Initial sequence number (ISN) */
    uint32_t ack = 2000;  /* Initial acknowledgment number */

    printf("Initial: seq=%u, ack=%u\n", seq, ack);

    /* Send some data */
    int data1_len = 100;
    printf("\nSend %d bytes: [seq=%u, seq+%d] ---->\n", data1_len, seq, data1_len);
    seq += data1_len;

    /* Receive ACK */
    printf("<---- ACK=%u (received up to byte %u)\n", ack + data1_len, ack + data1_len - 1);
    ack = ack + data1_len;

    /* Send more data */
    int data2_len = 50;
    printf("\nSend %d bytes: [seq=%u, seq+%d] ---->\n", data2_len, seq, data2_len);
    seq += data2_len;

    /* Receive ACK */
    printf("<---- ACK=%u (received up to byte %u)\n", ack + data2_len, ack + data2_len - 1);
    ack = ack + data2_len;

    /* Send FIN */
    printf("\nSend FIN: [seq=%u] (no more data)\n", seq);
    seq++;  /* FIN consumes one sequence number */

    printf("\nFinal: seq=%u, ack=%u\n", seq, ack);
}

/* ============================================================================
 * Demo: TCP Window and Flow Control
 *
 * Demonstrates TCP's flow control mechanism using the window field.
 * ============================================================================ */

static void demo_tcp_flow_control(void) {
    printf("\n=== TCP Window (Flow Control) ===\n\n");

    uint16_t window = 65535;  /* Maximum window size */
    uint32_t snd_una = 1000;  /* Unacknowledged data */

    printf("Initial window: %d bytes\n", window);
    printf("Send window: %u to %u (window size: %d)\n",
           snd_una, snd_una + window, window);

    /* Simulate receiving ACK with window update */
    uint32_t new_ack = 1100;  /* Peer acknowledged 100 bytes */
    uint16_t new_window = 32768;  /* Peer's receive window */

    printf("\nReceived ACK: ack=%u, window=%d\n", new_ack, new_window);
    snd_una = new_ack;
    window = new_window;

    printf("Send window: %u to %u (window size: %d)\n",
           snd_una, snd_una + window, window);

    /* Simulate buffer filling */
    int data_sent = 20000;
    snd_una += data_sent;
    printf("\nSent %d bytes. Window: %u to %u (remaining: %d)\n",
           data_sent, snd_una, snd_una + window, window - data_sent);

    printf("\nWhen window reaches 0, sender must pause!\n");
    printf("This prevents overwhelming the receiver's buffer.\n");
}

/* ============================================================================
 * Main demo driver
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  TCP Client/Server Demo - embedded-network\n");
    printf("========================================\n");

    init_demo_interface();
    net_stack_init(&demo_iface);

    printf("\nLocal Interface:\n");
    debug_print_mac("MAC Address", &demo_iface.mac);
    printf("IP Address:    %s\n", ip_to_string(demo_iface.ip_addr));

    /* Run demos */
    demo_tcp_connection_lifecycle();
    demo_tcp_sequence_numbers();
    demo_tcp_flow_control();

    printf("\n========================================\n");
    printf("  Demo Complete!\n");
    printf("========================================\n");

    return 0;
}
