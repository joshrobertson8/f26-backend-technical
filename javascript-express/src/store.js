import { User } from "./models.js";

export class MemoryStore {
  constructor() {
    this.events = new Map();
    this.users = new Map();
    this.nextId = 1;

    this.users.set("u1", new User("u1", "Ada"));
    this.users.set("u2", new User("u2", "Grace"));
    this.users.set("u3", new User("u3", "Linus"));
  }

  generateId() {
    const eventId = "event-" + this.nextId;
    this.nextId += 1;

    return eventId;
  }
}
