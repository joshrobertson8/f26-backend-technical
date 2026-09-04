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

typedef struct {
    char *id;
    EventInput data;
} Event;

typedef struct {
    const char *id;
    const char *name;
} User;

bool event_input_parse(const char *json, EventInput *out);

bool event_input_copy(EventInput *out, const EventInput *input);

void event_input_free(EventInput *input);

cJSON *event_json(const Event *event);

char *copy_string(const char *value);

#endif
