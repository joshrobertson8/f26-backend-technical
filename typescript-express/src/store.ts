import { Event, User } from "./models";

export class MemoryStore {
  events = new Map<string, Event>();
  users = new Map<string, User>();

  private nextId = 1;

