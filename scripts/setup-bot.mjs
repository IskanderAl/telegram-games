// Настройка бота: вебхук, команды и кнопка меню «Играть».
// Запуск (токен берётся из переменной окружения, в файлах и логах не хранится):
//   BOT_TOKEN=... node scripts/setup-bot.mjs
import { createHash } from "node:crypto";

const token = process.env.BOT_TOKEN;
if (!token) throw new Error("BOT_TOKEN не задан");

const SITE = process.env.SITE_URL || "https://deluxe-kitten-c78929.netlify.app";
const secret = createHash("sha256").update("webhook:" + token).digest("hex"); // как в netlify/functions/bot.mjs

async function call(method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  console.log(method.padEnd(18), data.ok ? "ok" : "ОШИБКА: " + data.description);
  return data;
}

await call("setWebhook", {
  url: SITE + "/api/bot",
  secret_token: secret,
  allowed_updates: ["message", "callback_query"],
  drop_pending_updates: true,
});
await call("setMyCommands", {
  commands: [
    { command: "play", description: "Выбрать игру" },
    { command: "start", description: "Начать" },
  ],
});
await call("setChatMenuButton", {
  menu_button: { type: "web_app", text: "Играть", web_app: { url: SITE + "/" } },
});

const info = await (await fetch(`https://api.telegram.org/bot${token}/getWebhookInfo`)).json();
console.log("webhook url:", info.result && info.result.url, "| ошибок:", info.result && (info.result.last_error_message || "нет"));
