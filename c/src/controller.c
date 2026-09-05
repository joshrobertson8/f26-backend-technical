#include "controller.h"
#include "service.h"

#include <stdlib.h>
#include <string.h>

HttpResponse http_error(int status) {
    const char *message = "Internal server error";

    switch (status) {
        case 400:
            message = "Invalid event or invitations";
            break;
        case 404:
            message = "Not found";
            break;
        case 405:
            message = "Method not allowed";
            break;
        case 413:
            message = "Request too large";
            break;
        case 501:
            message = "Implement the event service";
            break;
    }

    cJSON *json = cJSON_CreateObject();
    cJSON_AddStringToObject(json, "error", message);

    char *body = cJSON_PrintUnformatted(json);
    cJSON_Delete(json);

    HttpResponse response = {status, body};

    return response;
}

static HttpResponse json_response(int status, cJSON *json) {
    if (json == NULL) {
        return http_error(500);
    }

    char *body = cJSON_PrintUnformatted(json);
    cJSON_Delete(json);

    if (body == NULL) {
        return http_error(500);
    }

    HttpResponse response = {status, body};

    return response;
}

HttpResponse controller(
    MemoryStore *store,
    const char *method,
    const char *path,
    const char *body
) {
    if (strcmp(path, "/api/health") == 0 && strcmp(method, "GET") == 0) {
        HttpResponse response = {200, copy_string("{\"status\":\"ok\"}")};

        return response;
    }

    if (strcmp(path, "/api/users") == 0 && strcmp(method, "GET") == 0) {
        cJSON *users = store_users_json(store);

        return json_response(200, users);
    }

    bool events_path = strcmp(path, "/api/events") == 0;

    if (events_path && strcmp(method, "POST") == 0) {
        EventInput input;

        if (!event_input_parse(body, &input)) {
            return http_error(400);
        }

        const Event *event = NULL;
        ServiceStatus status = service_create(store, &input, &event);
        event_input_free(&input);

        if (status != SERVICE_OK) {
            return http_error(status);
        }

        if (event == NULL) {
            return http_error(500);
        }

        cJSON *json = event_json(event);

        return json_response(201, json);
    }

    if (events_path) {
        return http_error(405);
    }

    if (strncmp(path, "/api/events/", 12) != 0) {
        return http_error(404);
    }

    const char *event_id = path + 12;

    if (event_id[0] == '\0' || strchr(event_id, '/') != NULL) {
        return http_error(404);
    }

    if (strcmp(method, "GET") == 0) {
        const Event *event = NULL;
        ServiceStatus status = service_read(store, event_id, &event);

        if (status != SERVICE_OK) {
            return http_error(status);
        }

        if (event == NULL) {
            return http_error(500);
        }

        cJSON *json = event_json(event);

