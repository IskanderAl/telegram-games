import { getStore } from "@netlify/blobs";
import { json, safeEqual } from "../lib/auth.mjs";

// Сюда Adsgram присылает GET после просмотра ролика (Reward URL блока).
// Пример: https://<сайт>/api/reward?userid=[userId]&secret=<REWARD_SECRET>
export default async (req) => {
  const url = new URL(req.url);
  const secret = Netlify.env.get("REWARD_SECRET");
  if (!secret || !safeEqual(url.searchParams.get("secret") || "", secret)) return json({ error: "forbidden" }, 403);

  const uid = url.searchParams.get("userid") || url.searchParams.get("userId") || url.searchParams.get("user_id") || "";
  if (!/^\d{1,20}$/.test(uid)) return json({ error: "bad user" }, 400);

  await getStore({ name: "rewards", consistency: "strong" }).set("pending:" + uid, String(Date.now()));
  return json({ ok: true });
};

export const config = { path: "/api/reward" };
