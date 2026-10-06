"""img2img через локальный ComfyUI: картинка-основа + промпт -> несколько вариантов.

Использует функции из скилла comfy-gen (запуск сервера, отправка задания), но строит
свой граф: LoadImage -> VAEEncode -> RepeatLatentBatch -> KSampler(denoise) -> SaveImage.
Чем меньше --denoise, тем точнее сохраняется форма основы.

  P:/ComfyUI/ComfyUI_windows_portable/python_embeded/python.exe tools/comfy_img2img.py base.png "prompt" \
      --negative "..." --denoise 0.55 --n 4 --name t90i2i -o tools/comfy_t90 [--lora]
"""
import argparse
import importlib.util
import os
import random
import shutil

SKILL = "C:/Users/Usa_f/.claude/skills/comfy-gen/comfy.py"
spec = importlib.util.spec_from_file_location("comfy_gen", SKILL)
cg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("prompt")
    ap.add_argument("--negative", default="")
    ap.add_argument("--denoise", type=float, default=0.55)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--lora", action="store_true", help="с пиксельной LoRA")
    ap.add_argument("--lora-strength", type=float, default=1.0)
    ap.add_argument("--name", default="i2i")
    ap.add_argument("-o", "--out", default=".")
    a = ap.parse_args()

    cg.start_server()
    in_dir = os.path.join(cg.COMFY_HOME, "ComfyUI", "input")
    os.makedirs(in_dir, exist_ok=True)
    base_name = "claude_" + os.path.basename(a.base)
    shutil.copyfile(a.base, os.path.join(in_dir, base_name))

    seed = a.seed if a.seed is not None else random.randint(0, 2**31 - 1)
    wf = cg.workflow(a.prompt, a.negative, 1024, 1024, a.steps, a.cfg, seed, 1,
                     a.lora_strength, a.lora, "claude/i2i")
    # пустой латент заменяем закодированной картинкой-основой, повторённой n раз
    del wf["5"]
    wf["10"] = {"class_type": "LoadImage", "inputs": {"image": base_name}}
    wf["11"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["1", 2]}}
    wf["12"] = {"class_type": "RepeatLatentBatch", "inputs": {"samples": ["11", 0], "amount": a.n}}
    wf["6"]["inputs"]["latent_image"] = ["12", 0]
    wf["6"]["inputs"]["denoise"] = a.denoise

    print(f"img2img {a.n} шт., seed={seed}, denoise={a.denoise}, lora={a.lora}...")
    imgs = cg.run_workflow(wf)
    os.makedirs(a.out, exist_ok=True)
    for i, im in enumerate(imgs):
        q = f"/view?filename={im['filename']}&subfolder={im.get('subfolder', '')}&type={im.get('type', 'output')}"
        path = os.path.join(a.out, f"{a.name}_{seed}_{i}.png")
        with open(path, "wb") as f:
            f.write(cg.http(q, timeout=60))
        print("сохранено:", path)


if __name__ == "__main__":
    main()
