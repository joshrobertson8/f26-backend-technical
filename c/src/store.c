#include "store.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool store_init(MemoryStore *store) {
    store->events = NULL;
    store->users = NULL;
    store->next_id = 1;

    const User seeds[] = {
        {"u1", "Ada"},
        {"u2", "Grace"},
        {"u3", "Linus"},
    };

    for (size_t i = 0; i < 3; i++) {
        UserEntry *entry = calloc(1, sizeof(*entry));

        if (entry == NULL) {
            store_free(store);
            return false;
        }

        entry->user = seeds[i];
        HASH_ADD_KEYPTR(hh, store->users, entry->user.id, strlen(entry->user.id), entry);
    }

    return true;
}

void store_free(MemoryStore *store) {
    EventEntry *event;
    EventEntry *next_event;

    HASH_ITER(hh, store->events, event, next_event) {
        HASH_DEL(store->events, event);
        free(event->event.id);
        event_input_free(&event->event.data);
        free(event);
    }

    UserEntry *user;
    UserEntry *next_user;

    HASH_ITER(hh, store->users, user, next_user) {
        HASH_DEL(store->users, user);
        free(user);
    }
}

const Event *store_get_event(MemoryStore *store, const char *id) {
    EventEntry *entry = NULL;

    HASH_FIND_STR(store->events, id, entry);

    if (entry == NULL) {
        return NULL;
    }

    return &entry->event;
}

bool store_set_event(MemoryStore *store, const char *id, const EventInput *data) {
    EventEntry *entry = calloc(1, sizeof(*entry));

    if (entry == NULL) {
        return false;
    }

    entry->event.id = copy_string(id);

    if (entry->event.id == NULL || !event_input_copy(&entry->event.data, data)) {
        free(entry->event.id);
        free(entry);
        return false;
    }

    store_remove_event(store, id);
    HASH_ADD_KEYPTR(hh, store->events, entry->event.id, strlen(entry->event.id), entry);

    return true;
}

bool store_remove_event(MemoryStore *store, const char *id) {
    EventEntry *entry = NULL;

    HASH_FIND_STR(store->events, id, entry);

    if (entry == NULL) {
        return false;
    }

