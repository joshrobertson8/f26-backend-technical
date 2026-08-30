import { ServiceError } from "./errors";
import { EventInput } from "./models";

export function parseEventInput(body: any): EventInput {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    throw new ServiceError(400, "Expected an event object");
  }

  for (const field in body) {
    if (field !== "title" && field !== "description" && field !== "inviteeIds") {
      throw new ServiceError(400, "Unexpected field: " + field);
    }
  }

  const title = body.title;

