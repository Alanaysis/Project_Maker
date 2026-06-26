/*
 * socket_api.c - Socket API implementation
 *
 * The Socket API provides a standardized interface for network communication.
 * It abstracts the underlying protocol details into a file-descriptor-like model.
 *
 * Socket API Functions (套接字 API 函数):
 *   socket()  - Create a network endpoint
 *   bind()    - Associate socket with a local address/port
 *   listen()  - Mark TCP socket as passive (accept connections)
 *   accept()  - Accept incoming TCP connection
 *   connect() - Initiate TCP connection to remote host
 *   send()    - Send data
 *   recv()    - Receive data
 *   close()   - Close socket and release resources
 *
 * Socket Types (套接字类型):
 *   SOCK_STREAM - TCP: reliable, ordered, connection-oriented byte stream
 *   SOCK_DGRAM  - UDP: connectionless, datagram-based
 *
 * This implementation provides a simplified but functional Socket API
 * for learning purposes. In production, you'd use BSD sockets (recv,
 * send, accept, etc.) from libc.
 */

#include "embedded_net.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* ============================================================================
 * Socket Table Management (套接字表管理)
 * ============================================================================ */

static socket_t *find_socket(int fd) {
    socket_t *sockets = net_get_sockets();
    int count = net_get_socket_count();
    for (int i = 0; i < count; i++) {
        if (sockets[i].fd == fd) {
            return &sockets[i];
        }
    }
    return NULL;
}

static int find_free_slot(void) {
    socket_t *sockets = net_get_sockets();
    int count = net_get_socket_count();
    for (int i = 0; i < MAX_SOCKETS; i++) {
        if (!sockets[i].is_bound && !sockets[i].is_connected) {
            return i;
        }
    }
    return -1;
}

/* ============================================================================
 * socket_create() - Create a Socket (创建套接字)
 *
 * Creates a new socket of the specified type (SOCK_STREAM or SOCK_DGRAM).
 * Returns a file descriptor (positive integer) or -1 on failure.
 *
 * In the BSD sockets API:
 *   int fd = socket(AF_INET, SOCK_STREAM, 0);
 *   fd = socket(AF_INET, SOCK_DGRAM, 0);
 *
 * The domain (AF_INET) specifies IPv4. The type determines the protocol.
 * The protocol (0) means "use the default for this type."
 * ============================================================================ */

int socket_create(int type) {
    socket_t *sockets = net_get_sockets();
    int slot = find_free_slot();

    if (slot < 0) {
        return SOCKET_INVALID;
    }

    socket_t *sock = &sockets[slot];
    memset(sock, 0, sizeof(socket_t));

    sock->fd = slot + 1;  /* FDs start at 1 */
    sock->type = type;
    sock->state = TCP_CLOSED;
    sock->mss = TCP_DEFAULT_MSS;
    sock->window = TCP_WINDOW_SIZE;
    sock->srtt = TCP_DEFAULT_SRTT << 4;  /* Fixed-point: ms * 16 */
    sock->rttvar = 500 << 4;
    sock->is_bound = 1;

    net_increment_socket_count();

    return sock->fd;
}

/* ============================================================================
 * socket_bind() - Bind Socket to Address (绑定套接字到地址)
 *
 * Associates a local address and port with the socket.
 * Only one socket can be bound to a specific port at a time.
 *
 * For TCP servers, binding to port 0 means "let the OS choose."
 * For UDP, binding is needed before sending/receiving.
 *
 * In BSD API:
 *   struct sockaddr_in addr;
 *   addr.sin_family = AF_INET;
 *   addr.sin_port = htons(port);
 *   addr.sin_addr.s_addr = INADDR_ANY;  // or specific IP
 *   bind(fd, (struct sockaddr*)&addr, sizeof(addr));
 * ============================================================================ */

int socket_bind(int fd, const sock_addr_t *addr) {
    if (!addr) return -1;

    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    sock->local_addr = *addr;
    sock->is_bound = 1;

    return 0;
}

/* ============================================================================
 * socket_listen() - Listen for Connections (监听连接)
 *
 * Marks a TCP socket as passive, meaning it will accept incoming
 * connections instead of initiating them.
 *
 * The backlog parameter specifies the maximum number of pending
 * connections that can queue up.
 *
 * In BSD API:
 *   listen(fd, SOMAXCONN);
 *
 * After listen(), the socket is in LISTEN state and can accept
 * incoming connections via accept().
 * ============================================================================ */

int socket_listen(int fd, int backlog) {
    (void)backlog;  /* Simplified: don't enforce backlog limit */

    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    if (sock->type != SOCK_STREAM) {
        return -1;  /* Only TCP sockets can listen */
    }

    sock->state = TCP_LISTEN;
    sock->is_listening = 1;

    return 0;
}

/* ============================================================================
 * socket_accept() - Accept Incoming Connection (接受传入连接)
 *
 * Accepts an incoming TCP connection on a listening socket.
 * Returns a new socket descriptor for the accepted connection.
 *
 * For a listening socket:
 *   1. Wait for incoming SYN
 *   2. Complete TCP three-way handshake
 *   3. Create new socket for the connection
 *   4. Return the new socket descriptor
 *
 * In BSD API:
 *   struct sockaddr_in peer;
 *   int new_fd = accept(fd, (struct sockaddr*)&peer, &len);
 * ============================================================================ */

int socket_accept(int fd, sock_addr_t *addr) {
    socket_t *sock = find_socket(fd);
    if (!sock || !sock->is_listening) {
        return SOCKET_INVALID;
    }

    /* In a full implementation, we'd find a connection in SYN_RECEIVED
     * or ESTABLISHED state and return it. For this learning implementation,
     * we return the listening socket itself for simplicity. */
    sock->state = TCP_ESTABLISHED;
    sock->is_listening = 0;

    if (addr) {
        *addr = sock->peer_addr;
    }

    return sock->fd;
}

/* ============================================================================
 * socket_connect() - Initiate TCP Connection (发起 TCP 连接)
 *
 * Initiates a TCP connection to the specified remote address.
 * This performs the TCP three-way handshake:
 *
 *   Client                          Server
 *   ------                          ------
 *   [SYN, seq=I] ---------------->
 *                              <---- [SYN-ACK, seq=J, ack=I+1]
 *   [ACK, ack=J+1] ------------>
 *
 *   Connection is now ESTABLISHED
 *
 * In BSD API:
 *   connect(fd, (struct sockaddr*)&addr, sizeof(addr));
 * ============================================================================ */

int socket_connect(int fd, const sock_addr_t *addr) {
    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    if (sock->type != SOCK_STREAM) {
        return -1;  /* Only TCP sockets can connect */
    }

    sock->peer_addr = *addr;
    sock->is_connected = 1;

    /* Send initial SYN */
    sock->state = TCP_SYN_SENT;
    sock->snd_seq = 1;  /* Initial sequence number */
    sock->rcv_seq = 1;
    sock->snd_una = 1;

    /* Send SYN segment */
    tcp_send_segment(sock, sock->snd_seq, 0, NULL, 0, TCP_FLAG_SYN);

    /* In a full implementation, we'd wait for SYN-ACK here.
     * For this learning implementation, we simulate the handshake. */
    sock->state = TCP_ESTABLISHED;

    return 0;
}

/* ============================================================================
 * socket_send() - Send Data (发送数据)
 *
 * Sends data over a TCP connection.
 *
 * TCP send semantics:
 *   - Data is placed in the send buffer
 *   - TCP handles segmentation, flow control, and retransmission
 *   - Returns the number of bytes accepted for sending
 *   - May return less than requested if buffer is full
 *
 * In BSD API:
 *   int bytes_sent = send(fd, buf, len, 0);
 * ============================================================================ */

int socket_send(int fd, const void *buf, int len) {
    socket_t *sock = find_socket(fd);
    if (!sock || !sock->is_connected) {
        return -1;
    }

    if (sock->type != SOCK_STREAM) {
        return -1;
    }

    if (!buf || len <= 0) {
        return 0;
    }

    /* Copy data to send buffer */
    int to_send = len < sock->mss ? len : sock->mss;
    memcpy(sock->rbuf, buf, to_send);
    sock->rbuf_len = to_send;

    /* Send with PSH flag to flush */
    tcp_send(sock, (const uint8_t *)buf, to_send, TCP_FLAG_ACK | TCP_FLAG_PSH);

    /* Update sequence number */
    sock->snd_seq += to_send;
    sock->snd_una = sock->snd_seq;

    return to_send;
}

/* ============================================================================
 * socket_sendto() - Send to Address (UDP) (发送到指定地址 - UDP)
 *
 * Sends a UDP datagram to the specified address.
 * Used for connectionless communication.
 *
 * In BSD API:
 *   int sent = sendto(fd, buf, len, 0, &addr, addrlen);
 * ============================================================================ */

int socket_sendto(int fd, const void *buf, int len, const sock_addr_t *addr) {
    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    if (sock->type != SOCK_DGRAM) {
        return -1;
    }

    if (!buf || len <= 0) {
        return 0;
    }

    net_interface_t *iface = net_get_interface();
    if (!iface) return -1;

    uint16_t dst_port = addr ? addr->sin_port : 0;
    uint32_t dst_ip = addr ? addr->sin_addr : 0;

    return udp_send(iface, dst_ip, dst_port, sock->local_addr.sin_port,
                    (const uint8_t *)buf, len);
}

/* ============================================================================
 * socket_recv() - Receive Data (接收数据)
 *
 * Receives data from a TCP connection.
 *
 * TCP recv semantics:
 *   - Returns data from the receive buffer
 *   - May block if no data is available (non-blocking mode not implemented)
 *   - Returns 0 on connection close
 *   - Returns -1 on error
 *
 * In BSD API:
 *   int bytes_recv = recv(fd, buf, len, 0);
 * ============================================================================ */

int socket_recv(int fd, void *buf, int len) {
    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    /* Check receive buffer */
    if (sock->rbuf_offset >= sock->rbuf_len) {
        return 0;  /* No data available */
    }

    int avail = sock->rbuf_len - sock->rbuf_offset;
    int to_recv = avail < len ? avail : len;

    memcpy(buf, sock->rbuf + sock->rbuf_offset, to_recv);
    sock->rbuf_offset += to_recv;

    return to_recv;
}

/* ============================================================================
 * socket_recvfrom() - Receive from Address (UDP) (从指定地址接收 - UDP)
 *
 * Receives a UDP datagram and optionally the sender's address.
 *
 * In BSD API:
 *   int recv = recvfrom(fd, buf, len, 0, &addr, &addrlen);
 * ============================================================================ */

int socket_recvfrom(int fd, void *buf, int len, sock_addr_t *addr) {
    /* Simplified: UDP receive is handled by udp_input() which would
     * deliver to the appropriate socket. For this learning implementation,
     * we return a placeholder. */
    (void)fd;
    (void)buf;
    (void)len;
    (void)addr;

    return 0;
}

/* ============================================================================
 * socket_close() - Close Socket (关闭套接字)
 *
 * Closes a socket and releases its resources.
 *
 * For TCP sockets, this initiates the TCP connection termination:
 *   1. Send FIN (graceful close)
 *   2. Wait for FIN-ACK from peer
 *   3. Send final ACK
 *   4. Enter TIME_WAIT state
 *   5. Transition to CLOSED
 *
 * In BSD API:
 *   close(fd);
 * ============================================================================ */

int socket_close(int fd) {
    socket_t *sock = find_socket(fd);
    if (!sock) return -1;

    /* Send FIN for TCP sockets */
    if (sock->type == SOCK_STREAM && sock->state != TCP_CLOSED) {
        tcp_send(sock, NULL, 0, TCP_FLAG_FIN | TCP_FLAG_ACK);
        sock->state = TCP_FIN_WAIT_1;
    }

    /* Reset socket */
    memset(sock, 0, sizeof(socket_t));

    return 0;
}
