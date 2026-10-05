import { getStore } from "@netlify/blobs";
import { json, verifyInitData } from "../lib/auth.mjs";

const MAX_AGE_MS = 10 * 60 * 1000;

// Клиент вызывает после показа рекламы: подтверждаем, что Adsgram действительно прислал награду на /api/reward.
// Награда одноразовая: после подтверждения запись удаляется.
export default async (req) => {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);
  const user = verifyInitData(req.headers.get("x-init-data"), Netlify.env.get("BOT_TOKEN"));
  if (!user) return json({ error: "unauthorized" }, 401);

  const store = getStore("rewards");
  const key = "pending:" + user.id;
  const ts = Number(await store.get(key));
  if (!ts) return json({ ok: false, reason: "no_reward" }, 404);

  await store.delete(key);
  if (Date.now() - ts > MAX_AGE_MS) return json({ ok: false, reason: "expired" }, 410);
  return json({ ok: true });
};

export const config = { path: "/api/claim" };
