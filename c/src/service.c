#include "service.h"

ServiceStatus service_create(MemoryStore *store, const EventInput *data, const Event **out) {
    return SERVICE_NOT_IMPLEMENTED;
}

ServiceStatus service_read(MemoryStore *store, const char *event_id, const Event **out) {
    return SERVICE_NOT_IMPLEMENTED;
}

ServiceStatus service_update(MemoryStore *store, const char *event_id, const EventInput *data,
                            const Event **out) {
    return SERVICE_NOT_IMPLEMENTED;
}

ServiceStatus service_delete(MemoryStore *store, const char *event_id) {
    return SERVICE_NOT_IMPLEMENTED;
}
