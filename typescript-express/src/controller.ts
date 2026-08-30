import { Router } from "express";

import { EventService } from "./service";
import { MemoryStore } from "./store";
import { parseEventInput } from "./validation";

export function controller(service: EventService, store: MemoryStore): Router {
  const router = Router();

  router.get("/health", (request, response) => {
    response.json({ status: "ok" });
  });

