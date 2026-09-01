import { read, update, remove } from "../../../../controller.js";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request, context) {
  const params = await context.params;

