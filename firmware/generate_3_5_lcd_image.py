#!/usr/bin/env python3
"""
Genera una imagen binaria RGB565 para una pantalla LCD 3.5" 320x480.

Uso:
    python3 generate_3_5_lcd_image.py input.png output.bin
    python3 generate_3_5_lcd_image.py --default output.bin

Si no pasas imagen, genera una imagen de ejemplo con estilo aqua/teal para
la pantalla ESP32-P4 WiFi-6 Touch LCD 3.5".
"""

from __future__ import annotations
import argparse
import math
import os
import sys
from typing import Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:
    print("[ERROR] Necesitas instalar Pillow: pip install pillow")
    raise SystemExit(1)

DEFAULT_WIDTH = 320
DEFAULT_HEIGHT = 480


def rgb888_to_rgb565(r: int, g: int, b: int) -> int:
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


def image_to_rgb565_bin(input_path: str, output_path: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> None:
    img = Image.open(input_path).convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)

    data = bytearray()
    px = img.load()
    for y in range(height):
        for x in range(width):
            r, g, b = px[x, y]
            v = rgb888_to_rgb565(r, g, b)
            data.append(v & 0xFF)
            data.append((v >> 8) & 0xFF)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"[OK] Convertida: {input_path} -> {output_path}")
    print(f"[OK] Resolucion: {width}x{height}")
    print(f"[OK] Tamaño: {len(data)} bytes")


def generate_default_image(path: str, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT) -> None:
    img = Image.new("RGB", (width, height), (15, 24, 36))
    draw = ImageDraw.Draw(img)

    # Fondo oceánico / aqua con degradado
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(16 + 55 * t)
        g = int(40 + 145 * t)
        b = int(52 + 142 * t)
        draw.line((0, y, width, y), fill=(r, g, b))

    # Efecto de ondas
    for wave in range(12):
        y0 = 15 + wave * 34
        for x in range(0, width, 3):
            yy = y0 + int(math.sin(x * 0.09 + wave) * 9)
            draw.line((x, yy, x + 2, yy + 2), fill=(90, 210, 220, 100), width=1)

    # Sombra del panel/board visual
    panel = (38, 80, 120)
    draw.rounded_rectangle((30, 80, width - 30, height - 80), radius=26, fill=(18, 60, 76))
    draw.rounded_rectangle((36, 86, width - 36, height - 86), radius=22, fill=(10, 40, 52))

    # Marca de LCD
    txt = "3.5\" LCD"
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), txt, font=font_big)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x0 = (width - tw) // 2
    y0 = (height // 2) - 20
    draw.text((x0, y0), txt, fill=(200, 240, 250), font=font_big)
    draw.text((x0 - 18, y0 + 42), "ESP32-P4 WiFi-6 TOUCH", fill=(120, 230, 230), font=font_small)
    draw.text((x0 + 30, y0 + 64), "320x480", fill=(180, 210, 240), font=font_small)

    # Barra inferior de conexiones
    draw.rounded_rectangle((60, height - 68, width - 60, height - 30), radius=12, fill=(18, 32, 42), outline=(120, 170, 190), width=2)
    for i in range(8):
        x = 78 + i * 28
        draw.rounded_rectangle((x, height - 60, x + 16, height - 38), radius=3, fill=(26, 110, 130))

    img.save(path.replace(".bin", ".png"))
    print(f"[OK] Imagen de ejemplo creada: {path.replace('.bin', '.png')}")


def main():
    parser = argparse.ArgumentParser(description="Generador de imagen para pantalla ESP32-P4 LCD 3.5\".")
    parser.add_argument("input", nargs="?", help="Archivo PNG/JPG de entrada")
    parser.add_argument("output", nargs="?", help="Archivo binario de salida")
    parser.add_argument("--default", action="store_true", help="Genera una imagen de ejemplo para 320x480")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Ancho de salida (default 320)")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Alto de salida (default 480)")
    args = parser.parse_args()

    if args.default or args.input is None or args.output is None:
        if not args.output:
            out = "boot_screen_320x480.bin"
        else:
            out = args.output
        generate_default_image(out, args.width, args.height)
        source = out.replace(".bin", ".png")
        image_to_rgb565_bin(source, out, args.width, args.height)
        return

    image_to_rgb565_bin(args.input, args.output, args.width, args.height)


if __name__ == "__main__":
    main()
