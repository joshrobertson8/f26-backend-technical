import { NotImplementedError, ServiceError } from "./errors";
import { Event, EventInput } from "./models";
import { MemoryStore } from "./store";

export class EventService {
  private store: MemoryStore;

  constructor(store: MemoryStore) {
    this.store = store;
  }

  create(data: EventInput): Event {
    throw new NotImplementedError();
  }

  read(eventId: string): Event {
    throw new NotImplementedError();
  }

