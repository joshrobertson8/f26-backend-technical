import { service } from "./context";
import { ServiceError } from "./errors";
import { parseEventInput } from "./validation";

function errorResponse(error: unknown) {
  if (error instanceof ServiceError) {
    return Response.json({ error: error.message }, { status: error.status });
  }

  if (error instanceof SyntaxError) {
    return Response.json({ error: "Malformed JSON" }, { status: 400 });
  }

  console.error(error);

  return Response.json({ error: "Internal server error" }, { status: 500 });
}

export async function create(request: Request) {
  try {
    const body = await request.json();
    const data = parseEventInput(body);
    const event = service.create(data);

    return Response.json(event, { status: 201 });
  } catch (error) {
    return errorResponse(error);
  }
}

export function read(eventId: string) {
  try {
    const event = service.read(eventId);

    return Response.json(event);
  } catch (error) {
    return errorResponse(error);
  }
}

export async function update(request: Request, eventId: string) {
  try {
    const body = await request.json();
    const data = parseEventInput(body);
    const event = service.update(eventId, data);

