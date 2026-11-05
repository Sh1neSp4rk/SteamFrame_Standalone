"""Build Steam library art with the red "<GAME> VR" pill (and, for entries streamed from the PC,
the blue "STREAM FROM PC" pill above it) in the style of ~/PCVR/bin/make_vrart.ps1 and
add_stream_pill.ps1 on the Frame, but with Pillow so it runs from Python on the PC.

Usage: python -I make_vrart.py jobs.json
jobs.json is a list of objects:
  {"id": "3664936261",            # Steam app or shortcut id (file name prefix)
   "src": "path/to/src_dir",      # holds library_600x900_2x.jpg (or library_600x900.jpg),
                                  #   library_header.jpg (or header.jpg), library_hero.jpg, logo.png
   "label": "RE4 VR",             # red pill text
   "title": "",                   # optional white title under the pill (for art without the game's name)
   "stream": false,               # add the blue STREAM FROM PC pill (Frame copy of a PC entry)
   "hero": true, "logo": true,    # also write <id>_hero.png and <id>_logo.png
   "out": "path/to/out_dir"}
Outputs <id>p.png (600x900), <id>.png (920x430), <id>_hero.png (1920x620), <id>_logo.png.
"""
import json, os, shutil, sys
from PIL import Image, ImageDraw, ImageFont

FONT = r"C:\Windows\Fonts\arialbd.ttf"
RED = (204, 18, 24, 255)
BLUE = (28, 104, 214, 255)
STREAM_TEXT = "STREAM FROM PC"


def find_art(src, names):
    for n in names:
        p = os.path.join(src, n)
        if os.path.exists(p):
            return p
    return None


def canvas(path, w, h):
    """Cover-fit the source image onto a w x h canvas."""
    im = Image.open(path).convert("RGBA")
    s = max(w / im.width, h / im.height)
    dw, dh = round(im.width * s), round(im.height * s)
    im = im.resize((dw, dh), Image.LANCZOS)
    out = Image.new("RGBA", (w, h))
    out.paste(im, ((w - dw) // 2, (h - dh) // 2))
    return out


def pill(img, w, cy, text, font_px, color):
    """Rounded pill centred horizontally at vertical centre cy. Returns (top, height)."""
    font = ImageFont.truetype(FONT, font_px)
    tw = font.getlength(text)
    ph = int(font_px * 1.6)
    pw = int(tw + font_px * 1.3)
    x = int((w - pw) / 2)
    y = int(cy - ph / 2)
    r = int(ph * 0.28)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    off = int(font_px * 0.12)
    d.rounded_rectangle([x, y + off, x + pw, y + ph + off], radius=r, fill=(0, 0, 0, 120))
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=r, fill=color)
    d.text((x + pw / 2, y + ph / 2 + 1), text, font=font, fill=(255, 255, 255, 255), anchor="mm")
    return y, ph


def title(img, w, cy, text, font_px):
    font = ImageFont.truetype(FONT, font_px)
    d = ImageDraw.Draw(img)
    d.text((w / 2, cy), text, font=font, fill=(255, 255, 255, 255), anchor="mm",
           stroke_width=max(1, int(font_px * 0.06)), stroke_fill=(0, 0, 0, 255))


def stream_pill(img, w, red_top, red_h):
    px = int(red_h / 1.6 * 0.72)
    ph = int(px * 1.6)
    cy = red_top - 6 - ph / 2
    pill(img, w, cy, STREAM_TEXT, px, BLUE)


def build(job):
    src, out, label = job["src"], job["out"], job["label"]
    ttl = job.get("title", "")
    stream = job.get("stream", False)
    os.makedirs(out, exist_ok=True)
    jid = str(job["id"])
    portrait = find_art(src, ["library_600x900_2x.jpg", "library_600x900.jpg", "library_capsule.jpg"])
    wide = find_art(src, ["library_header.jpg", "header.jpg"])
    hero = find_art(src, ["library_hero.jpg"])
    logo = find_art(src, ["logo.png"])
    if portrait:
        im = canvas(portrait, 600, 900)
        if ttl:
            top, h = pill(im, 600, 690, label, 38, RED)
            title(im, 600, 800, ttl, 92)
        else:
            top, h = pill(im, 600, 820, label, 42, RED)
        if stream:
            stream_pill(im, 600, top, h)
        im.convert("RGB").save(os.path.join(out, jid + "p.png"))
    else:
        print(jid, "WARNING no portrait")
    if wide:
        im = canvas(wide, 920, 430)
        if ttl:
            top, h = pill(im, 920, 300, label, 34, RED)
            title(im, 920, 375, ttl, 58)
        else:
            top, h = pill(im, 920, 370, label, 38, RED)
        if stream:
            stream_pill(im, 920, top, h)
        im.convert("RGB").save(os.path.join(out, jid + ".png"))
    else:
        print(jid, "WARNING no wide")
    if job.get("hero", True) and hero:
        canvas(hero, 1920, 620).convert("RGB").save(os.path.join(out, jid + "_hero.png"))
    if job.get("logo", True) and logo:
        shutil.copyfile(logo, os.path.join(out, jid + "_logo.png"))
    print(jid, label, "stream" if stream else "", "->", out)


if __name__ == "__main__":
    for j in json.load(open(sys.argv[1], encoding="utf-8")):
        build(j)
