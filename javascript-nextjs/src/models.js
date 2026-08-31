export class User {
  constructor(id, name) {
    this.id = id;
    this.name = name;
  }
}

export class EventInput {
  constructor(title, description = "", inviteeIds = []) {
    this.title = title;
    this.description = description;
    this.inviteeIds = inviteeIds;
  }
}

export class Event extends EventInput {
  constructor(id, title, description = "", inviteeIds = []) {
    super(title, description, inviteeIds);

