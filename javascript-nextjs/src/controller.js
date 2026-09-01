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

