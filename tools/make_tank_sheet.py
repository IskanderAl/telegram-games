"""Собирает лист из двух кадров (езда с подпрыгиванием на 1 px) из готового спрайта танка
и подсказывает хитбокс без ствола для таблицы OBS в runner/index.html.

  python tools/make_tank_sheet.py tools/comfy_t90/cand/e_hand.png runner/sprites/svo_t90.png --scale 2
"""
import argparse

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--scale", type=float, default=2, help="масштаб в игре (для подсказки хитбокса)")
    a = ap.parse_args()

    im = Image.open(a.src).convert("RGBA")
    im = im.crop(im.getbbox())
    w, h = im.size
    fh = h + 1
    while abs(fh * a.scale - round(fh * a.scale)) > 1e-6:  # при дробном масштабе высота кадра должна давать целые пиксели
        fh += 1
    sheet = Image.new("RGBA", (w * 2, fh), (0, 0, 0, 0))
    sheet.alpha_composite(im, (0, fh - h))       # кадр 1: на земле
    sheet.alpha_composite(im, (w, fh - h - 1))   # кадр 2: на 1 px выше
    sheet.save(a.dst)

    # Ствол — тонкая часть слева: столбцы, где непрозрачных пикселей меньше трети высоты корпуса.
    alpha = np.asarray(im)[..., 3] > 0
    col = alpha.sum(0)
    hull = col.max()
    left = int(np.argmax(col >= hull / 3))
    right = int(w - 1 - np.argmax(col[::-1] >= hull / 3))
    rows = alpha[:, left:right + 1].any(1)
    top = int(np.argmax(rows))
    s = a.scale
    print(f"{a.dst}: кадр {w}x{fh}, 2 кадра")
    print(f'SPR:  {{ fw: {w}, fh: {fh}, frames: 2, fps: 5 }}')
    print(f"корпус: столбцы {left}..{right} из {w}, верх корпуса на строке {top} из {h}")
    print(f"OBS inset (l, r, t, b) при scale {s}: "
          f"[{round(left * s) + 4}, {round((w - 1 - right) * s) + 4}, {round((top + fh - h) * s) + 6}, 2]")
    print(f"размер в игре: {w * s:g} x {fh * s:g}")


if __name__ == "__main__":
    main()
