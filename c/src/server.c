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

        if (sent <= 0) {
            return false;
        }

        buffer += sent;
        length -= (size_t)sent;
    }

    return true;
}

static void respond(Socket connection, HttpResponse response) {
    const char *reason = "Internal Server Error";

    switch (response.status) {
        case 200:
            reason = "OK";
            break;
        case 201:
            reason = "Created";
            break;
        case 204:
            reason = "No Content";
            break;
        case 400:
            reason = "Bad Request";
            break;
        case 404:
            reason = "Not Found";
            break;
        case 405:
            reason = "Method Not Allowed";
            break;
        case 413:
            reason = "Content Too Large";
            break;
        case 501:
            reason = "Not Implemented";
            break;
    }

    const char *body = response.body;

    if (body == NULL) {
        body = "";
    }

