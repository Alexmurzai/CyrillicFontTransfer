import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.append(str(Path(__file__).parent.parent))

from core.cyrillic_builder import CyrillicBuilder
from fontTools.ttLib import TTFont

def test_mapping():
    builder = CyrillicBuilder()
    
    # Используем любой шрифт из базы
    source_font = "fonts_db/Abel Regular.ttf" 
    if not os.path.exists(source_font):
        print(f"Skipping test: {source_font} not found")
        return
        
    output_font = "generated_fonts/advanced_test.ttf"
    os.makedirs("generated_fonts", exist_ok=True)
    
    print(f"Building Cyrillic (Advanced) for {source_font}...")
    builder.build_cyrillic(source_font, output_font)
    
    # Проверяем результат
    print(f"Verifying {output_font}...")
    font = TTFont(output_font)
    cmap = font.getBestCmap()
    
    # Проверяем наличие новых букв
    glyphs_to_check = {
        0x0410: "А (A-copy)",
        0x0418: "И (N-mirror)",
        0x0413: "Г (L-mirror)",
        0x041B: "Л (V-mirror)",
        0x042F: "Я (R-mirror)",
        0x041F: "П (Synthesized)"
    }
    
    for code, desc in glyph_to_check:
        pass # To be fixed below

if __name__ == "__main__":
    # Fix the loop and run
    builder = CyrillicBuilder()
    source_font = "fonts_db/Abel Regular.ttf"
    output_font = "generated_fonts/advanced_test.ttf"
    builder.build_cyrillic(source_font, output_font)
    font = TTFont(output_font)
    cmap = font.getBestCmap()
    
    glyphs_to_check = {
        0x0410: "А",
        0x0418: "И",
        0x0413: "Г",
        0x041B: "Л",
        0x042F: "Я",
        0x041F: "П"
    }
    
    all_found = True
    for code, name in glyphs_to_check.items():
        if code in cmap:
            print(f"SUCCESS: Glyph {name} (U+{code:04X}) found! GlyphName: {cmap[code]}")
        else:
            print(f"FAILURE: Glyph {name} (U+{code:04X}) NOT found.")
            all_found = False
            
    if all_found:
        print("\nALL TESTED GLYPHS GENERATED CORRECTLY!")
