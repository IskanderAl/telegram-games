# Генерирует спрайт перекати-поле (runner/sprites/kz_tumbleweed.png) через sprite-forge.
# Остальные спрайты — текстовые спеки в tools/sprites/*.sprite.txt, собираются командой:
#   python <папка sprite-forge>/forge.py build tools/sprites/<имя>.sprite.txt -o runner/sprites --scale 12
import sys
sys.path.insert(0, r"C:/Users/Usa_f/.claude/skills/sprite-forge")
from forge import Canvas, save_sheet

f = Canvas(16, 16)
c = 7.5
f.ellipse(c, c, 6.3, 6.3, "#6e5224")   # тёмная основа (просветы между прутьями)
f.ellipse(c, c, 5.4, 5.4, "#9a7a3a")
f.ellipse(c, c, 4.0, 4.0, "#6e5224")
f.ellipse(c, c, 3.0, 3.0, "#c9a45a")
f.ellipse(c, c, 1.4, 1.4, "#6e5224")
f.line(2, 4, 13, 11, "#e3c682"); f.line(3, 12, 12, 3, "#c9a45a")   # перекрещенные прутья
f.line(1, 8, 14, 7, "#b08a44"); f.line(7, 1, 8, 14, "#e3c682")
for (x, y) in [(0, 3), (15, 12), (1, 13), (14, 2), (7, 0), (8, 15)]:  # торчащие кончики
    f.set(x, y, "#9a7a3a")
f.outline("#3a2a14")
save_sheet({"idle": f}, "runner/sprites", "kz_tumbleweed", ppu=16)
