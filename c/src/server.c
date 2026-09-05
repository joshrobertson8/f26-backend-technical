#define _POSIX_C_SOURCE 200809L

#include "controller.h"
#include "picohttpparser.h"
#include "platform.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_REQUEST 65536

static volatile sig_atomic_t stopping = 0;

static void stop_server(int signal_number) {
    (void)signal_number;
    stopping = 1;
}

static bool send_all(Socket connection, const char *buffer, size_t length) {
    while (length > 0) {
        int sent = (int)send(connection, buffer, (int)length, 0);

        if (sent < 0 && socket_interrupted()) {
            continue;
        }

