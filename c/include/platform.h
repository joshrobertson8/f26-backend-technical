#ifndef PLATFORM_H
#define PLATFORM_H

#include <signal.h>
#include <stdbool.h>
#include <stdio.h>

#ifdef _WIN32

#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0600
#endif

#include <winsock2.h>
#include <ws2tcpip.h>

#define strncasecmp _strnicmp

typedef SOCKET Socket;
#define INVALID_CONNECTION INVALID_SOCKET

static bool start_sockets(void) {
    WSADATA data;

    return WSAStartup(MAKEWORD(2, 2), &data) == 0;
}

static void stop_sockets(void) {
    WSACleanup();
}

static void close_socket(Socket connection) {
    closesocket(connection);
}

static bool socket_interrupted(void) {
    return WSAGetLastError() == WSAEINTR;
}

static void socket_error(const char *operation) {
    fprintf(stderr, "%s: Windows socket error %d\n", operation, WSAGetLastError());
}

static void set_socket_timeout(Socket connection) {
    DWORD timeout = 5000;

    setsockopt(connection, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout, sizeof(timeout));
    setsockopt(connection, SOL_SOCKET, SO_SNDTIMEO, (const char *)&timeout, sizeof(timeout));
}

static void install_signal_handlers(void (*handler)(int)) {
    signal(SIGINT, handler);
    signal(SIGTERM, handler);
}

#else

#include <arpa/inet.h>
#include <errno.h>
#include <strings.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

typedef int Socket;
#define INVALID_CONNECTION (-1)

static bool start_sockets(void) {
    return true;
}

