"""Укорачивает ствол танка, вырезая столбцы ровной трубы (шва не видно).

  python tools/shorten_gun.py src.png dst.png 5:16 31:36
Каждый аргумент a:b — вырезать столбцы a..b-1.
"""
import sys

from PIL import Image

src, dst, *cuts = sys.argv[1:]
im = Image.open(src).convert("RGBA")
drop = set()
for c in cuts:
    a, b = map(int, c.split(":"))
    drop.update(range(a, b))
keep = [x for x in range(im.width) if x not in drop]
out = Image.new("RGBA", (len(keep), im.height), (0, 0, 0, 0))
for nx, x in enumerate(keep):
    out.paste(im.crop((x, 0, x + 1, im.height)), (nx, 0))
out.save(dst)
print(f"{dst}: {im.width} -> {out.width} px")
