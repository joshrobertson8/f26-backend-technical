import { User } from "./models.js";

export class MemoryStore {
  constructor() {
    this.events = new Map();
    this.users = new Map();
    this.nextId = 1;

