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

