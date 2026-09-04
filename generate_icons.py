from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ICONS = ROOT / "icons"
SIZE = 1024


def build_icon() -> Image.Image:
    image = Image.new("RGB", (SIZE, SIZE), "#174d3e")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((82, 82, 942, 942), radius=180, outline="#c8a65a", width=16)
    draw.rounded_rectangle((112, 112, 912, 912), radius=155, outline="#eadba9", width=5)
    draw.line((290, 230, 734, 230), fill="#c8a65a", width=8)
    draw.line((290, 794, 734, 794), fill="#c8a65a", width=8)
    for cy in (210, 814):
        draw.polygon(((512, cy - 26), (538, cy), (512, cy + 26), (486, cy)), fill="#eadba9", outline="#c8a65a")

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 540)
    letter = "ب"
    box = draw.textbbox((0, 0), letter, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    x = (SIZE - width) / 2 - box[0]
    y = 525 - height / 2 - box[1]
    draw.text((x, y), letter, font=font, fill="#fffaf0")
    return image


def main() -> None:
    ICONS.mkdir(exist_ok=True)
    source = build_icon()
    for size, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
        output = source.resize((size, size), Image.Resampling.LANCZOS)
        output.save(ICONS / name, format="PNG", optimize=True)
        print(f"created={ICONS / name} size={size}x{size}")


if __name__ == "__main__":
    main()
