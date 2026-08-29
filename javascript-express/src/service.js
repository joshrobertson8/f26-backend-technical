import { NotImplementedError, ServiceError } from "./errors.js";
import { Event, EventInput } from "./models.js";

export class EventService {
  constructor(store) {
    this.store = store;
  }

  create(data) {
    throw new NotImplementedError();
  }

  read(eventId) {
    throw new NotImplementedError();
  }

  update(eventId, data) {
    throw new NotImplementedError();
  }

  delete(eventId) {
    throw new NotImplementedError();
  }
}
