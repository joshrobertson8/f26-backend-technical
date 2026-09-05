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

    char headers[512];
    int length = snprintf(
        headers,
        sizeof(headers),
        "HTTP/1.1 %d %s\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n\r\n",
        response.status,
        reason,
        strlen(body)
    );

    if (length > 0 && (size_t)length < sizeof(headers) && send_all(connection, headers, (size_t)length)) {
        send_all(connection, body, strlen(body));
    }

    free(response.body);
}

static int hex_digit(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }

    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }

    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }

    return -1;
}

static bool decode_path(char *path) {
    char *source = path;
    char *destination = path;

    while (*source != '\0' && *source != '?') {
        if (*source == '%') {
            if (source[1] == '\0' || source[2] == '\0') {
                return false;
            }

            int high = hex_digit(source[1]);
            int low = hex_digit(source[2]);
            int value = high * 16 + low;

            if (high < 0 || low < 0 || value == 0) {
                return false;
            }

            *destination = (char)value;
            source += 3;
        } else {
            *destination = *source;
            source += 1;
        }

        destination += 1;
    }

    *destination = '\0';

    return true;
}

