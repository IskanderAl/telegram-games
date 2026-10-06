"""Сравнительный лист спрайтов на фоне руин (как в стиле «СВО»): python compare_sprites.py out.png scale a.png b.png ..."""
import sys
from PIL import Image, ImageDraw

out, scale, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert("RGBA") for f in files]
cw = max(i.width for i in ims) * scale + 40
ch = max(i.height for i in ims) * scale + 70
cols = 2
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGBA", (cw * cols, ch * rows), (222, 220, 203, 255))
d = ImageDraw.Draw(sheet)
for n, (f, im) in enumerate(zip(files, ims)):
    x0, y0 = (n % cols) * cw, (n // cols) * ch
    ground = y0 + ch - 20
    for k in range(cw // 56 + 1):  # силуэты руин, как в игре
        h = 30 + ((k * 37) % 5) * 14
        d.rectangle([x0 + k * 56, ground - h, x0 + k * 56 + 48, ground], fill=(196, 195, 174, 255))
    d.rectangle([x0, ground, x0 + cw, ground + 2], fill=(58, 63, 38, 255))
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    sheet.alpha_composite(big, (x0 + (cw - big.width) // 2, ground - big.height))
    d.text((x0 + 8, y0 + 6), f"{f.split('/')[-1]}  {im.width}x{im.height}", fill=(0, 0, 0, 255))
sheet.convert("RGB").save(out)
print(out, sheet.size)
