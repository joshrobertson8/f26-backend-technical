import { NotImplementedError, ServiceError } from "./errors";
import { Event, EventInput } from "./models";
import { MemoryStore } from "./store";

export class EventService {
  private store: MemoryStore;

