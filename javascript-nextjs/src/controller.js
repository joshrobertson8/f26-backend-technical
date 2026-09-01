import { service } from "./context.js";
import { ServiceError } from "./errors.js";
import { parseEventInput } from "./validation.js";

function errorResponse(error) {
  if (error instanceof ServiceError) {
    return Response.json({ error: error.message }, { status: error.status });
  }

  if (error instanceof SyntaxError) {
    return Response.json({ error: "Malformed JSON" }, { status: 400 });
  }

  console.error(error);

  return Response.json({ error: "Internal server error" }, { status: 500 });
}

export async function create(request) {
  try {
    const body = await request.json();
    const data = parseEventInput(body);
    const event = service.create(data);

    return Response.json(event, { status: 201 });
  } catch (error) {
    return errorResponse(error);
  }
}

export function read(eventId) {
  try {
    const event = service.read(eventId);

    return Response.json(event);
  } catch (error) {
    return errorResponse(error);
  }
}

export async function update(request, eventId) {
  try {
    const body = await request.json();
    const data = parseEventInput(body);
    const event = service.update(eventId, data);

    return Response.json(event);
  } catch (error) {
    return errorResponse(error);
  }
}

export function remove(eventId) {
  try {
    service.delete(eventId);

    return new Response(null, { status: 204 });
  } catch (error) {
    return errorResponse(error);
  }
}
