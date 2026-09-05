#ifndef SERVICE_H
#define SERVICE_H

#include "store.h"

typedef enum {
    SERVICE_OK = 200,
    SERVICE_BAD_REQUEST = 400,
    SERVICE_NOT_FOUND = 404,
    SERVICE_INTERNAL_ERROR = 500,
    SERVICE_NOT_IMPLEMENTED = 501
} ServiceStatus;

