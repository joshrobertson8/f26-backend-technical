import { Router } from "express";

import { parseEventInput } from "./validation.js";

export function controller(service, store) {
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

