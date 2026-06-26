/*
 * socket_programming_demo.c - Socket Programming Demo
 *
 * Demonstrates the Socket API used in network programming.
 *
 * The Socket API is the standard interface for network communication in
 * Unix-like systems (BSD sockets) and Windows (Winsock).
 *
 * Server-side workflow (服务器端工作流):
 *   1. socket()     - Create a socket endpoint
 *   2. bind()       - Bind to a local address/port
 *   3. listen()     - Mark as listening (TCP only)
 *   4. accept()     - Accept incoming connection
 *   5. recv()/send() - Communicate
 *   6. close()      - Close the socket
 *
 * Client-side workflow (客户端工作流):
 *   1. socket()     - Create a socket endpoint
 *   2. connect()    - Connect to server
 *   3. send()/recv() - Communicate
 *   4. close()      - Close the socket
 *
 * Common port numbers (常见端口号):
 *   20/21   FTP
 *   22      SSH
 *   25      SMTP
 *   53      DNS
 *   80      HTTP
 *   443     HTTPS
 *   3306    MySQL
 *   5432    PostgreSQL
 */

#include "embedded_net.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Demo configuration */
#define DEMO_PORT     9000
#define DEMO_ADDR     "192.168.1.1"
#define DEMO_CLIENT_IP "192.168.1.100"
#define DEMO_DATA     "Hello from Socket Demo!"

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

    demo_iface.ip_addr = string_to_ip(DEMO_CLIENT_IP);
    demo_iface.subnet_mask = string_to_ip("255.255.255.0");
    demo_iface.gateway = string_to_ip("192.168.1.1");
    demo_iface.dns_server = string_to_ip("8.8.8.8");
    demo_iface.is_up = 1;
    demo_iface.has_ip = 1;
}

/* ============================================================================
 * Demo: Socket API Reference
 *
 * Shows the complete Socket API with explanations.
 * ============================================================================ */

static void demo_socket_api_reference(void) {
    printf("\n=== Socket API Reference ===\n\n");

    printf("C/S Architecture (客户端/服务器架构):\n\n");
    printf("  Server                          Client\n");
    printf("  ------                          ------\n");
    printf("  socket()     --------------->   socket()\n");
    printf("  bind()                              \n");
    printf("  listen()                            \n");
    printf("  accept()   <---------------   connect()\n");
    printf("  recv()     <---------------   send()\n");
    printf("  send()     --------------->   recv()\n");
    printf("  close()                            \n");
    printf("                                    close()\n");

    printf("\nSocket API Functions:\n");
    printf("  int socket(int domain, int type, int protocol);\n");
    printf("    Creates a socket. domain=AF_INET (IPv4), type=SOCK_STREAM/UDP\n");
    printf("\n  int bind(int fd, const struct sockaddr *addr, socklen_t len);\n");
    printf("    Binds socket to local address. Server must bind.\n");
    printf("\n  int listen(int fd, int backlog);\n");
    printf("    Marks TCP socket as passive. Specifies max pending connections.\n");
    printf("\n  int accept(int fd, struct sockaddr *addr, socklen_t *len);\n");
    printf("    Accepts incoming connection. Returns new socket fd.\n");
    printf("\n  int connect(int fd, const struct sockaddr *addr, socklen_t len);\n");
    printf("    Initiates TCP connection to server.\n");
    printf("\n  int send(int fd, const void *buf, int len, int flags);\n");
    printf("    Sends data on a connected socket.\n");
    printf("\n  int recv(int fd, void *buf, int len, int flags);\n");
    printf("    Receives data from a connected socket.\n");
    printf("\n  int close(int fd);\n");
    printf("    Closes the socket.\n");
}

/* ============================================================================
 * Demo: TCP Socket Communication
 *
 * Simulates a TCP client-server interaction using our Socket API.
 * ============================================================================ */

static void demo_tcp_socket(void) {
    printf("\n=== TCP Socket Communication Demo ===\n\n");

    /* Create server socket */
    int server_fd = socket_create(SOCK_STREAM);
    printf("Server: socket(SOCK_STREAM) = fd=%d\n", server_fd);

    /* Bind server socket */
    sock_addr_t server_addr = {
        .sin_addr = string_to_ip(DEMO_ADDR),
        .sin_port = htons(DEMO_PORT),
        .sin_family = 2
    };
    socket_bind(server_fd, &server_addr);
    printf("Server: bind(fd=%d, port=%d) = 0\n", server_fd, DEMO_PORT);

    /* Listen */
    socket_listen(server_fd, SOMAXCONN);
    printf("Server: listen(fd=%d, backlog=%d) = 0\n", server_fd, SOMAXCONN);

    /* Create client socket */
    int client_fd = socket_create(SOCK_STREAM);
    printf("\nClient: socket(SOCK_STREAM) = fd=%d\n", client_fd);

    /* Connect */
    sock_addr_t peer_addr = {
        .sin_addr = string_to_ip(DEMO_ADDR),
        .sin_port = htons(DEMO_PORT),
        .sin_family = 2
    };
    socket_connect(client_fd, &peer_addr);
    printf("Client: connect(fd=%d, %s:%d) = 0\n",
           client_fd, DEMO_ADDR, DEMO_PORT);

    /* Send data */
    const char *msg = DEMO_DATA;
    int sent = socket_send(client_fd, msg, strlen(msg));
    printf("\nClient: send(fd=%d, \"%s\") = %d bytes\n",
           client_fd, msg, sent);

    /* Receive (simulated) */
    char recv_buf[256];
    int recv_len = 0;
    printf("Server: recv(fd=%d, buf, %d) = '%s' bytes\n",
           server_fd, (int)sizeof(recv_buf), msg);
    recv_len = sent;
    memcpy(recv_buf, msg, recv_len);
    recv_buf[recv_len] = '\0';

    /* Server response */
    const char *response = "Server received your message!";
    sent = socket_send(server_fd, response, strlen(response));
    printf("\nServer: send(fd=%d, \"%s\") = %d bytes\n",
           server_fd, response, sent);

    /* Client receives response */
    printf("Client: recv(fd=%d, buf, %d) = '%s' bytes\n",
           client_fd, (int)sizeof(recv_buf), response);

    /* Close */
    socket_close(client_fd);
    socket_close(server_fd);
    printf("\nBoth sockets closed. Connection terminated.\n");
}

/* ============================================================================
 * Demo: UDP Socket Communication
 *
 * Simulates a UDP client-server interaction.
 * ============================================================================ */

static void demo_udp_socket(void) {
    printf("\n=== UDP Socket Communication Demo ===\n\n");

    /* Create UDP socket */
    int udp_fd = socket_create(SOCK_DGRAM);
    printf("Client: socket(SOCK_DGRAM) = fd=%d\n", udp_fd);

    /* Bind (for receiving responses) */
    sock_addr_t local_addr = {
        .sin_addr = string_to_ip(DEMO_CLIENT_IP),
        .sin_port = htons(DEMO_PORT),
        .sin_family = 2
    };
    socket_bind(udp_fd, &local_addr);
    printf("Client: bind(fd=%d, port=%d) = 0\n", udp_fd, DEMO_PORT);

    /* Send to server */
    sock_addr_t server_addr = {
        .sin_addr = string_to_ip(DEMO_ADDR),
        .sin_port = htons(DEMO_PORT + 1),
        .sin_family = 2
    };
    const char *msg = DEMO_DATA;
    int sent = socket_sendto(udp_fd, msg, strlen(msg), &server_addr);
    printf("\nClient: sendto(fd=%d, \"%s\", %s:%d) = %d bytes\n",
           udp_fd, msg, DEMO_ADDR, DEMO_PORT + 1, sent);

    /* No connection needed for UDP! */
    printf("\nNote: UDP is connectionless - no connect() or accept() needed.\n");
    printf("Each datagram is independent.\n");

    /* Close */
    socket_close(udp_fd);
    printf("\nUDP socket closed.\n");
}

/* ============================================================================
 * Demo: Socket Address Structure
 *
 * Shows how socket addresses are structured.
 * ============================================================================ */

static void demo_sockaddr_structure(void) {
    printf("\n=== Socket Address Structure ===\n\n");

    printf("sockaddr_in structure:\n");
    printf("  struct sockaddr_in {\n");
    printf("      sa_family_t  sin_family;    // Address family (AF_INET = 2)\n");
    printf("      in_port_t    sin_port;       // Port (network byte order)\n");
    printf("      struct in_addr sin_addr;      // IP address (network byte order)\n");
    printf("      char         sin_zero[8];    // Padding\n");
    printf("  };\n");

    printf("\nCommon address constants:\n");
    printf("  INADDR_ANY      = 0.0.0.0  (bind to all interfaces)\n");
    printf("  INADDR_BROADCAST = 255.255.255.255 (broadcast)\n");
    printf("  INADDR_LOOPBACK  = 127.0.0.1 (localhost)\n");

    printf("\nByte order conversion:\n");
    printf("  htons()  - Host to Network Short (16-bit)\n");
    printf("  htonl()  - Host to Network Long (32-bit)\n");
    printf("  ntohs()  - Network to Host Short\n");
    printf("  ntohl()  - Network to Host Long\n");
    printf("\nNetwork byte order is BIG-ENDIAN (big-endian).\n");
    printf("Most PCs use LITTLE-ENDIAN. Conversion is needed!\n");
}

/* ============================================================================
 * Main demo driver
 * ============================================================================ */

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("========================================\n");
    printf("  Socket Programming Demo - embedded-network\n");
    printf("========================================\n");

    init_demo_interface();
    net_stack_init(&demo_iface);

    printf("\nLocal Interface:\n");
    debug_print_mac("MAC Address", &demo_iface.mac);
    printf("IP Address:    %s\n", ip_to_string(demo_iface.ip_addr));

    /* Run demos */
    demo_socket_api_reference();
    demo_tcp_socket();
    demo_udp_socket();
    demo_sockaddr_structure();

    printf("\n========================================\n");
    printf("  Demo Complete!\n");
    printf("========================================\n");

    return 0;
}
