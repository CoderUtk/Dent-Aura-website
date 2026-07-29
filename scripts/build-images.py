#!/usr/bin/env python3
"""Generate responsive WebP + JPEG derivatives for every photo on the site.

The originals in assets/ are 1.7-2 MB RGBA PNGs straight off a phone, which is
roughly 11 MB of images on a page that renders them at 185-620 CSS px. This
script writes optimised derivatives to assets/img/ so the HTML can serve a
<picture> with a srcset instead. Originals stay put as the source of truth.

Run it after adding or replacing anything in SOURCES, then commit assets/img/.

    python scripts/build-images.py
"""
import io
import json
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "assets")
OUT_DIR = os.path.join(ROOT, "assets", "img")
MANIFEST = os.path.join(OUT_DIR, "manifest.json")

# Widths to emit. Anything wider than the source is skipped rather than upscaled.
# 400 covers gallery tiles and doctor thumbs at 2x, 800 covers tablet, 1200 the
# hero and any social/OG crop.
WIDTHS = (400, 800, 1200)

WEBP_QUALITY = 78
JPEG_QUALITY = 82

# stem -> source filename. The stem is what the HTML references.
SOURCES = {
    "exterior": "exterior.png",
    "exterior2": "exterior2.png",
    "reception": "reception.png",
    "treatment": "treatment.png",
    "waiting": "waiting.png",
    "consultation": "Consultation.png",
    "dr-jyoti-gupta": "jyotiGupta.jpeg",
    "dr-laxmi-gupta": "laxmigupta.jpeg",
}


def flatten(im):
    """PNGs here are RGBA with a fully opaque alpha; JPEG can't carry that."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def build(stem, filename):
    src = os.path.join(SRC_DIR, filename)
    original = Image.open(src)
    original = flatten(original)
    saved = []

    widths = [w for w in WIDTHS if w <= original.width] or [original.width]
    if original.width not in widths and original.width < max(WIDTHS):
        widths.append(original.width)

    for width in widths:
        height = round(original.height * width / original.width)
        resized = original.resize((width, height), Image.LANCZOS)
        out = os.path.join(OUT_DIR, "%s-%d.webp" % (stem, width))
        resized.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
        saved.append(out)

    # One JPEG at the largest width, as the <img> fallback inside <picture>.
    fallback_width = max(widths)
    height = round(original.height * fallback_width / original.width)
    resized = original.resize((fallback_width, height), Image.LANCZOS)
    out = os.path.join(OUT_DIR, "%s.jpg" % stem)
    resized.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    saved.append(out)

    return original.size, widths, saved


def build_og_card():
    """Social cards are 1.91:1. The portrait clinic shots crop badly, so the card
    comes off the landscape treatment-room photo, centre-cropped to 1200x630."""
    im = flatten(Image.open(os.path.join(SRC_DIR, "treatment.png")))
    target_w, target_h = 1200, 630

    scale = max(target_w / im.width, target_h / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = (im.width - target_w) // 2
    top = (im.height - target_h) // 2
    im = im.crop((left, top, left + target_w, top + target_h))

    out = os.path.join(OUT_DIR, "og-card.jpg")
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    print("%-16s %4dx%-4d -> %-18s %6.1f KB"
          % ("og-card", target_w, target_h, "social", os.path.getsize(out) / 1024))
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    before = total = 0
    manifest = {}

    for stem, filename in sorted(SOURCES.items()):
        before += os.path.getsize(os.path.join(SRC_DIR, filename))
        (w, h), widths, saved = build(stem, filename)
        size = sum(os.path.getsize(p) for p in saved)
        total += size
        manifest[stem] = {"widths": widths, "width": w, "height": h}
        print("%-16s %4dx%-4d -> %-18s %6.1f KB"
              % (stem, w, h, ",".join(str(x) for x in widths), size / 1024))

    total += os.path.getsize(build_og_card())

    # scripts/build-pages.py reads this to expand [[photo:...]] tokens, so the
    # srcset widths in the HTML can never drift from what was actually written.
    io.open(MANIFEST, "w", encoding="utf-8", newline="\n").write(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print("\noriginals %.1f MB -> derivatives %.1f MB"
          % (before / 1048576, total / 1048576))


if __name__ == "__main__":
    main()
