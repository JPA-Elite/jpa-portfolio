import { rm } from "node:fs/promises";
import { join } from "node:path";

export default async function globalTeardown() {
  await rm(join(process.cwd(), "app", "logs", "recent_activity.jsonl"), {
    force: true,
  });
}
