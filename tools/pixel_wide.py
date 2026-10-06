#!/usr/bin/env python3
"""Пикселизация картинки из ComfyUI с сохранением пропорций.

`comfy.py pixelize` из скилла comfy-gen сначала сжимает кадр в квадрат, поэтому широкие
предметы (танк на кадре 1344x768) выходят сплющенными. Этот скрипт делает то же самое
(убирает фон, обрезает, уменьшает, сводит палитру), но пропорции не трогает.

Запуск питоном ComfyUI (в нём есть Pillow и numpy):
  P:/ComfyUI/ComfyUI_windows_portable/python_embeded/python.exe tools/pixel_wide.py src.png \
      --width 96 --colors 24 --flip --outline "#1d2210" -o out.png
"""
import argparse
from collections import Counter, deque

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def background_mask(img, tol, shadow_lum):
    """True там, где фон: заливка от краёв кадра по пикселям, похожим на цвет фона."""
    w, h = img.size
    px = img.load()
    border = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] \
        + [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
    bg = Counter((r // 8 * 8, g // 8 * 8, b // 8 * 8) for r, g, b in border).most_common(1)[0][0]
    tol2 = tol * tol

    def is_bg(c):
        if sum((c[k] - bg[k]) ** 2 for k in range(3)) <= tol2:
            return True
        # светлая серая тень, примыкающая к фону, тоже фон (тёмные гусеницы не задевает)
        return shadow_lum > 0 and max(c) - min(c) < 22 and sum(c) / 3 >= shadow_lum

    mask = np.zeros((h, w), dtype=bool)
    dq = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while dq:
        x, y = dq.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or mask[y, x] or not is_bg(px[x, y]):
            continue
        mask[y, x] = True
        dq.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return mask, bg


def remove_holes(img, mask, bg, tol, min_px):
    """Замкнутые участки цвета фона (просвет между ногами, между рукой и корпусом) — тоже фон.
    До них заливка от краёв не доходит. Мелкие участки (блики) не трогаем."""
    w, h = img.size
    px = img.load()
    tol2 = tol * tol
    near = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if not mask[y, x]:
                c = px[x, y]
                near[y, x] = sum((c[k] - bg[k]) ** 2 for k in range(3)) <= tol2
    seen = np.zeros_like(near)
    for sy in range(h):
        for sx in range(w):
            if not near[sy, sx] or seen[sy, sx]:
                continue
            comp, dq = [], deque([(sx, sy)])
            seen[sy, sx] = True
            while dq:
                x, y = dq.popleft()
                comp.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and near[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        dq.append((nx, ny))
            if len(comp) >= min_px:
                for x, y in comp:
                    mask[y, x] = True
    return mask


def drop_islands(opaque, min_px):
    """Убирает отдельные кусочки меньше min_px пикселей (мусор после удаления фона)."""
    h, w = opaque.shape
    seen = np.zeros_like(opaque)
    for sy in range(h):
        for sx in range(w):
            if not opaque[sy, sx] or seen[sy, sx]:
                continue
            comp, dq = [], deque([(sx, sy)])
            seen[sy, sx] = True
            while dq:
                x, y = dq.popleft()
                comp.append((x, y))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and opaque[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            dq.append((nx, ny))
            if len(comp) < min_px:
                for x, y in comp:
                    opaque[y, x] = False
    return opaque


def resize_premultiplied(rgb, alpha, size):
    """Уменьшение с учётом прозрачности: цвет фона не подмешивается в края."""
    a = alpha.astype(np.float32) / 255.0
    chans = []
    for i in range(3):
        pm = Image.fromarray(rgb[..., i].astype(np.float32) * a, mode="F").resize(size, Image.BOX)
        chans.append(np.asarray(pm))
    a_s = np.asarray(Image.fromarray(a, mode="F").resize(size, Image.BOX))
    out = np.stack(chans, axis=-1) / np.maximum(a_s, 1e-4)[..., None]
    return np.clip(out, 0, 255), a_s


def quantize(rgb, opaque, colors):
    """Палитра из colors цветов по непрозрачным пикселям, без дизеринга."""
    pts = rgb[opaque].astype(np.uint8)
    strip = Image.fromarray(pts.reshape(1, -1, 3), mode="RGB")
    pal_img = strip.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(pal_img.getpalette()[: colors * 3], dtype=np.float32).reshape(-1, 3)
    flat = rgb.reshape(-1, 3).astype(np.float32)
    idx = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(-1).argmin(1)
    return pal[idx].reshape(rgb.shape).astype(np.uint8)


def add_outline(rgba, color):
    """Контур в 1 пиксель снаружи силуэта (как у спрайтов sprite-forge)."""
    h, w = rgba.shape[:2]
    out = np.zeros((h + 2, w + 2, 4), dtype=np.uint8)
    out[1:-1, 1:-1] = rgba
    op = out[..., 3] > 0
    ring = np.zeros_like(op)
    ring[1:, :] |= op[:-1, :]
    ring[:-1, :] |= op[1:, :]
    ring[:, 1:] |= op[:, :-1]
    ring[:, :-1] |= op[:, 1:]
    ring &= ~op
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    out[ring] = (r, g, b, 255)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("--width", type=int, default=96, help="ширина спрайта в пикселях (высота по пропорции)")
    ap.add_argument("--height", type=int, default=0, help="задать высоту вместо ширины (для фигур в рост)")
    ap.add_argument("--colors", type=int, default=24)
    ap.add_argument("--tol", type=int, default=40, help="допуск цвета фона")
    ap.add_argument("--shadow", type=int, default=175, help="светлые серые пиксели ярче этого считаются тенью (0 = выкл.)")
    ap.add_argument("--work", type=int, default=4, help="во сколько раз уменьшать кадр для поиска фона")
    ap.add_argument("--min-island", type=int, default=6)
    ap.add_argument("--holes", type=int, default=0,
                    help="убирать замкнутые участки цвета фона от N пикселей (в уменьшенном кадре); 0 = выкл.")
    ap.add_argument("--sat", type=float, default=1.0, help="насыщенность (1 = без изменений)")
    ap.add_argument("--bright", type=float, default=1.0)
    ap.add_argument("--flip", action="store_true", help="отзеркалить по горизонтали")
    ap.add_argument("--outline", default="", help="цвет контура, например #1d2210 (пусто = без контура)")
    a = ap.parse_args()

    src = Image.open(a.src).convert("RGB")
    if a.sat != 1.0:
        src = ImageEnhance.Color(src).enhance(a.sat)
    if a.bright != 1.0:
        src = ImageEnhance.Brightness(src).enhance(a.bright)

    k = max(1, a.work)
    work = src.resize((src.width // k, src.height // k), Image.BOX)
    bgm, bg = background_mask(work, a.tol, a.shadow)
    if a.holes:
        bgm = remove_holes(work, bgm, bg, min(a.tol, 28), a.holes)
    alpha_work = Image.fromarray(np.where(bgm, 0, 255).astype(np.uint8), mode="L")
    bbox = alpha_work.getbbox()
    if not bbox:
        raise SystemExit("после удаления фона ничего не осталось: уменьши --tol или --shadow")

    full_box = tuple(v * k for v in bbox)
    crop = np.asarray(src.crop(full_box))
    acrop = np.asarray(alpha_work.crop(bbox).resize((crop.shape[1], crop.shape[0]), Image.NEAREST))

    if a.height:
        h = a.height
        w = max(1, round(crop.shape[1] * h / crop.shape[0]))
    else:
        w = a.width
        h = max(1, round(crop.shape[0] * w / crop.shape[1]))
    rgb, a_s = resize_premultiplied(crop, acrop, (w, h))
    opaque = drop_islands(a_s >= 0.5, a.min_island)
    rgb = quantize(rgb, opaque, a.colors)

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = np.where(opaque, 255, 0)
    if a.outline:
        rgba = add_outline(rgba, a.outline)
    out = Image.fromarray(rgba, mode="RGBA")
    out = out.crop(out.getbbox())
    if a.flip:
        out = ImageOps.mirror(out)

    dst = a.out or a.src.replace(".png", f"_w{w}.png")
    out.save(dst)
    print(f"{dst}: {out.width}x{out.height}")


if __name__ == "__main__":
    main()
