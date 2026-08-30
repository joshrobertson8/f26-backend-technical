export class ServiceError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);

    this.status = status;
  }
}

export class NotImplementedError extends ServiceError {
  constructor() {
    super(501, "Implement the event service");
  }
}
