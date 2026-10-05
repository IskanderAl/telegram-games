import { getStore } from "@netlify/blobs";
import { json, verifyInitData, displayName } from "../lib/auth.mjs";
import { parseGroupToken, esc, cleanName } from "../lib/groups.mjs";

const MAX_SCORE = 200000;
const THROTTLE_MS = 20 * 1000;   // не чаще одного сообщения в 20 секунд от игрока в группе
const MAX_IMAGE_B64 = 600_000;   // ~450 КБ

async function tg(method, body) {
  const headers = typeof body === "string" ? { "content-type": "application/json" } : undefined; // FormData ставит свой
  const res = await fetch(`https://api.telegram.org/bot${Netlify.env.get("BOT_TOKEN")}/${method}`, { method: "POST", headers, body });
  return res.json().catch(() => null);
}

export default async (req) => {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  const user = verifyInitData(req.headers.get("x-init-data"), Netlify.env.get("BOT_TOKEN"));
  if (!user) return json({ error: "unauthorized" }, 401);

  const chatId = parseGroupToken(user.start_param);
  if (chatId === null) return json({ posted: false, reason: "no_group" });

  // Пишем только в группы, где бот сам видел команду /play или своё добавление — произвольный id подставить нельзя
  const groups = getStore({ name: "groups", consistency: "strong" });
  if (!(await groups.get("g:" + user.start_param))) return json({ posted: false, reason: "unregistered" });

  const b = await req.json().catch(() => null);
  const score = Math.floor(Number(b && b.score));
  const gap = Math.floor(Number(b && b.gap));
  if (!Number.isFinite(score) || score < 0 || score > MAX_SCORE || !Number.isFinite(gap) || gap < 1 || gap > 1000) {
    return json({ error: "bad data" }, 400);
  }
  // Игрок сам нажимает «Опубликовать»; защищаемся только от частых повторов
  const lastKey = `last:${user.start_param}:${user.id}`;
  const last = Number(await groups.get(lastKey)) || 0;
  if (Date.now() - last < THROTTLE_MS) return json({ posted: false, reason: "throttled" });

  const who = displayName(user);
  const role = cleanName(b.playerName);
  const target = cleanName(b.targetName);
  const lines = [];
  lines.push(
    `🏃 <b>${esc(who)}</b>` +
      (role ? ` был(а) «${esc(role)}»` : " бежал(а)") +
      (target ? ` и догонял(а) «${esc(target)}»` : " за недосягаемой целью")
  );
  lines.push(`Не догнал(а) всего на <b>${gap} м</b>! Счёт: <b>${score}</b>`);
  const caption = lines.join("\n");

  const image = typeof b.image === "string" && b.image.length <= MAX_IMAGE_B64 && /^[A-Za-z0-9+/=]+$/.test(b.image) ? b.image : null;
  let sent = null;
  if (image) {
    const form = new FormData();
    form.set("chat_id", String(chatId));
    form.set("caption", caption);
    form.set("parse_mode", "HTML");
    form.set("photo", new Blob([Buffer.from(image, "base64")], { type: "image/jpeg" }), "result.jpg");
    sent = await tg("sendPhoto", form);
  }
  if (!sent || !sent.ok) {
    sent = await tg("sendMessage", JSON.stringify({ chat_id: chatId, text: caption, parse_mode: "HTML" }));
  }
  const posted = !!(sent && sent.ok);
  if (posted) await groups.set(lastKey, String(Date.now()));
  return json({ posted });
};

export const config = { path: "/api/group-result" };
