from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

font = TTFont()
pen = TTGlyphPen(None)
print("Methods in TTGlyphPen:")
print(dir(pen))
