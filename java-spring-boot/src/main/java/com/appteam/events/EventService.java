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

    public Event read(String eventId) {
        throw new UnsupportedOperationException();
    }

    public Event update(String eventId, EventInput data) {
        throw new UnsupportedOperationException();
    }

    public void delete(String eventId) {
        throw new UnsupportedOperationException();
    }
}
