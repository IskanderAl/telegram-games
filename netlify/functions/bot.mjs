import { createHash } from "node:crypto";
import { json, safeEqual } from "../lib/auth.mjs";

// Секрет вебхука выводится из токена бота — отдельной переменной окружения не нужно.
// Тот же расчёт делает scripts/setup-bot.mjs при регистрации вебхука.
export const webhookSecret = (botToken) => createHash("sha256").update("webhook:" + botToken).digest("hex");

const SITE = () => (Netlify.env.get("URL") || "https://deluxe-kitten-c78929.netlify.app").replace(/\/$/, "");

async function tg(method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${Netlify.env.get("BOT_TOKEN")}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json().catch(() => null);
}

function gamesMenu(chatId) {
  return {
    chat_id: chatId,
    text: "🎮 Выбери игру:",
    reply_markup: {
      inline_keyboard: [
        [{ text: "🏃 Раннер: Догони его!", web_app: { url: SITE() + "/runner/" } }],
        [{ text: "🔒 Ферма (в разработке)", callback_data: "farm_locked" }],
      ],
    },
  };
}

export default async (req) => {
  if (req.method !== "POST") return json({ ok: true });

  const token = Netlify.env.get("BOT_TOKEN");
  if (!token || !safeEqual(req.headers.get("x-telegram-bot-api-secret-token") || "", webhookSecret(token))) {
    return json({ error: "forbidden" }, 403);
  }

  const update = await req.json().catch(() => null);
  if (!update) return json({ ok: true });

  const msg = update.message;
  if (msg && msg.chat && msg.chat.type === "private" && typeof msg.text === "string") {
    const cmd = msg.text.trim().split(/[\s@]/)[0].toLowerCase();
    if (cmd === "/play" || cmd === "/start") {
      await tg("sendMessage", gamesMenu(msg.chat.id));
    }
  }

  const cb = update.callback_query;
  if (cb && cb.data === "farm_locked") {
    await tg("answerCallbackQuery", { callback_query_id: cb.id, text: "Ферма ещё в разработке 🚧" });
  }

  return json({ ok: true });
};

export const config = { path: "/api/bot" };
