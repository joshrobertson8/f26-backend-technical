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

