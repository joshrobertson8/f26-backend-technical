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

