"""Силуэт Т-90 в профиль по реальным размерам — основа для img2img в ComfyUI.

Размеры Т-90А: длина корпуса 6.86 м, с пушкой вперёд 9.53 м, высота по крыше башни 2.23 м,
6 опорных катков на борт, ведущее колесо сзади, ленивец спереди, резиновые бортовые экраны.
Пушка смотрит влево (как препятствие в раннере). Фон белый — его потом удаляет пикселизатор.

  python tools/t90_base.py out.png
"""
import sys
from PIL import Image, ImageDraw

W, H = 1344, 768
S = 131.0       # пикселей на метр
X0 = 380        # нос корпуса
GY = 640        # земля


def P(u, h):
    """u — метры от носа корпуса назад, h — метры над землёй."""
    return (X0 + u * S, GY - h * S)


def rect(d, u0, h0, u1, h1, fill, outline=None, width=1):
    (x0, y0), (x1, y1) = P(u0, h0), P(u1, h1)
    d.rectangle([min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)], fill=fill, outline=outline, width=width)


def circle(d, u, h, r, fill, outline=None, width=1):
    x, y = P(u, h)
    d.ellipse([x - r * S, y - r * S, x + r * S, y + r * S], fill=fill, outline=outline, width=width)


def poly(d, pts, fill, outline=None):
    d.polygon([P(u, h) for u, h in pts], fill=fill, outline=outline)


C = dict(
    base=(74, 88, 42), light=(104, 120, 60), top=(122, 138, 72), dark=(50, 60, 28), darker=(34, 41, 19),
    track=(40, 40, 37), rubber=(26, 26, 26), hub=(86, 98, 52), steel=(72, 74, 68), era=(90, 106, 52),
    lens=(180, 40, 30),
)


def draw(path):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # гусеница
    poly(d, [(0.25, 0.55), (0.75, 0.0), (6.05, 0.0), (6.55, 0.5), (6.55, 0.75), (6.2, 0.9), (0.6, 0.9), (0.2, 0.75)], C["track"])
    for i in range(46):  # траки
        x, _ = P(0.75 + i * 0.115, 0)
        d.line([x, GY - 4, x, GY], fill=C["rubber"], width=3)

    # 6 опорных катков, ленивец и ведущее колесо
    for i in range(6):
        u = 1.05 + i * 0.95
        circle(d, u, 0.4, 0.37, C["rubber"])
        circle(d, u, 0.4, 0.30, C["hub"], outline=C["dark"], width=3)
        circle(d, u, 0.4, 0.11, C["dark"])
    circle(d, 0.45, 0.55, 0.27, C["steel"], outline=C["rubber"], width=4)
    circle(d, 6.3, 0.55, 0.30, C["steel"], outline=C["rubber"], width=4)
    for k in range(8):  # зубья ведущего колеса
        import math
        a = k * math.pi / 4
        x, y = P(6.3 + 0.3 * math.cos(a), 0.55 + 0.3 * math.sin(a))
        d.rectangle([x - 6, y - 6, x + 6, y + 6], fill=C["rubber"])

    # корпус: нос, верхний лобовой лист, надгусеничные полки, корма
    poly(d, [(0.0, 1.02), (1.7, 1.48), (6.86, 1.48), (6.86, 0.9), (0.3, 0.9)], C["base"])
    poly(d, [(0.0, 1.02), (1.7, 1.48), (1.75, 1.42), (0.12, 0.98)], C["top"])
    for k in range(6):  # блоки динамической защиты на лобовом листе
        t = 0.08 + k * 0.15
        u, h = 0.0 + 1.7 * t, 1.02 + 0.46 * t
        poly(d, [(u, h + 0.02), (u + 0.2, h + 0.075), (u + 0.24, h - 0.04), (u + 0.04, h - 0.1)], C["era"], outline=C["dark"])
    rect(d, 1.7, 1.48, 6.86, 1.42, C["top"])               # кромка крыши корпуса
    for k in range(9):                                     # решётки МТО на корме
        u = 4.7 + k * 0.22
        d.line([P(u, 1.46), P(u + 0.12, 1.46)], fill=C["dark"], width=3)

    # бортовой резиновый экран поверх верхней части катков
    poly(d, [(0.15, 0.97), (6.7, 0.97), (6.7, 0.62), (0.4, 0.62)], C["dark"])
    for k in range(1, 7):
        x, _ = P(0.4 + k * 0.92, 0)
        d.line([(x, GY - 0.97 * S), (x, GY - 0.62 * S)], fill=C["darker"], width=3)
    for k in range(3):                                     # передние экраны с ДЗ
        rect(d, 0.45 + k * 0.42, 0.93, 0.82 + k * 0.42, 0.68, C["era"], outline=C["darker"], width=2)
    rect(d, 0.15, 0.99, 6.7, 0.95, C["light"])             # кромка полки

    # топливные бочки и бревно самовытаскивания на корме
    circle(d, 6.98, 1.22, 0.28, C["base"], outline=C["darker"], width=4)
    circle(d, 6.98, 1.22, 0.17, C["light"], outline=C["dark"], width=3)
    rect(d, 6.6, 1.62, 7.08, 1.5, C["steel"], outline=C["darker"], width=2)

    # башня: клиновидный лоб с ДЗ, низкая крыша, кормовая ниша с ЗИП
    poly(d, [(1.95, 1.48), (2.05, 1.78), (2.45, 2.18), (4.0, 2.24), (4.35, 2.05), (4.5, 1.62), (4.3, 1.48)], C["base"])
    poly(d, [(2.45, 2.18), (4.0, 2.24), (3.98, 2.18), (2.5, 2.13)], C["top"])
    poly(d, [(2.0, 1.6), (2.45, 2.18), (3.0, 2.2), (2.6, 1.62)], C["era"], outline=C["dark"])
    for k in range(1, 4):
        t = k / 4
        d.line([P(2.0 + 0.45 * t, 1.6 + 0.58 * t), P(2.6 + 0.4 * t, 1.62 + 0.58 * t)], fill=C["dark"], width=3)
    rect(d, 4.05, 1.64, 4.62, 1.98, C["dark"], outline=C["darker"], width=2)   # ящик ЗИП
    rect(d, 3.45, 1.98, 4.72, 2.1, C["steel"], outline=C["darker"], width=2)   # труба ОПВТ
    rect(d, 2.55, 2.2, 2.95, 2.38, C["dark"], outline=C["darker"], width=2)    # прицел наводчика
    rect(d, 3.3, 2.22, 3.9, 2.4, C["base"], outline=C["darker"], width=2)      # командирская башенка
    rect(d, 2.85, 2.46, 3.6, 2.5, C["darker"])                                  # пулемёт
    rect(d, 3.45, 2.4, 3.55, 2.48, C["darker"])
    rect(d, 2.1, 1.82, 2.38, 1.98, C["darker"])                                 # «Штора»
    circle(d, 2.14, 1.9, 0.05, C["lens"])

    # пушка 125 мм: маска, ствол с термокожухом, эжектор
    rect(d, 1.75, 2.02, 2.1, 1.72, C["dark"], outline=C["darker"], width=2)
    rect(d, -2.67, 1.98, 1.8, 1.76, C["base"], outline=C["darker"], width=2)
    rect(d, -2.67, 1.98, 1.8, 1.95, C["light"])
    for k in range(6):
        x, _ = P(-2.3 + k * 0.72, 0)
        d.line([(x, GY - 1.98 * S), (x, GY - 1.76 * S)], fill=C["darker"], width=3)
    rect(d, -1.25, 2.04, -0.45, 1.70, C["base"], outline=C["darker"], width=3)  # эжектор
    rect(d, -1.25, 2.04, -0.45, 2.0, C["light"])
    rect(d, -2.7, 2.0, -2.55, 1.74, C["dark"], outline=C["darker"], width=2)    # дульный срез

    img.save(path)
    print(path, img.size)


if __name__ == "__main__":
    draw(sys.argv[1] if len(sys.argv) > 1 else "t90_base.png")
