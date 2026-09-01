import { ServiceError } from "./errors.js";
import { EventInput } from "./models.js";

export function parseEventInput(body) {
  if (body === null || typeof body !== "object" || Array.isArray(body)) {
    throw new ServiceError(400, "Expected an event object");
  }

  for (const field in body) {
    if (field !== "title" && field !== "description" && field !== "inviteeIds") {
      throw new ServiceError(400, "Unexpected field: " + field);
    }
  }

  const title = body.title;

