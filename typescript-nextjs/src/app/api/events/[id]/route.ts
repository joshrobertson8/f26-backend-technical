import { read, update, remove } from "../../../../controller";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface EventParams {
  id: string;
}

interface RouteContext {
  params: Promise<EventParams>;
}

export async function GET(request: Request, context: RouteContext) {
  const params = await context.params;

  return read(params.id);
}

export async function PUT(request: Request, context: RouteContext) {
  const params = await context.params;

  return update(request, params.id);
}

export async function DELETE(request: Request, context: RouteContext) {
  const params = await context.params;

  return remove(params.id);
}
