export class ServiceError extends Error {
  constructor(status, message) {
    super(message);

    this.status = status;
  }
}

export class NotImplementedError extends ServiceError {
  constructor() {
    super(501, "Implement the event service");
  }
}
