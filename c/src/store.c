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

