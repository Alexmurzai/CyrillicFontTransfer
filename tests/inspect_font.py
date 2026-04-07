from fontTools.ttLib import TTFont
import os

def inspect_glyph(font_path, glyph_char):
    if not os.path.exists(font_path):
        return
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    if ord(glyph_char) not in cmap:
        print(f"{glyph_char} not found in {font_path}")
        return
    
    glyph_name = cmap[ord(glyph_char)]
    print(f"\nInspecting {glyph_char} ({glyph_name}) in {font_path}")
    
    if 'glyf' in font:
        glyph = font['glyf'][glyph_name]
        print(f"Number of contours: {glyph.numberOfContours}")
        # Для простых глифов numberOfContours > 0
        if glyph.numberOfContours > 0:
            for i in range(glyph.numberOfContours):
                # В fontTools точки контуров хранятся в coordinates
                # Но проще использовать pens для анализа
                pass
    elif 'CFF ' in font:
        print("Type: CFF (OpenType)")

if __name__ == "__main__":
    sample_font = "fonts_db/Abel Regular.ttf"
    inspect_glyph(sample_font, 'F')
    inspect_glyph(sample_font, 'H')
    inspect_glyph(sample_font, 'E')
