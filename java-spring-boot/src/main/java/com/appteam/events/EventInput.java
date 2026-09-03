package com.appteam.events;

import java.util.ArrayList;
import java.util.List;

public class EventInput {

    public String title;
    public String description = "";
    public List<String> inviteeIds = new ArrayList<>();

    public void validate() {
        if (title == null || title.isBlank()) {
            throw new ServiceException(400, "Invalid event body");
        }

