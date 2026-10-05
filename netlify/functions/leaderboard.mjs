import { getStore } from "@netlify/blobs";
import { json, verifyInitData, displayName } from "../lib/auth.mjs";

const MAX_SCORE = 200000; // ~ 44 минут непрерывной игры на максимальной скорости
const KEEP = 100;
const SHOW = 20;

export default async (req) => {
  const user = verifyInitData(req.headers.get("x-init-data"), Netlify.env.get("BOT_TOKEN"));
  const store = getStore({ name: "leaderboard", consistency: "strong" });
  const top = (await store.get("top", { type: "json" })) || [];

  if (req.method === "GET") {
    const myIdx = user ? top.findIndex((e) => e.id === user.id) : -1;
    return json({
      top: top.slice(0, SHOW).map((e, i) => ({ rank: i + 1, name: e.name, score: e.score, me: !!user && e.id === user.id })),
      mine: myIdx >= 0 ? { rank: myIdx + 1, score: top[myIdx].score } : null,
    });
  }

  if (req.method === "POST") {
    if (!user) return json({ error: "unauthorized" }, 401);
    const body = await req.json().catch(() => null);
    const score = Math.floor(Number(body && body.score));
    if (!Number.isFinite(score) || score < 0 || score > MAX_SCORE) return json({ error: "bad score" }, 400);

    const idx = top.findIndex((e) => e.id === user.id);
    if (idx >= 0 && top[idx].score >= score) return json({ ok: true, rank: idx + 1, best: top[idx].score });

    const entry = { id: user.id, name: displayName(user), score };
    if (idx >= 0) top[idx] = entry; else top.push(entry);
    top.sort((a, b) => b.score - a.score);
    const kept = top.slice(0, KEEP);
    await store.setJSON("top", kept);
    const rank = kept.findIndex((e) => e.id === user.id);
    return json({ ok: true, rank: rank >= 0 ? rank + 1 : null, best: score });
  }

  return json({ error: "method not allowed" }, 405);
};

export const config = { path: "/api/leaderboard" };
