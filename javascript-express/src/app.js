import express from "express";

import { controller } from "./controller.js";
import { ServiceError } from "./errors.js";
import { EventService } from "./service.js";
import { MemoryStore } from "./store.js";

export function createApp() {
  const app = express();
  const store = new MemoryStore();
  const service = new EventService(store);

  app.use(express.json());
  app.use("/api", controller(service, store));

  const handleError = (error, request, response, next) => {
    if (error instanceof ServiceError) {
      response.status(error.status).json({ error: error.message });
      return;
    }

    if (error.type === "entity.parse.failed") {
      response.status(400).json({ error: "Malformed JSON" });
      return;
    }

    console.error(error);

