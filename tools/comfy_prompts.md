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
4. **Лист из двух кадров и хитбокс** (`tools/make_tank_sheet.py`), в игре масштаб 1.5 (195×54 px):
   ```
   python tools/make_tank_sheet.py tools/comfy_t90/cand/w128_i2iP_954233467_1.png runner/sprites/svo_t90.png --scale 1.5
   ```

Сравнительные листы вариантов: `tools/compare_sprites.py`. Промежуточные картинки лежат в `tools/comfy_t90/` (в git не попадают).
