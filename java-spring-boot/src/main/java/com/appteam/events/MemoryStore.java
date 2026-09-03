package com.appteam.events;

import java.util.HashMap;
import java.util.Map;

import org.springframework.stereotype.Component;

@Component
public class MemoryStore {

    public final Map<String, Event> events = new HashMap<>();
    public final Map<String, User> users = new HashMap<>();

    private int nextId = 1;

