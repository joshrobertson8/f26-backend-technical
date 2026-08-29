import express from "express";

import { controller } from "./controller.js";
import { ServiceError } from "./errors.js";
import { EventService } from "./service.js";
import { MemoryStore } from "./store.js";

export function createApp() {
  const app = express();
  const store = new MemoryStore();
  const service = new EventService(store);

