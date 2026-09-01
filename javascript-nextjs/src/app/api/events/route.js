import { create } from "../../../controller.js";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request) {
  return create(request);
}
