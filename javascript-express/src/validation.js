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

  if (typeof title !== "string" || title.trim() === "") {
    throw new ServiceError(400, "title must be a nonempty string");
  }

  let description = body.description;

  if (description === undefined) {
    description = "";
  }

  if (typeof description !== "string") {
    throw new ServiceError(400, "description must be a string");
  }

  let invitees = body.inviteeIds;

  if (invitees === undefined) {
    invitees = [];
  }

  if (!Array.isArray(invitees)) {
    throw new ServiceError(400, "inviteeIds must be a list");
  }

  const inviteeIds = [];

  for (const id of invitees) {
    if (typeof id !== "string") {
      throw new ServiceError(400, "Each invitee ID must be a string");
    }

    inviteeIds.push(id);
  }

  return new EventInput(title, description, inviteeIds);
}
