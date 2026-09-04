#ifndef MODELS_H
#define MODELS_H

#include <stdbool.h>
#include <stddef.h>

#include "cJSON.h"

typedef struct {
    char *title;
    char *description;
    char **invitee_ids;
    size_t invitee_count;
} EventInput;

