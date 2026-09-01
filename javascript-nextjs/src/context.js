import { EventService } from "./service.js";
import { MemoryStore } from "./store.js";

if (globalThis.eventStore === undefined) {
  globalThis.eventStore = new MemoryStore();
}

export const store = globalThis.eventStore;
export const service = new EventService(store);
