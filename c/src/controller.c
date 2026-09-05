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

