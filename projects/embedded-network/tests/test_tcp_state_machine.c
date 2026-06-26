/*
 * test_tcp_state_machine.c - Unit tests for TCP state machine
 *
 * Tests the TCP connection state machine implementation.
 *
 * The TCP state machine is the heart of TCP reliability. Every state
 * transition is carefully defined to handle network unreliability.
 *
 * TCP States:
 *   CLOSED, LISTEN, SYN_SENT, SYN_RECEIVED, ESTABLISHED,
 *   FIN_WAIT_1, FIN_WAIT_2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT
 *
 * Test scenarios:
 *   1. Three-way handshake (SYN -> SYN-ACK -> ACK)
 *   2. Connection termination (FIN -> ACK -> FIN -> ACK)
 *   3. RST handling
 *   4. Invalid transitions
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Test result tracking */
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg)  printf("FAIL: %s\n", msg); tests_failed++

/* Helper: create a test socket */
static socket_t* create_test_socket(void) {
    socket_t *sock = calloc(1, sizeof(socket_t));
    sock->fd = 1;
    sock->type = SOCK_STREAM;
    sock->state = TCP_CLOSED;
    sock->mss = TCP_DEFAULT_MSS;
    sock->window = TCP_WINDOW_SIZE;
    sock->srtt = TCP_DEFAULT_SRTT << 4;
    sock->rttvar = 500 << 4;
    return sock;
}

/* ============================================================================
 * Test: Three-way handshake
 * ============================================================================ */

static void test_three_way_handshake(void) {
    TEST("three_way_handshake");

    socket_t *sock = create_test_socket();

    /* Initial state: CLOSED */
    if (sock->state != TCP_CLOSED) {
        FAIL("initial state not CLOSED");
        free(sock);
        return;
    }

    /* Client sends SYN -> SYN_SENT */
    sock->state = TCP_SYN_SENT;
    if (sock->state != TCP_SYN_SENT) {
        FAIL("SYN_SENT state failed");
        free(sock);
        return;
    }

    /* Server receives SYN, sends SYN-ACK -> SYN_RECEIVED */
    sock->state = tcp_state_machine(sock, TCP_FLAG_SYN | TCP_FLAG_ACK);
    if (sock->state != TCP_SYN_RECEIVED) {
        FAIL("SYN_RECEIVED state failed");
        free(sock);
        return;
    }

    /* Client receives SYN-ACK + ACK -> ESTABLISHED */
    sock->state = tcp_state_machine(sock, TCP_FLAG_ACK);
    if (sock->state != TCP_ESTABLISHED) {
        FAIL("ESTABLISHED state failed");
        free(sock);
        return;
    }

    PASS();
    free(sock);
}

/* ============================================================================
 * Test: Connection termination (FIN handshake)
 * ============================================================================ */

static void test_connection_termination(void) {
    TEST("connection_termination");

    socket_t *sock = create_test_socket();

    /* Start from ESTABLISHED */
    sock->state = TCP_ESTABLISHED;

    /* Client sends FIN -> FIN_WAIT_1 */
    sock->state = tcp_state_machine(sock, TCP_FLAG_FIN);

    /* Server receives FIN, sends ACK -> CLOSE_WAIT */
    sock->state = tcp_state_machine(sock, TCP_FLAG_ACK);

    if (sock->state != TCP_CLOSE_WAIT) {
        FAIL("CLOSE_WAIT state failed");
        free(sock);
        return;
    }

    PASS();
    free(sock);
}

/* ============================================================================
 * Test: RST handling
 * ============================================================================ */

static void test_rst_handling(void) {
    TEST("rst_handling");

    socket_t *sock = create_test_socket();

    /* Start from ESTABLISHED */
    sock->state = TCP_ESTABLISHED;

    /* Receive RST -> CLOSED */
    sock->state = tcp_state_machine(sock, TCP_FLAG_RST);

    if (sock->state == TCP_CLOSED) {
        PASS();
    } else {
        FAIL("RST should transition to CLOSED");
    }

    free(sock);
}

/* ============================================================================
 * Test: FIN-WAIT-1 state transitions
 * ============================================================================ */

static void test_fin_wait_states(void) {
    TEST("fin_wait_states");

    socket_t *sock = create_test_socket();

    /* Start from FIN_WAIT_1 */
    sock->state = TCP_FIN_WAIT_1;

    /* Receive FIN+ACK -> TIME_WAIT */
    sock->state = tcp_state_machine(sock, TCP_FLAG_FIN | TCP_FLAG_ACK);

    if (sock->state == TCP_TIME_WAIT) {
        PASS();
    } else {
        FAIL("FIN_WAIT_1 + FIN+ACK should go to TIME_WAIT");
    }

    free(sock);
}

/* ============================================================================
 * Test: FIN-WAIT-2 state transitions
 * ============================================================================ */

static void test_fin_wait_2(void) {
    TEST("fin_wait_2");

    socket_t *sock = create_test_socket();

    /* Start from FIN_WAIT_2 */
    sock->state = TCP_FIN_WAIT_2;

    /* Receive FIN -> TIME_WAIT */
    sock->state = tcp_state_machine(sock, TCP_FLAG_FIN);

    if (sock->state == TCP_TIME_WAIT) {
        PASS();
    } else {
        FAIL("FIN_WAIT_2 + FIN should go to TIME_WAIT");
    }

    free(sock);
}

/* ============================================================================
 * Test: LAST_ACK state
 * ============================================================================ */

static void test_last_ack(void) {
    TEST("last_ack");

    socket_t *sock = create_test_socket();

    /* Start from LAST_ACK */
    sock->state = TCP_LAST_ACK;

    /* Receive ACK -> CLOSED */
    sock->state = tcp_state_machine(sock, TCP_FLAG_ACK);

    if (sock->state == TCP_CLOSED) {
        PASS();
    } else {
        FAIL("LAST_ACK + ACK should go to CLOSED");
    }

    free(sock);
}

/* ============================================================================
 * Test: TIME_WAIT state
 * ============================================================================ */

static void test_time_wait(void) {
    TEST("time_wait");

    socket_t *sock = create_test_socket();

    /* Start from TIME_WAIT */
    sock->state = TCP_TIME_WAIT;

    /* Only RST can transition from TIME_WAIT */
    sock->state = tcp_state_machine(sock, TCP_FLAG_ACK);

    if (sock->state == TCP_TIME_WAIT) {
        PASS();
    } else {
        FAIL("TIME_WAIT should not change on ACK");
    }

    free(sock);
}

/* ============================================================================
 * Test: LISTEN state
 * ============================================================================ */

static void test_listen_state(void) {
    TEST("listen_state");

    socket_t *sock = create_test_socket();

    /* Set to LISTEN */
    sock->state = TCP_LISTEN;

    /* Receive SYN */
    sock->state = tcp_state_machine(sock, TCP_FLAG_SYN);

    if (sock->state == TCP_SYN_RECEIVED) {
        PASS();
    } else {
        FAIL("LISTEN + SYN should go to SYN_RECEIVED");
    }

    free(sock);
}

/* ============================================================================
 * Test: TCP flags extraction
 * ============================================================================ */

static void test_tcp_flags_extraction(void) {
    TEST("tcp_flags_extraction");

    uint8_t flags_byte = (5 << 4) | (TCP_FLAG_SYN | TCP_FLAG_ACK);
    uint8_t flags = tcp_flags(&flags_byte);

    if (flags == (TCP_FLAG_SYN | TCP_FLAG_ACK)) {
        PASS();
    } else {
        FAIL("flags extraction failed");
    }
}

/* ============================================================================
 * Test: TCP data offset extraction
 * ============================================================================ */

static void test_tcp_data_offset(void) {
    TEST("tcp_data_offset");

    uint8_t flags_byte = (5 << 4) | TCP_FLAG_ACK;
    uint8_t doff = tcp_data_offset(&flags_byte);

    if (doff == 20) {  /* 5 * 4 = 20 bytes */
        PASS();
    } else {
        FAIL("data offset should be 20 for IHL=5");
    }
}

/* ============================================================================
 * Test: Retransmission counter
 * ============================================================================ */

static void test_retransmission(void) {
    TEST("retransmission");

    socket_t *sock = create_test_socket();
    sock->state = TCP_ESTABLISHED;
    sock->retransmit_cnt = 0;
    sock->srtt = 500 << 4;
    sock->rttvar = 100 << 4;

    /* Simulate timeouts */
    int max_retrans = TCP_MAX_RETRANSMISSIONS;
    for (int i = 0; i < max_retrans; i++) {
        tcp_handle_timeout(sock);
    }

    /* After max retransmissions, should be CLOSED */
    if (sock->state == TCP_CLOSED) {
        PASS();
    } else {
        FAIL("should be CLOSED after max retransmissions");
    }

    free(sock);
}

/* ============================================================================
 * Main test runner
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  TCP State Machine Unit Tests\n");
    printf("========================================\n\n");

    test_three_way_handshake();
    test_connection_termination();
    test_rst_handling();
    test_fin_wait_states();
    test_fin_wait_2();
    test_last_ack();
    test_time_wait();
    test_listen_state();
    test_tcp_flags_extraction();
    test_tcp_data_offset();
    test_retransmission();

    printf("\n========================================\n");
    printf("  Results: %d/%d passed", tests_passed, tests_run);
    if (tests_failed > 0) {
        printf(" (%d failed)", tests_failed);
    }
    printf("\n");
    printf("========================================\n");

    return tests_failed > 0 ? 1 : 0;
}
