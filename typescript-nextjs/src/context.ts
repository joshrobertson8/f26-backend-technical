import { EventService } from "./service";
import { MemoryStore } from "./store";

declare global {
  var eventStore: MemoryStore | undefined;
}

if (globalThis.eventStore === undefined) {
  globalThis.eventStore = new MemoryStore();
}

export const store = globalThis.eventStore;
export const service = new EventService(store);
