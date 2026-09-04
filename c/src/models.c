#include "models.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

char *copy_string(const char *value) {
    size_t size = strlen(value) + 1;
    char *result = malloc(size);

    if (result != NULL) {
        memcpy(result, value, size);
    }

    return result;
}

void event_input_free(EventInput *input) {
    free(input->title);
    free(input->description);

    for (size_t i = 0; i < input->invitee_count; i++) {
        free(input->invitee_ids[i]);
    }

    free(input->invitee_ids);
    *input = (EventInput){0};
}

bool event_input_copy(EventInput *out, const EventInput *input) {
    *out = (EventInput){0};
    out->title = copy_string(input->title);
    out->description = copy_string(input->description);

    if (out->title == NULL || out->description == NULL) {
        goto fail;
    }

    if (input->invitee_count > 0) {
        out->invitee_ids = calloc(input->invitee_count, sizeof(char *));

        if (out->invitee_ids == NULL) {
            goto fail;
        }

        for (size_t i = 0; i < input->invitee_count; i++) {
            out->invitee_ids[i] = copy_string(input->invitee_ids[i]);
            out->invitee_count++;

            if (out->invitee_ids[i] == NULL) {
                goto fail;
            }
        }
    }

    return true;

fail:
    event_input_free(out);

