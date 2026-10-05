import { createHash } from "node:crypto";
import { getStore } from "@netlify/blobs";
import { json, safeEqual } from "../lib/auth.mjs";
import { groupToken } from "../lib/groups.mjs";

const BOT_USERNAME = "dream_runnerbot";
const GAME_SHORT_NAME = "runner";

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

const isGroup = (chat) => chat && (chat.type === "group" || chat.type === "supergroup");

// В группах web_app-кнопки недоступны, поэтому открываем игру прямой ссылкой с пометкой группы.
// Бот запоминает группу: результаты можно отправлять только в известные ему чаты.
async function greetGroup(chat) {
  const token = groupToken(chat.id);
  await getStore({ name: "groups", consistency: "strong" }).set("g:" + token, String(chat.id));
  return tg("sendMessage", {
    chat_id: chat.id,
    text: "🏃 Играем в «Догони его!» После забега нажми «Опубликовать в группе» — здесь появится карточка: кем ты был и кого догонял.",
    reply_markup: {
      inline_keyboard: [[{ text: "🏃 Играть", url: `https://t.me/${BOT_USERNAME}/${GAME_SHORT_NAME}?startapp=${token}` }]],
    },
  });
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
  if (msg && msg.chat && typeof msg.text === "string") {
    const [first] = msg.text.trim().split(/\s+/);
    const [cmd, target] = first.toLowerCase().split("@");
    const forUs = !target || target === BOT_USERNAME;
    if (forUs && (cmd === "/play" || cmd === "/start")) {
      if (msg.chat.type === "private") await tg("sendMessage", gamesMenu(msg.chat.id));
      else if (isGroup(msg.chat)) await greetGroup(msg.chat);
    }
  }

  // Бота добавили в группу
  const mcm = update.my_chat_member;
  if (mcm && isGroup(mcm.chat) && ["member", "administrator"].includes(mcm.new_chat_member && mcm.new_chat_member.status)) {
    await greetGroup(mcm.chat);
  }

  const cb = update.callback_query;
  if (cb && cb.data === "farm_locked") {
    await tg("answerCallbackQuery", { callback_query_id: cb.id, text: "Ферма ещё в разработке 🚧" });
  }

  return json({ ok: true });
};

export const config = { path: "/api/bot" };
