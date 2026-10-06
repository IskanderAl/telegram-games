# Спрайты, сгенерированные в ComfyUI (скилл comfy-gen)

Скрипты запускаются питоном ComfyUI (в нём есть Pillow и numpy):
`P:/ComfyUI/ComfyUI_windows_portable/python_embeded/python.exe`

## svo_t90 — танк Т-90 для стиля «СВО» (runner/sprites/svo_t90.png)

Обычная генерация давала либо «танк вообще», либо ракурс три четверти, поэтому форма задаётся силуэтом:

1. **Силуэт по реальным размерам** (`tools/t90_base.py`): корпус 6.86 м, с пушкой 9.53 м, высота 2.23 м,
   6 катков под резиновыми экранами, клиновидная башня с ДЗ, «Штора», пулемёт, пушка с эжектором, бочка на корме.
   ```
   python tools/t90_base.py tools/comfy_t90/t90_base.png
   ```
2. **img2img с пиксельной LoRA** (`tools/comfy_img2img.py`), denoise 0.55, 30 шагов, seed 954233467, вариант №1 из 4:
   ```
   python tools/comfy_img2img.py tools/comfy_t90/t90_base.png "pixel art, T-90 main battle tank, exact side view, long gun with bore evacuator, reactive armor turret, six road wheels, side skirts, dark green, detailed shading, plain white background" --negative "people, soldier, crew, text, numbers, letters, flag, emblem, insignia, logo, watermark, Z symbol, top view, front view, three quarter view, perspective, cropped, multiple tanks, ground, terrain, grass, dust, smoke, shadow, blurry, cartoon, toy, gradient, antialiasing, noise" --denoise 0.55 --lora --n 4 --seed 954233467 --name i2iP -o tools/comfy_t90
   ```
3. **Пикселизация с сохранением пропорций** (`tools/pixel_wide.py`) — `comfy.py pixelize` сжимает кадр в квадрат,
   из-за чего широкие предметы выходят сплющенными:
   ```
   python tools/pixel_wide.py tools/comfy_t90/i2iP_954233467_1.png --width 128 --colors 28 --outline "#1d2210" -o tools/comfy_t90/cand/w128_i2iP_954233467_1.png
   ```
4. **Пушка покороче** (`tools/shorten_gun.py`): вырезаны столбцы ровной трубы до и после эжектора,
   вылет за корпус 38 → 22 px:
   ```
   python tools/shorten_gun.py tools/comfy_t90/cand/w128_i2iP_954233467_1.png tools/comfy_t90/cand/t90_shortgun.png 5:16 31:36
   ```
5. **Лист из двух кадров и хитбокс** (`tools/make_tank_sheet.py`), в игре масштаб 1.5 (171×54 px):
   ```
   python tools/make_tank_sheet.py tools/comfy_t90/cand/t90_shortgun.png runner/sprites/svo_t90.png --scale 1.5
   ```

## svo_fighter и svo_fpv — боец ВС РФ и FPV-дрон (без флагов и знаков различия)

1. Силуэты (`tools/svo_bases.py`): боец в «Ратнике» (шлем 6Б47 в чехле, наушники, очки, бронежилет, наколенники,
   камуфляж ЕМР, АК стволом к земле), FPV в ракурсе сверху-сбоку (4 винта видны), а также варианты FPV сбоку и «Ланцета».
   ```
   python tools/svo_bases.py tools/comfy_svo
   ```
2. img2img с пиксельной LoRA, denoise 0.55:
   - боец — seed 393911595, вариант №3; промпт: `pixel art, modern Russian army soldier, Ratnik combat gear, 6B47 helmet with digital camouflage cover, tactical headset, ballistic glasses, EMR digital pixel camouflage uniform, plate carrier with magazine pouches, knee pads, AK-12 rifle held at low ready pointing down, side view facing left, full body, standing, detailed shading, plain white background`; негатив: `flag, patch, insignia, emblem, chevron, armband, letters, text, numbers, Z symbol, V symbol, blood, gore, multiple people, cropped, front view, back view, aiming, gradient, antialiasing, noise, blurry`
   - FPV — seed 1058255568, вариант №2; промпт: `pixel art, FPV quadcopter drone seen from the side and slightly above, four spinning propellers, black carbon fiber frame, battery on top, camera at the front, olive green munition attached underneath, detailed shading, plain white background`
3. Пикселизация: боец `--height 36 --colors 20 --holes 12` (убирает просвет фона между ногами), дрон `--width 52 --colors 16 --shadow 0 --tol 30` (светлые винты не путать с тенью).
4. Листы: `make_tank_sheet.py ... --scale 1.5` → `runner/sprites/svo_fighter.png` (24×60 px в игре), `runner/sprites/svo_fpv.png` (81×27 px).

Сравнительные листы вариантов: `tools/compare_sprites.py`. Промежуточные картинки лежат в `tools/comfy_t90/` (в git не попадают).
