import express from "express";
import { ErrorRequestHandler } from "express";

import { controller } from "./controller";
import { ServiceError } from "./errors";
import { EventService } from "./service";
import { MemoryStore } from "./store";

export function createApp() {
  const app = express();
  const store = new MemoryStore();
  const service = new EventService(store);

  app.use(express.json());
  app.use("/api", controller(service, store));

  const handleError: ErrorRequestHandler = (error, request, response, next) => {
    if (error instanceof ServiceError) {
      response.status(error.status).json({ error: error.message });
      return;
    }

    if (error.type === "entity.parse.failed") {
      response.status(400).json({ error: "Malformed JSON" });
      return;
    }

    console.error(error);

    response.status(500).json({ error: "Internal server error" });
  };

  app.use(handleError);

  return app;
}
