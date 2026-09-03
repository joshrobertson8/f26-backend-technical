package com.appteam.events;

import org.springframework.stereotype.Service;

@Service
public class EventService {

    private final MemoryStore store;

    public EventService(MemoryStore store) {
        this.store = store;
    }

    public Event create(EventInput data) {
        throw new UnsupportedOperationException();
    }

