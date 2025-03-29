import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import tifffile


# Ascii_converter.py

# === CONFIGURATION ===
CONFIG = {
    "input_path": "Aphelion/skull.jpg",#"Aphelion/wave.jpg",
    "output_image_path": "Aphelion/skull_ascii.jpg",#"Aphelion/wave_ascii.jpg",
    "output_text_path": "Aphelion/skull_ascii.txt",
    "ascii_chars": " ;i7JYGP$B&#@",#"@%#*+=-:. " " :-=+*#%@"  " .,:;i1tfLCG08@" " .oO@" " ⠀" ;i7JYGP$B8&#@"
    "scale_factor": 0.9,                  # Controls resolution: lower = bigger characters
    "font_size": None,                    # None = use default font, or set to e.g. 14 for truetype
    "mode": "dark",                       # Options: "dark", "bright", "blur"
    "use_edges": True,                    # Whether to apply edge detection
    "char_color_mode": "fixed",           # Options: "image", "fixed"
    "char_fixed_color": (255, 255, 255)   # RGB tuple, only used if char_color_mode == "fixed"
}

# === LOAD IMAGE ===
img = Image.open(CONFIG["input_path"]).convert("RGB")
img_np = np.array(img)
img_width, img_height = img.size

# === LOAD FONT ===
if CONFIG["font_size"]:
    font = ImageFont.truetype("arial.ttf", CONFIG["font_size"])
else:
    font = ImageFont.load_default()

bbox = font.getbbox("A")
char_width = bbox[2] - bbox[0]
char_height = bbox[3] - bbox[1]
aspect_correction = char_height / char_width

# === COMPUTE CHARACTER GRID SIZE ===
cols = int(img_width / char_width * CONFIG["scale_factor"])
rows = int(img_height / char_height * CONFIG["scale_factor"])
new_width = cols
new_height = int(rows * aspect_correction)

# === RESIZE IMAGE TO MATCH GRID ===
img_resized = img.resize((new_width, new_height))
img_np = np.array(img_resized)
gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

# === EDGE ENHANCEMENT (optional) ===
if CONFIG["use_edges"]:
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1)
    edges = np.sqrt(sobelx**2 + sobely**2)
    edges = (edges / edges.max() * 255).astype(np.uint8)
    luminance = cv2.addWeighted(gray, 0.5, edges, 0.5, 0)
else:
    luminance = gray

# === PREPARE BACKGROUND BASED ON MODE ===
if CONFIG["mode"] == "dark":
    background_color = (0, 0, 0)
    background_img = Image.new("RGB", (cols * char_width, rows * char_height), background_color)
elif CONFIG["mode"] == "bright":
    background_color = (255, 255, 255)
    background_img = Image.new("RGB", (cols * char_width, rows * char_height), background_color)
elif CONFIG["mode"] == "blur":
    blur_img = cv2.GaussianBlur(img_np, (15, 15), 5)
    blur_img_pil = Image.fromarray(blur_img).resize((cols * char_width, rows * char_height))
    background_img = blur_img_pil
else:
    raise ValueError(f"Invalid mode: {CONFIG['mode']}")

draw = ImageDraw.Draw(background_img)

# === GENERATE ASCII AND DRAW ===
ascii_lines = []
for y in range(rows):
    line = ""
    for x in range(cols):
        px_x = x
        px_y = int(y * aspect_correction)
        if px_y >= new_height or px_x >= new_width:
            continue
        lum = luminance[px_y, px_x]
        char = CONFIG["ascii_chars"][lum * len(CONFIG["ascii_chars"]) // 256]

        # === CHOOSE CHARACTER COLOR ===
        if CONFIG["char_color_mode"] == "fixed":
            color = CONFIG["char_fixed_color"]
        else:
            color = tuple(img_np[px_y, px_x])


        draw.text((x * char_width, y * char_height), char, font=font, fill=color)
        line += char
    ascii_lines.append(line)

# === SAVE OUTPUTS ===
tifffile.imwrite(CONFIG["output_image_path"], np.array(background_img))
with open(CONFIG["output_text_path"], "w", encoding="utf-8") as f:
    f.write("\n".join(ascii_lines))

print("ASCII image and text exported.")

