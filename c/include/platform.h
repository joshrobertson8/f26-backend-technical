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

