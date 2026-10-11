#!/usr/bin/env python3
"""
Conversor de imágenes a formato BIN para ESP32-P4 LCD 3.5"
Genera un archivo .bin listo para flashear en la partición de datos
"""

from PIL import Image
import struct
import os
import sys

class ImageToBin:
    def __init__(self, width=320, height=240):
        self.width = width
        self.height = height
        
    def rgb888_to_rgb565(self, r, g, b):
        """Convierte RGB888 a RGB565 (16 bits)"""
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F
        b5 = (b >> 3) & 0x1F
        rgb565 = (r5 << 11) | (g6 << 5) | b5
        return rgb565
    
    def convert_image(self, input_path, output_path, resize=True):
        """Convierte imagen a BIN para LCD"""
        try:
            # Abrir imagen
            img = Image.open(input_path)
            print(f"[✓] Imagen cargada: {img.size}")
            
            # Redimensionar si es necesario
            if resize:
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                print(f"[✓] Redimensionada a: {self.width}x{self.height}")
            
            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')
                print(f"[✓] Convertida a RGB")
            
            # Crear archivo BIN
            bin_data = bytearray()
            pixels = img.load()
            
            # Procesar píxeles
            for y in range(self.height):
                for x in range(self.width):
                    r, g, b = pixels[x, y]
                    rgb565 = self.rgb888_to_rgb565(r, g, b)
                    # Little-endian (LSB primero, como lo espera el LCD)
                    bin_data.append(rgb565 & 0xFF)
                    bin_data.append((rgb565 >> 8) & 0xFF)
                
                # Progreso
                if (y + 1) % 10 == 0:
                    print(f"[→] Procesando: {y+1}/{self.height} líneas")
            
            # Guardar BIN
            with open(output_path, 'wb') as f:
                f.write(bin_data)
            
            size_kb = len(bin_data) / 1024
            print(f"[✓] Archivo BIN creado: {output_path}")
            print(f"[✓] Tamaño: {size_kb:.2f} KB ({len(bin_data)} bytes)")
            
            return True
            
        except Exception as e:
            print(f"[✗] Error: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 image_converter.py <imagen.jpg> [ancho] [alto]")
        print("Ejemplo: python3 image_converter.py ocean.jpg 320 240")
        sys.exit(1)
    
    input_file = sys.argv[1]
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 320
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 240
    
    output_file = os.path.splitext(input_file)[0] + ".bin"
    
    converter = ImageToBin(width, height)
    converter.convert_image(input_file, output_file)

if __name__ == "__main__":
    main()
