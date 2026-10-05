// Игры из групповых чатов: параметр запуска "g<id>" (минус в id заменён на "m").
export const groupToken = (chatId) => "g" + String(chatId).replace("-", "m");

export function parseGroupToken(token) {
  const m = /^g(m?\d{1,20})$/.exec(token || "");
  return m ? Number(m[1].replace("m", "-")) : null;
}

export const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export const cleanName = (s, max = 24) =>
  String(s || "").replace(/[\u0000-\u001f]/g, "").trim().slice(0, max);
