import { store } from "../../../context";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export function GET() {
  const users = Array.from(store.users.values());

  return Response.json(users);
}
