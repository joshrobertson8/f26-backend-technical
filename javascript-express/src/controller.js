import { Router } from "express";

import { parseEventInput } from "./validation.js";

export function controller(service, store) {
  const router = Router();

  router.get("/health", (request, response) => {
    response.json({ status: "ok" });
  });

