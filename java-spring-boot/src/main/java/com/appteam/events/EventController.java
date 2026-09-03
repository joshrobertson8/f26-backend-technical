package com.appteam.events;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class EventController {

    private final EventService service;
    private final MemoryStore store;

    public EventController(EventService service, MemoryStore store) {
        this.service = service;
        this.store = store;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok");
    }

    @GetMapping("/users")
    public List<User> users() {
        return new ArrayList<>(store.users.values());
    }

    @PostMapping("/events")
    public ResponseEntity<Event> create(@RequestBody EventInput data) {
        data.validate();

        Event event = service.create(data);

        return ResponseEntity.status(201).body(event);
    }

    @GetMapping("/events/{id}")
    public Event read(@PathVariable String id) {
        return service.read(id);
    }

    @PutMapping("/events/{id}")
    public Event update(@PathVariable String id, @RequestBody EventInput data) {
        data.validate();

        return service.update(id, data);
    }

    @DeleteMapping("/events/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        service.delete(id);

        return ResponseEntity.noContent().build();
    }
}
