#!/usr/bin/env python3
"""
Generador de pantalla de arranque BIN RGB565 para Waveshare ESP32-P4-WIFI6-Touch-LCD-3.5"
ST7796 Driver - Resolución: 320x480 (vertical)

Genera assets/boot_screen_320x480.bin en formato RGB565 little-endian
Tamaño exacto requerido: 307200 bytes (320*480*2)

Uso:
    python3 tools/make_boot_screen.py
    python3 tools/make_boot_screen.py imagen.png
    python3 tools/make_boot_screen.py imagen.jpg --swap --bgr
"""

from PIL import Image, ImageDraw, ImageFont
import struct
import sys
import argparse
import os

LCD_WIDTH = 320
LCD_HEIGHT = 480
EXPECTED_SIZE = LCD_WIDTH * LCD_HEIGHT * 2  # 307200 bytes


def rgb888_to_rgb565(r, g, b, bgr=False):
    """Convierte RGB888 a RGB565"""
    if bgr:
        r, b = b, r
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


def convert_image_to_bin(input_image, output_bin, width=LCD_WIDTH, height=LCD_HEIGHT, swap=False, bgr=False):
    """Convierte una imagen a formato binario RGB565 con padding si es necesario"""
    print(f"[*] Cargando imagen: {input_image}")
    img = Image.open(input_image).convert("RGB")
    orig_w, orig_h = img.size
    print(f"[*] Tamaño original: {orig_w}x{orig_h}")
    
    # Calcular dimensiones con padding para mantener aspecto
    ratio_img = orig_w / orig_h
    ratio_lcd = width / height
    
    if ratio_img > ratio_lcd:
        # Imagen más ancha: add padding top/bottom
        new_w = width
        new_h = int(width / ratio_img)
        pad_top = (height - new_h) // 2
        pad_bottom = height - new_h - pad_top
        pad_left = pad_right = 0
    else:
        # Imagen más alta: add padding left/right
        new_h = height
        new_w = int(height * ratio_img)
        pad_left = (width - new_w) // 2
        pad_right = width - new_w - pad_left
        pad_top = pad_bottom = 0
    
    print(f"[*] Escalando a: {new_w}x{new_h}")
    img_scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Crear imagen con fondo negro (padding)
    img_final = Image.new("RGB", (width, height), (0, 0, 0))
    img_final.paste(img_scaled, (pad_left, pad_top))
    
    print(f"[*] Convirtiendo a RGB565 little-endian...")
    bin_data = bytearray()
    pixels = img_final.load()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            rgb565 = rgb888_to_rgb565(r, g, b, bgr=bgr)
            
            if swap:
                # Big-endian
                bin_data.append((rgb565 >> 8) & 0xFF)
                bin_data.append(rgb565 & 0xFF)
            else:
                # Little-endian
                bin_data.append(rgb565 & 0xFF)
                bin_data.append((rgb565 >> 8) & 0xFF)
        
        if (y + 1) % 48 == 0:
            progress = ((y + 1) / height) * 100
            print(f"[→] {progress:.1f}% ({y+1}/{height})")
    
    # Verificar tamaño
    if len(bin_data) != EXPECTED_SIZE:
        print(f"[ERROR] Tamaño incorrecto: {len(bin_data)} bytes (esperado {EXPECTED_SIZE})")
        return False
    
    # Guardar
    with open(output_bin, 'wb') as f:
        f.write(bin_data)
    
    # Guardar PNG de referencia
    png_path = output_bin.replace('.bin', '.png')
    img_final.save(png_path)
    
    print(f"\n[✓] Archivo BIN generado: {output_bin}")
    print(f"[✓] Tamaño: {len(bin_data)} bytes (verificado: {len(bin_data) == EXPECTED_SIZE})")
    print(f"[✓] PNG referencia: {png_path}")
    return True


def generate_default_image(output_bin, width=LCD_WIDTH, height=LCD_HEIGHT, swap=False, bgr=False):
    """Genera imagen de arranque por defecto"""
    print(f"[*] Generando imagen por defecto: {width}x{height}...")
    
    img = Image.new("RGB", (width, height), (10, 15, 30))
    draw = ImageDraw.Draw(img)
    
    # Degradado azul oscuro -> azul claro
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(15 + 50 * t)
        g = int(40 + 120 * t)
        b = int(70 + 140 * t)
        draw.line((0, y, width, y), fill=(r, g, b))
    
    # Panel central
    panel_w, panel_h = 240, 180
    x0 = (width - panel_w) // 2
    y0 = (height - panel_h) // 2
    
    draw.rounded_rectangle((x0, y0, x0 + panel_w, y0 + panel_h), radius=15, fill=(15, 50, 85))
    draw.rounded_rectangle((x0 + 4, y0 + 4, x0 + panel_w - 4, y0 + panel_h - 4), radius=13, fill=(20, 60, 100))
    
    # Texto
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 16)
    except:
        font_big = font_small = ImageFont.load_default()
    
    text1 = "ESP32-P4"
    text2 = "320×480 · ST7796"
    
    bbox1 = draw.textbbox((0, 0), text1, font=font_big)
    tw1 = bbox1[2] - bbox1[0]
    x1 = (width - tw1) // 2
    y1 = y0 + 40
    
    bbox2 = draw.textbbox((0, 0), text2, font=font_small)
    tw2 = bbox2[2] - bbox2[0]
    x2 = (width - tw2) // 2
    y2 = y1 + 50
    
    draw.text((x1, y1), text1, fill=(200, 240, 255), font=font_big)
    draw.text((x2, y2), text2, fill=(120, 200, 240), font=font_small)
    
    # Línea decorativa
    draw.line((x0 + 20, y2 + 40, x0 + panel_w - 20, y2 + 40), fill=(80, 180, 220), width=2)
    
    # Guardar PNG
    png_path = output_bin.replace('.bin', '.png')
    img.save(png_path)
    print(f"[✓] PNG generado: {png_path}")
    
    # Convertir a BIN
    convert_image_to_bin(png_path, output_bin, width, height, swap=swap, bgr=bgr)


def main():
    parser = argparse.ArgumentParser(
        description="Generador de boot screen para Waveshare ESP32-P4-WIFI6-Touch-LCD-3.5\" (ST7796 320x480)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 tools/make_boot_screen.py
  python3 tools/make_boot_screen.py mi_imagen.png
  python3 tools/make_boot_screen.py imagen.jpg --swap --bgr
        """
    )
    
    parser.add_argument("input", nargs="?", help="Imagen de entrada (PNG/JPG). Si no especifica, genera imagen por defecto")
    parser.add_argument("--output", default="assets/boot_screen_320x480.bin", help="Archivo BIN de salida")
    parser.add_argument("--swap", action="store_true", help="Usar big-endian en lugar de little-endian")
    parser.add_argument("--bgr", action="store_true", help="Intercambiar canales R y B (BGR en lugar de RGB)")
    parser.add_argument("--landscape", action="store_true", help="Generar para orientación landscape (480x320)")
    
    args = parser.parse_args()
    
    width = 480 if args.landscape else LCD_WIDTH
    height = 320 if args.landscape else LCD_HEIGHT
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    
    if not args.input:
        generate_default_image(args.output, width, height, swap=args.swap, bgr=args.bgr)
    else:
        convert_image_to_bin(args.input, args.output, width, height, swap=args.swap, bgr=args.bgr)


if __name__ == "__main__":
    main()
