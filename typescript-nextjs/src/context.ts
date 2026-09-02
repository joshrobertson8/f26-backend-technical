import { EventService } from "./service";
import { MemoryStore } from "./store";

declare global {
  var eventStore: MemoryStore | undefined;
}

