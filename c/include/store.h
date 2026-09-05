#ifndef STORE_H
#define STORE_H

#include "models.h"
#include "uthash.h"

typedef struct EventEntry {
    Event event;
    UT_hash_handle hh;
} EventEntry;

typedef struct UserEntry {
    User user;
    UT_hash_handle hh;
} UserEntry;

typedef struct {
    EventEntry *events;
    UserEntry *users;
    unsigned long next_id;
} MemoryStore;

bool store_init(MemoryStore *store);

void store_free(MemoryStore *store);

const Event *store_get_event(MemoryStore *store, const char *id);

bool store_set_event(MemoryStore *store, const char *id, const EventInput *data);

