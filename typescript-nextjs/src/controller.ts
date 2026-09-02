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

