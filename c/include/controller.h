#ifndef CONTROLLER_H
#define CONTROLLER_H

#include "store.h"

typedef struct {
    int status;
    char *body;
} HttpResponse;

HttpResponse controller(
    MemoryStore *store,
    const char *method,
    const char *path,
    const char *body
);

HttpResponse http_error(int status);

#endif
