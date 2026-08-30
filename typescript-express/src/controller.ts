import { Router } from "express";

import { EventService } from "./service";
import { MemoryStore } from "./store";
import { parseEventInput } from "./validation";

export function controller(service: EventService, store: MemoryStore): Router {
  const router = Router();

  router.get("/health", (request, response) => {
    response.json({ status: "ok" });
  });

  router.get("/users", (request, response) => {
    const users = Array.from(store.users.values());

    response.json(users);
  });

  router.post("/events", (request, response) => {
    const data = parseEventInput(request.body);
    const event = service.create(data);

    response.status(201).json(event);
  });

  router.get("/events/:id", (request, response) => {
    const eventId = request.params.id;
    const event = service.read(eventId);

    response.json(event);
  });

  router.put("/events/:id", (request, response) => {
    const eventId = request.params.id;
    const data = parseEventInput(request.body);
    const event = service.update(eventId, data);

    response.json(event);
  });

