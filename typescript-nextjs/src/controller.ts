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

