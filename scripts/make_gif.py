"""Assemble a walkthrough GIF from the captured screenshots."""
from pathlib import Path
from PIL import Image

OUT = Path("assets")

# Ordered frames: (filename, hold_seconds, caption)
FRAMES = [
    ("01_hero.png",               3.5),
    ("02_demo_ip_input.png",      3.0),
    ("03_demo_ip_gauge.png",      3.5),
    ("04_demo_sample_blacklist.png", 3.5),
    ("06_demo_sample_ip_detail.png", 3.5),
    ("08_connect.png",            3.0),
    ("13_live_ip_top.png",        3.0),
    ("14_live_ip_gauge.png",      4.0),
    ("15_live_ip_detail.png",     3.5),
]

TARGET_W, TARGET_H = 1280, 720

def load_frame(name: str) -> Image.Image:
    img = Image.open(OUT / name).convert("RGB")
    # Resize to target, keeping aspect ratio with letterbox
    img.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), (255, 255, 255))
    x = (TARGET_W - img.width) // 2
    y = (TARGET_H - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas

images = []
durations = []

for fname, hold in FRAMES:
    path = OUT / fname
    if not path.exists():
        print(f"  skip (not found): {fname}")
        continue
    img = load_frame(fname)
    images.append(img)
    durations.append(int(hold * 1000))
    print(f"  added {fname}  ({hold}s)")

out_path = OUT / "walkthrough.gif"
images[0].save(
    out_path,
    save_all=True,
    append_images=images[1:],
    duration=durations,
    loop=0,
    optimize=False,
)
size_kb = out_path.stat().st_size // 1024
print(f"\nGIF saved: {out_path}  ({size_kb} KB,  {len(images)} frames)")
