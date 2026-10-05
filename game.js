"use strict";

// ───────────── Настройки ─────────────
const CONFIG = {
  // Block ID из кабинета Adsgram (partner.adsgram.ai). Пусто = демо-режим с фейковой рекламой.
  ADSGRAM_BLOCK_ID: "",
  SAVE_KEY: "farm_save_v1",
  PLOTS_TOTAL: 9,
  PLOTS_START: 3,
  UNLOCK_BASE: 150,
  UNLOCK_MULT: 4,
  UPGRADE_MULT: 1.5,
  OFFLINE_CAP_SEC: 2 * 3600,
  OFFLINE_RATE: 0.5,
  BOOST_MULT: 2,
  BOOST_SEC: 120,
  AD_BONUS_MINUTES: 10,
  AD_BONUS_COOLDOWN_SEC: 60,
  TAP_UP_BASE: 50,
  TAP_UP_MULT: 2.2,
};

const BUILDINGS = [
  { id: "field",  name: "Грядка",     emoji: "🌾", cost: 15,     income: 0.2 },
  { id: "coop",   name: "Курятник",   emoji: "🐔", cost: 100,    income: 1 },
  { id: "barn",   name: "Коровник",   emoji: "🐄", cost: 500,    income: 4 },
  { id: "mill",   name: "Мельница",   emoji: "🌬️", cost: 2500,   income: 15 },
  { id: "garden", name: "Сад",        emoji: "🍎", cost: 12000,  income: 60 },
  { id: "dairy",  name: "Сыроварня",  emoji: "🧀", cost: 60000,  income: 250 },
  { id: "bakery", name: "Пекарня",    emoji: "🥖", cost: 300000, income: 1100 },
];
const B = Object.fromEntries(BUILDINGS.map((b) => [b.id, b]));

// ───────────── Telegram ─────────────
const tg = window.Telegram && window.Telegram.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try { tg.setHeaderColor("#1f3a1c"); tg.setBackgroundColor("#1f3a1c"); } catch (_) {}
}
const haptic = (kind = "light") => {
  try { tg && tg.HapticFeedback && tg.HapticFeedback.impactOccurred(kind); } catch (_) {}
};

// ───────────── Состояние ─────────────
function newState() {
  return {
    coins: 0,
    plots: Array.from({ length: CONFIG.PLOTS_TOTAL }, () => null),
    unlocked: CONFIG.PLOTS_START,
    tapLevel: 0,
    boostUntil: 0,
    adBonusReadyAt: 0,
    lastSeen: Date.now(),
  };
}

let state = load();

function load() {
  try {
    const raw = localStorage.getItem(CONFIG.SAVE_KEY);
    if (raw) return Object.assign(newState(), JSON.parse(raw));
  } catch (_) {}
  return newState();
}
function save() {
  state.lastSeen = Date.now();
  try { localStorage.setItem(CONFIG.SAVE_KEY, JSON.stringify(state)); } catch (_) {}
}

// ───────────── Формулы ─────────────
const plotIncome = (p) => (p ? B[p.id].income * p.level : 0);
const baseIncome = () => state.plots.reduce((s, p) => s + plotIncome(p), 0);
const boostActive = () => Date.now() < state.boostUntil;
const income = () => baseIncome() * (boostActive() ? CONFIG.BOOST_MULT : 1);
const tapPower = () => 1 + state.tapLevel;
const upgradeCost = (p) => Math.ceil(B[p.id].cost * Math.pow(CONFIG.UPGRADE_MULT, p.level));
const unlockCost = () => Math.ceil(CONFIG.UNLOCK_BASE * Math.pow(CONFIG.UNLOCK_MULT, state.unlocked - CONFIG.PLOTS_START));
const tapUpCost = () => Math.ceil(CONFIG.TAP_UP_BASE * Math.pow(CONFIG.TAP_UP_MULT, state.tapLevel));

function fmt(n) {
  if (n < 1000) return n < 10 && n % 1 ? n.toFixed(1) : Math.floor(n).toString();
  const units = ["K", "M", "B", "T", "Qa"];
  let i = -1;
  while (n >= 1000 && i < units.length - 1) { n /= 1000; i++; }
  return (n < 10 ? n.toFixed(2) : n < 100 ? n.toFixed(1) : Math.floor(n)) + units[i];
}

// ───────────── Элементы ─────────────
const $ = (id) => document.getElementById(id);
const el = {
  coins: $("coins"), rate: $("rate"), boost: $("boost"), boostLeft: $("boost-left"),
  tap: $("tap"), tapPower: $("tap-power"), farm: $("farm"),
  btnAdCoins: $("btn-ad-coins"), adCoinsSub: $("ad-coins-sub"),
  btnAdBoost: $("btn-ad-boost"),
  btnTapUp: $("btn-tap-up"), tapUpSub: $("tap-up-sub"),
  modal: $("modal"), modalTitle: $("modal-title"), modalBody: $("modal-body"), modalClose: $("modal-close"),
  toast: $("toast"),
};

let toastTimer;
function toast(msg) {
  el.toast.textContent = msg;
  el.toast.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.toast.classList.add("hidden"), 2200);
}

function floatText(text, x, y) {
  const d = document.createElement("div");
  d.className = "float";
  d.textContent = text;
  d.style.left = x - 12 + "px";
  d.style.top = y - 20 + "px";
  document.body.appendChild(d);
  setTimeout(() => d.remove(), 800);
}

// ───────────── Действия ─────────────
function spend(cost) {
  if (state.coins < cost) { toast("Не хватает монет 🪙"); return false; }
  state.coins -= cost;
  return true;
}

function build(index, id) {
  if (!spend(B[id].cost)) return;
  state.plots[index] = { id, level: 1 };
  haptic("medium");
  closeModal();
  renderFarm(); save();
}

function upgrade(index) {
  const p = state.plots[index];
  if (!p || !spend(upgradeCost(p))) return;
  p.level++;
  haptic("medium");
  renderFarm(); save();
  openPlot(index);
}

function unlockPlot() {
  if (!spend(unlockCost())) return;
  state.unlocked++;
  haptic("medium");
  closeModal();
  renderFarm(); save();
}

function upgradeTap() {
  if (!spend(tapUpCost())) return;
  state.tapLevel++;
  haptic("medium");
  render(); save();
}

el.tap.addEventListener("click", (e) => {
  const gain = tapPower();
  state.coins += gain;
  haptic("light");
  floatText("+" + fmt(gain), e.clientX, e.clientY);
  renderStats();
});
el.btnTapUp.addEventListener("click", upgradeTap);

// ───────────── Реклама (Adsgram) ─────────────
let adBusy = false;

function showRewardedAd() {
  if (window.Adsgram && CONFIG.ADSGRAM_BLOCK_ID) {
    const controller = window.Adsgram.init({ blockId: CONFIG.ADSGRAM_BLOCK_ID });
    // resolve — досмотрел, reject — пропустил или ошибка/нет рекламы
    return controller.show().then(() => true, () => false);
  }
  return demoAd();
}

// Демо-режим для локальной разработки, когда blockId не задан
function demoAd() {
  return new Promise((resolve) => {
    const d = document.createElement("div");
    d.className = "demo-ad";
    let left = 3;
    d.innerHTML = '<div style="font-size:48px">📺</div><div>Демо-реклама (задайте ADSGRAM_BLOCK_ID)</div><div id="demo-left"></div>';
    document.body.appendChild(d);
    const tick = () => {
      d.querySelector("#demo-left").textContent = "Награда через " + left + " c";
      if (left-- <= 0) { d.remove(); resolve(true); } else setTimeout(tick, 1000);
    };
    tick();
  });
}

async function watchAd(onReward) {
  if (adBusy) return;
  adBusy = true;
  try {
    const ok = await showRewardedAd();
    if (ok) { onReward(); haptic("heavy"); render(); save(); }
    else toast("Реклама недоступна или пропущена — награды нет");
  } finally {
    adBusy = false;
  }
}

el.btnAdCoins.addEventListener("click", () => {
  const wait = Math.ceil((state.adBonusReadyAt - Date.now()) / 1000);
  if (wait > 0) return toast("Следующий бонус через " + wait + " c");
  watchAd(() => {
    const gain = Math.max(100, baseIncome() * 60 * CONFIG.AD_BONUS_MINUTES);
    state.coins += gain;
    state.adBonusReadyAt = Date.now() + CONFIG.AD_BONUS_COOLDOWN_SEC * 1000;
    toast("🎁 +" + fmt(gain) + " монет");
  });
});

el.btnAdBoost.addEventListener("click", () => {
  watchAd(() => {
    state.boostUntil = Math.max(Date.now(), state.boostUntil) + CONFIG.BOOST_SEC * 1000;
    toast("⚡ Доход x" + CONFIG.BOOST_MULT + " включён");
  });
});

// ───────────── Модальное окно ─────────────
function openModal(title) {
  el.modalTitle.textContent = title;
  el.modalBody.innerHTML = "";
  el.modal.classList.remove("hidden");
}
function closeModal() { el.modal.classList.add("hidden"); }
el.modalClose.addEventListener("click", closeModal);
el.modal.addEventListener("click", (e) => { if (e.target === el.modal) closeModal(); });

function row(emoji, name, desc, btnText, disabled, onClick) {
  const r = document.createElement("div");
  r.className = "row";
  r.innerHTML = '<div class="emoji"></div><div class="info"><b></b><div></div></div><button type="button"></button>';
  r.querySelector(".emoji").textContent = emoji;
  r.querySelector("b").textContent = name;
  r.querySelector(".info div").textContent = desc;
  const btn = r.querySelector("button");
  btn.textContent = btnText;
  btn.disabled = disabled;
  btn.addEventListener("click", onClick);
  return r;
}

function openPlot(index) {
  const p = state.plots[index];
  if (index >= state.unlocked) {
    const cost = unlockCost();
    openModal("Расширить участок");
    el.modalBody.appendChild(row("🔓", "Новый участок", "Место для ещё одного здания", "🪙 " + fmt(cost), state.coins < cost, unlockPlot));
    return;
  }
  if (!p) {
    openModal("Построить здание");
    BUILDINGS.forEach((b) => {
      el.modalBody.appendChild(
        row(b.emoji, b.name, "+" + fmt(b.income) + " монет/сек", "🪙 " + fmt(b.cost), state.coins < b.cost, () => build(index, b.id))
      );
    });
    return;
  }
  const b = B[p.id];
  const cost = upgradeCost(p);
  openModal(b.emoji + " " + b.name);
  el.modalBody.appendChild(
    row(b.emoji, "Уровень " + p.level,
      fmt(plotIncome(p)) + " → " + fmt(b.income * (p.level + 1)) + " монет/сек",
      "⬆ " + fmt(cost), state.coins < cost, () => upgrade(index))
  );
}

// ───────────── Отрисовка ─────────────
function renderFarm() {
  el.farm.innerHTML = "";
  state.plots.forEach((p, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "plot";
    if (i >= state.unlocked) {
      btn.classList.add("locked");
      btn.innerHTML = '<span class="emoji">🔒</span><span class="inc"></span>';
      btn.querySelector(".inc").textContent = i === state.unlocked ? "🪙 " + fmt(unlockCost()) : "";
    } else if (!p) {
      btn.classList.add("empty");
      btn.innerHTML = '<span class="emoji">➕</span><span class="inc">Построить</span>';
    } else {
      btn.classList.add("built");
      if (state.coins >= upgradeCost(p)) btn.classList.add("can-upgrade");
      btn.innerHTML = '<span class="emoji"></span><span class="lvl"></span><span class="inc"></span>';
      btn.querySelector(".emoji").textContent = B[p.id].emoji;
      btn.querySelector(".lvl").textContent = "Ур. " + p.level;
      btn.querySelector(".inc").textContent = fmt(plotIncome(p)) + "/с";
    }
    btn.addEventListener("click", () => openPlot(i));
    el.farm.appendChild(btn);
  });
}

function renderStats() {
  el.coins.textContent = fmt(state.coins);
  el.rate.firstChild.textContent = fmt(income());
  el.tapPower.textContent = fmt(tapPower());
  el.tapUpSub.textContent = "🪙 " + fmt(tapUpCost());
  el.btnTapUp.disabled = state.coins < tapUpCost();

  const active = boostActive();
  el.boost.classList.toggle("hidden", !active);
  if (active) el.boostLeft.textContent = Math.ceil((state.boostUntil - Date.now()) / 1000) + "с";

  const wait = Math.ceil((state.adBonusReadyAt - Date.now()) / 1000);
  el.adCoinsSub.textContent = wait > 0 ? "через " + wait + " c" : "+" + fmt(Math.max(100, baseIncome() * 60 * CONFIG.AD_BONUS_MINUTES));
}

function render() { renderFarm(); renderStats(); }

// ───────────── Игровой цикл ─────────────
let last = performance.now();
let sinceFarmRender = 0;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 1);
  last = now;
  state.coins += income() * dt;
  renderStats();

  sinceFarmRender += dt;
  if (sinceFarmRender >= 1 && el.modal.classList.contains("hidden")) {
    sinceFarmRender = 0;
    renderFarm(); // обновляет подсветку «можно улучшить»
  }
  requestAnimationFrame(loop);
}

// ───────────── Оффлайн-доход ─────────────
function applyOffline() {
  const away = Math.min((Date.now() - state.lastSeen) / 1000, CONFIG.OFFLINE_CAP_SEC);
  const gain = baseIncome() * away * CONFIG.OFFLINE_RATE;
  if (away > 30 && gain >= 1) {
    state.coins += gain;
    toast("🌙 Пока вас не было: +" + fmt(gain) + " монет");
  }
}

setInterval(save, 5000);
document.addEventListener("visibilitychange", () => { if (document.hidden) save(); });
window.addEventListener("pagehide", save);

applyOffline();
render();
requestAnimationFrame(loop);
