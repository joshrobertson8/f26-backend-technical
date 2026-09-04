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

    return false;
}

bool event_input_parse(const char *json, EventInput *out) {
    *out = (EventInput){0};

    cJSON *root = cJSON_ParseWithOpts(json, NULL, true);

    if (!cJSON_IsObject(root)) {
        cJSON_Delete(root);
        return false;
    }

    const cJSON *field = NULL;

    cJSON_ArrayForEach(field, root) {
        if (strcmp(field->string, "title") != 0 &&
            strcmp(field->string, "description") != 0 &&
            strcmp(field->string, "inviteeIds") != 0) {
            goto fail;
        }
    }

    const cJSON *title = cJSON_GetObjectItemCaseSensitive(root, "title");
    const cJSON *description = cJSON_GetObjectItemCaseSensitive(root, "description");
    const cJSON *invitees = cJSON_GetObjectItemCaseSensitive(root, "inviteeIds");

    if (!cJSON_IsString(title)) {
        goto fail;
    }

    const char *title_text = title->valuestring;
    bool nonblank = false;

    for (size_t i = 0; title_text[i] != '\0'; i++) {
        if (!isspace((unsigned char)title_text[i])) {
            nonblank = true;
            break;
        }
    }

    if (!nonblank) {
        goto fail;
    }

    if (description != NULL && !cJSON_IsString(description)) {
        goto fail;
    }

    if (invitees != NULL && !cJSON_IsArray(invitees)) {
        goto fail;
    }

    const char *description_text = "";

    if (description != NULL) {
        description_text = description->valuestring;
    }

    out->title = copy_string(title->valuestring);
    out->description = copy_string(description_text);

