import { createHmac, timingSafeEqual } from "node:crypto";

export const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });

export function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  const x = Buffer.from(a);
  const y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}

// Проверка подписи Telegram WebApp initData (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
// Возвращает объект пользователя или null, если подпись неверна / данные устарели.
export function verifyInitData(initData, botToken, maxAgeSec = 24 * 3600) {
  if (!initData || !botToken) return null;
  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) return null;
  params.delete("hash");

  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");

  const secret = createHmac("sha256", "WebAppData").update(botToken).digest();
  const calc = createHmac("sha256", secret).update(dataCheckString).digest("hex");
  if (!safeEqual(calc, hash)) return null;

  const authDate = Number(params.get("auth_date"));
  if (!authDate || Date.now() / 1000 - authDate > maxAgeSec) return null;

  try {
    const user = JSON.parse(params.get("user"));
    // start_param входит в подписанные данные, подделать его нельзя
    return user && Number.isInteger(user.id) ? { ...user, start_param: params.get("start_param") || "" } : null;
  } catch {
    return null;
  }
}

export function displayName(user) {
  const raw = user.first_name || user.username || "Игрок";
  return String(raw).replace(/[\u0000-\u001f<>]/g, "").trim().slice(0, 24) || "Игрок";
}
