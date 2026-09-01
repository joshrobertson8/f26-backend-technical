import { EventService } from "./service.js";
import { MemoryStore } from "./store.js";

if (globalThis.eventStore === undefined) {
  globalThis.eventStore = new MemoryStore();
}

