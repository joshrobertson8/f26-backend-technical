import { Event, User } from "./models";

export class MemoryStore {
  events = new Map<string, Event>();
  users = new Map<string, User>();

  private nextId = 1;

  constructor() {
    this.users.set("u1", { id: "u1", name: "Ada" });
    this.users.set("u2", { id: "u2", name: "Grace" });
    this.users.set("u3", { id: "u3", name: "Linus" });
  }

  generateId(): string {
    const eventId = "event-" + this.nextId;
    this.nextId += 1;

    return eventId;
  }
}
