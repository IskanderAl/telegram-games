"""Силуэты-основы для img2img (стиль «СВО»): боец ВС РФ в «Ратнике» и дроны. Без флагов и знаков.

Все смотрят влево (навстречу игроку). Фон белый — его потом удаляет tools/pixel_wide.py.

  python tools/svo_bases.py tools/comfy_svo
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw

EMR = (122, 134, 88)      # база камуфляжа «цифра» (ЕМР)
EMR2 = (108, 119, 77)     # бронежилет и рюкзак — тот же камуфляж чуть темнее
CAMO = [((78, 92, 52), 0.24), ((112, 94, 62), 0.16), ((44, 46, 37), 0.08), ((150, 160, 112), 0.10)]
SKIN = (214, 166, 128)
GLOVE = (58, 60, 48)
RIFLE = (29, 29, 29)


def apply_emr(img, cell=14, seed=7):
    """Пиксельные пятна камуфляжа поверх одежды (только там, где цвет базы ЕМР)."""
    rnd = random.Random(seed)
    px = img.load()
    d = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            c = px[min(x + cell // 2, w - 1), min(y + cell // 2, h - 1)]
            if c not in (EMR, EMR2):
                continue
            r, acc = rnd.random(), 0.0
            for color, p in CAMO:
                acc += p
                if r < acc:
                    ww = cell * (2 if rnd.random() < 0.35 else 1)  # «цифра» — пятна из 1–2 клеток
                    for yy in range(y, min(y + cell, h)):
                        for xx in range(x, min(x + ww, w)):
                            if px[xx, yy] in (EMR, EMR2):
                                px[xx, yy] = color
                    break


def soldier(path):
    W, H = 832, 1216
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # дальняя нога и ботинок (носки смотрят влево)
    d.polygon([(440, 615), (505, 615), (510, 700), (500, 860), (495, 1080), (445, 1080), (440, 860), (435, 700)], fill=EMR)
    d.polygon([(445, 1070), (500, 1070), (502, 1150), (405, 1150), (408, 1120), (440, 1110)], fill=(52, 40, 28))
    d.rounded_rectangle([445, 830, 494, 892], 12, fill=(50, 56, 38))                        # наколенник
    # ближняя нога и ботинок
    d.polygon([(360, 620), (440, 620), (440, 700), (418, 860), (402, 1080), (350, 1080), (355, 860), (352, 700)], fill=EMR)
    d.polygon([(350, 1075), (405, 1075), (408, 1150), (298, 1150), (303, 1118), (345, 1108)], fill=(58, 44, 30))
    d.rounded_rectangle([343, 828, 395, 892], 12, fill=(61, 68, 48))                        # наколенник

    # рюкзак, корпус, бронежилет с подсумками, пояс
    d.rounded_rectangle([488, 345, 548, 565], 16, fill=EMR2)
    d.polygon([(355, 330), (495, 330), (515, 420), (505, 610), (365, 615), (345, 520)], fill=EMR)
    d.polygon([(338, 360), (472, 352), (484, 600), (343, 602)], fill=EMR2)
    d.rounded_rectangle([318, 430, 352, 520], 6, fill=EMR2)                                 # подсумки магазинов
    d.rounded_rectangle([316, 525, 350, 590], 6, fill=EMR2)
    d.rectangle([348, 595, 507, 630], fill=(74, 82, 54))                                     # разгрузочный пояс
    d.rounded_rectangle([480, 598, 522, 655], 6, fill=(74, 82, 54))

    # голова: шея, лицо, баллистические очки, шлем 6Б47 в чехле, активные наушники
    d.rectangle([395, 300, 445, 342], fill=SKIN)
    d.ellipse([370, 222, 456, 322], fill=SKIN)
    d.polygon([(374, 252), (356, 272), (376, 278)], fill=SKIN)                              # нос
    d.rectangle([366, 248, 424, 266], fill=(40, 42, 40))                                     # очки
    d.chord([342, 108, 528, 300], 180, 360, fill=EMR)                                        # купол шлема
    d.polygon([(348, 203), (522, 203), (518, 252), (472, 262), (458, 238), (366, 242)], fill=EMR)
    d.rectangle([358, 186, 522, 200], fill=(52, 54, 44))                                     # ремень очков на шлеме
    d.rounded_rectangle([346, 168, 396, 202], 8, fill=(70, 74, 70))                          # тактические очки на шлеме
    d.ellipse([438, 232, 482, 288], fill=(54, 60, 42))                                       # наушник

    # автомат АК-12 «на изготовку вниз»: приклад у плеча, ствол к земле перед бойцом
    bx, by = 505, 430
    ang = math.radians(45)
    dx, dy = -math.cos(ang), math.sin(ang)        # вдоль оружия (к дульному срезу)
    nx, ny = math.sin(ang), math.cos(ang)         # перпендикуляр (вниз-вправо)
    L = 520

    def P(t, off=0.0):
        return (bx + dx * L * t + nx * off, by + dy * L * t + ny * off)

    def seg(t0, t1, half, color):
        d.polygon([P(t0, -half), P(t1, -half), P(t1, half), P(t0, half)], fill=color)

    seg(-0.02, 0.22, 17, (42, 42, 42))            # приклад
    seg(0.22, 0.56, 23, RIFLE)                    # ствольная коробка
    seg(0.56, 0.79, 18, (36, 36, 36))             # цевьё с планками
    seg(0.79, 0.97, 6, (58, 58, 58))              # ствол
    seg(0.95, 1.0, 9, (40, 40, 40))               # дульный тормоз
    d.polygon([P(0.45, 22), P(0.54, 22), P(0.6, 105), P(0.5, 112)], fill=(46, 40, 34))     # изогнутый магазин
    d.polygon([P(0.29, 22), P(0.34, 22), P(0.31, 80), P(0.25, 75)], fill=RIFLE)             # пистолетная рукоять
    d.rectangle([P(0.3, -40)[0] - 20, P(0.3, -40)[1] - 8, P(0.3, -40)[0] + 20, P(0.3, -40)[1] + 4], fill=(48, 48, 48))  # прицел
    gx, gy = P(0.3, 52)
    d.ellipse([gx - 22, gy - 22, gx + 22, gy + 22], fill=GLOVE)                             # правая рука на рукояти

    # ближняя (левая) рука держит цевьё
    hx, hy = P(0.66, 0)
    d.polygon([(432, 345), (482, 352), (434, 512), (394, 497)], fill=EMR)                  # плечо
    d.polygon([(394, 497), (434, 512), (hx + 18, hy + 10), (hx - 14, hy - 16)], fill=EMR)  # предплечье
    d.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=GLOVE)

    apply_emr(img)
    img.save(path)
    print(path)


def fpv(path, payload=False):
    W, H = 1344, 768
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.ellipse([250, 360, 530, 384], fill=(176, 180, 184))       # размытые винты (вид сбоку)
    d.ellipse([810, 360, 1090, 384], fill=(176, 180, 184))
    d.rectangle([380, 400, 960, 420], fill=(34, 34, 34))        # лучи рамы (карбон)
    for x in (365, 925):                                        # моторы
        d.rectangle([x, 376, x + 50, 402], fill=(58, 58, 58))
        d.rectangle([x + 18, 366, x + 32, 378], fill=(90, 90, 90))
    d.rectangle([560, 385, 780, 426], fill=(43, 43, 43))        # полётный стек
    d.rectangle([590, 338, 762, 385], fill=(58, 58, 58))        # аккумулятор
    d.rectangle([590, 352, 762, 364], fill=(200, 160, 32))      # обмотка аккумулятора
    d.rectangle([600, 336, 612, 388], fill=(20, 20, 20))        # стяжка
    d.rectangle([742, 336, 754, 388], fill=(20, 20, 20))
    d.rectangle([516, 390, 562, 430], fill=(30, 30, 30))        # камера
    d.ellipse([506, 400, 526, 420], fill=(80, 150, 200))
    d.line([(780, 386), (845, 318)], fill=(30, 30, 30), width=8)  # антенна
    d.ellipse([838, 310, 856, 328], fill=(30, 30, 30))
    if payload:
        d.rectangle([540, 432, 760, 470], fill=(86, 96, 58))    # боеприпас под рамой
        d.polygon([(540, 432), (540, 470), (470, 451)], fill=(70, 78, 48))
        d.polygon([(760, 428), (800, 420), (800, 482), (760, 474)], fill=(40, 40, 36))
        for x in (580, 700):
            d.rectangle([x, 426, x + 8, 476], fill=(20, 20, 20))  # стяжки
    img.save(path)
    print(path)


def fpv_34(path):
    """FPV сбоку-сверху: видны все 4 винта, так квадрокоптер узнаётся даже в маленьком спрайте."""
    W, H = 1344, 768
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    prop = (176, 180, 184)
    motors = [((500, 320), 0.85), ((850, 320), 0.85), ((430, 470), 1.0), ((920, 470), 1.0)]  # задние выше и меньше
    for (x, y), k in motors[:2]:
        d.ellipse([x - 160 * k, y - 46 * k, x + 160 * k, y + 46 * k], fill=prop)
    for (x, y), k in motors:                                    # лучи рамы к центру
        d.line([(x, y + 14), (672, 410)], fill=(34, 34, 34), width=int(26 * k))
    for (x, y), k in motors:
        d.rectangle([x - 22 * k, y - 4, x + 22 * k, y + 26 * k], fill=(58, 58, 58))
    for (x, y), k in motors[2:]:
        d.ellipse([x - 175 * k, y - 50 * k, x + 175 * k, y + 50 * k], fill=prop)
    d.rounded_rectangle([566, 360, 790, 452], 14, fill=(43, 43, 43))     # корпус
    d.rectangle([600, 318, 770, 366], fill=(58, 58, 58))                 # аккумулятор
    d.rectangle([600, 332, 770, 344], fill=(200, 160, 32))
    d.rectangle([528, 398, 572, 440], fill=(30, 30, 30))                 # камера спереди
    d.ellipse([518, 408, 540, 430], fill=(80, 150, 200))
    d.line([(780, 366), (842, 300)], fill=(30, 30, 30), width=8)        # антенна
    d.rectangle([586, 456, 790, 494], fill=(86, 96, 58))                # боеприпас снизу
    d.polygon([(586, 456), (586, 494), (520, 475)], fill=(70, 78, 48))
    d.polygon([(790, 452), (826, 444), (826, 506), (790, 498)], fill=(40, 40, 36))
    img.save(path)
    print(path)


def lancet(path):
    W, H = 1344, 768
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    body, dark = (110, 118, 96), (70, 76, 60)
    # X-образные крылья: видны верхняя и нижняя половины передней и задней пары
    d.polygon([(470, 360), (560, 360), (660, 240), (612, 236)], fill=dark)
    d.polygon([(470, 410), (560, 410), (660, 530), (612, 534)], fill=dark)
    d.polygon([(800, 360), (930, 360), (1060, 200), (1000, 196)], fill=dark)
    d.polygon([(800, 410), (930, 410), (1060, 570), (1000, 574)], fill=dark)
    d.rounded_rectangle([300, 352, 1060, 418], 32, fill=body)  # фюзеляж
    d.rectangle([340, 352, 1040, 362], fill=(140, 148, 124))   # блик сверху
    d.ellipse([300, 360, 350, 410], fill=(40, 44, 40))         # окно камеры в носу
    d.ellipse([1056, 316, 1080, 454], fill=(170, 172, 168))    # толкающий винт (размытый)
    d.rectangle([1040, 376, 1062, 394], fill=(50, 50, 50))
    img.save(path)
    print(path)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    soldier(os.path.join(out, "soldier_base.png"))
    fpv(os.path.join(out, "fpv_base.png"))
    fpv(os.path.join(out, "fpvp_base.png"), payload=True)
    lancet(os.path.join(out, "lancet_base.png"))
