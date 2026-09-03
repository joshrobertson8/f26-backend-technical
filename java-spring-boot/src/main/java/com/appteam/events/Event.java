package com.appteam.events;

import java.util.ArrayList;
import java.util.List;

public class Event {

    public String id;
    public String title;
    public String description;
    public List<String> inviteeIds;

    public Event(String id, String title, String description, List<String> inviteeIds) {
        this.id = id;
        this.title = title;
        this.description = description;
        this.inviteeIds = new ArrayList<>(inviteeIds);
    }
}
