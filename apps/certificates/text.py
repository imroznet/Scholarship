"""Shape Bangla with HarfBuzz and rasterize with FreeType.

ReportLab does not apply OpenType shaping, so certificate text is drawn from
these images while ASCII identifiers stay real PDF text.
"""

import uharfbuzz as hb
import freetype
from PIL import Image

from django.conf import settings


def _shape(text, font_path):
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    font = hb.Font(face)
    upem = face.upem or 1000
    font.scale = (upem, upem)
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer)
    return upem, list(zip(buffer.glyph_infos, buffer.glyph_positions))


def text_pixel_width(text, font_path, font_size):
    if not text:
        return 0
    upem, pairs = _shape(text, font_path)
    scale = font_size / upem
    return int(sum(position.x_advance * scale for _info, position in pairs))


def wrap_text(text, font_path, font_size, max_width):
    words = [part for part in (text or "").split() if part]
    if not words:
        return []
    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if text_pixel_width(trial, font_path, font_size) <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        if text_pixel_width(word, font_path, font_size) <= max_width:
            current = word
            continue
        chunk = ""
        for char in word:
            trial_chunk = chunk + char
            if text_pixel_width(trial_chunk, font_path, font_size) <= max_width:
                chunk = trial_chunk
            else:
                if chunk:
                    lines.append(chunk)
                chunk = char
        current = chunk
    if current:
        lines.append(current)
    return lines


def render_bangla_image(text, font_path=None, font_size=48, color=(15, 61, 46, 255)):
    font_path = str(font_path or settings.BANGLA_FONT_PATH)
    if not text:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    upem, pairs = _shape(text, font_path)
    scale = font_size / upem
    face = freetype.Face(font_path)
    face.set_char_size(int(font_size * 64))
    glyphs = []
    pen_x = 0
    pen_y = 0
    for info, position in pairs:
        face.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER)
        bitmap = face.glyph.bitmap
        width = bitmap.width
        rows = bitmap.rows
        pitch = bitmap.pitch
        raw = bytes(bitmap.buffer)
        pixels = b""
        if width and rows and raw:
            if pitch < 0:
                raw = raw[::-1]
                pitch = abs(pitch)
            for row in range(rows):
                start = row * pitch
                pixels += raw[start : start + width]
        glyphs.append(
            {
                "pixels": pixels,
                "w": width,
                "h": rows,
                "left": face.glyph.bitmap_left,
                "top": face.glyph.bitmap_top,
                "x": pen_x + position.x_offset * scale,
                "y": pen_y + position.y_offset * scale,
            }
        )
        pen_x += position.x_advance * scale
        pen_y += position.y_advance * scale
    ascender = face.size.ascender / 64
    descender = face.size.descender / 64
    image = Image.new("RGBA", (max(int(pen_x) + 8, 1), max(int(ascender - descender) + 8, 1)), (0, 0, 0, 0))
    baseline = int(ascender) + 4
    fill = tuple(color)
    for glyph in glyphs:
        if not glyph["w"] or not glyph["h"] or len(glyph["pixels"]) < glyph["w"] * glyph["h"]:
            continue
        mask = Image.frombytes("L", (glyph["w"], glyph["h"]), glyph["pixels"])
        colored = Image.new("RGBA", mask.size, fill)
        image.paste(colored, (int(glyph["x"] + glyph["left"]) + 2, int(baseline - glyph["top"] - glyph["y"])), mask)
    return image
