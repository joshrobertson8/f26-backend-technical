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

