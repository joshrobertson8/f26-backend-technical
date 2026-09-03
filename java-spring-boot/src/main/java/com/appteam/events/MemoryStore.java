package com.appteam.events;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

@Component
public class MemoryStore {

    public final Map<String, Event> events = new HashMap<>();
    public final Map<String, User> users = new HashMap<>();

    private int nextId = 1;

    public MemoryStore() {
        users.put("u1", new User("u1", "Ada"));
        users.put("u2", new User("u2", "Grace"));
        users.put("u3", new User("u3", "Linus"));
    }

    public String generateId() {
        String eventId = "event-" + nextId;
        nextId += 1;

        return eventId;
    }
}
