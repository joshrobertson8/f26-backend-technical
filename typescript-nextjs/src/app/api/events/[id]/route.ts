import { read, update, remove } from "../../../../controller";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface EventParams {
  id: string;
}

