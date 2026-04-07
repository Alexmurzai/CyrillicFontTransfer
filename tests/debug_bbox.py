from fontTools.ttLib import TTFont
import os

def check_bbox(font_path, char):
    if not os.path.exists(font_path):
        return
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    gname = cmap.get(ord(char))
    if not gname:
        print(f"Char {char} not in {font_path}")
        return
    
    gset = font.getGlyphSet()
    glyph = gset[gname]
    
    print(f"Inspecting {char} ({gname})")
    print(f"Has 'box' attribute? {hasattr(glyph, 'box')}")
    if hasattr(glyph, 'box'):
        print(f"Box: {glyph.box}")
    
    if 'glyf' in font:
        tt_glyph = font['glyf'][gname]
        print(f"xMin: {getattr(tt_glyph, 'xMin', 'N/A')}")
        print(f"xMax: {getattr(tt_glyph, 'xMax', 'N/A')}")

if __name__ == "__main__":
    check_bbox("fonts_db/Abel Regular.ttf", 'N')
