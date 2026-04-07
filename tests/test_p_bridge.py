import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from core.cyrillic_builder import CyrillicBuilder
from core.font_utils import render_font_sample

def test_p_bridge():
    builder = CyrillicBuilder()
    source = r'D:\applications\CyrillicFontTransfer\All fonts from Office 365 [v4.37 from 2023-10-10]\Perpetua Titling MT Light.ttf'
    font = TTFont(source)
    cmap = font.getBestCmap()
    
    # 1. Сначала сгенерируем Г
    # Г = L, v-mirror
    builder._transform_glyph(font, cmap[0x004C], "uni0413", mode="v-mirror")
    builder._add_to_cmap(font, 0x0413, "uni0413")
    
    # 2. П
    gamma_name = "uni0413"
    i_name = cmap[0x0049]
    width_source_name = cmap[0x0048]
    
    gamma_glyph = font.getGlyphSet()[gamma_name]
    pen = RecordingPen()
    gamma_glyph.draw(pen)
    
    i_glyph = font.getGlyphSet()[i_name]
    g_xmin, g_ymin, g_xmax, g_ymax = builder._get_glyph_box(font, gamma_name)
    i_xmin, i_ymin, i_xmax, i_ymax = builder._get_glyph_box(font, i_name)
    
    full_width = font['hmtx'][width_source_name][0]
    lsb = font['hmtx'][width_source_name][1]
    
    shift_x = full_width - i_xmax - lsb
    t_pen = TransformPen(pen, (1, 0, 0, 1, shift_x, 0))
    i_glyph.draw(t_pen)
    
    # Считаем толщину I
    i_thickness = i_xmax - i_xmin
    # Горизонтальные штрихи часто тоньше, умножим на 0.8
    crossbar_thick = i_thickness * 0.8
    
    y2 = g_ymax
    y1 = g_ymax - crossbar_thick
    x1 = g_xmax - 50 # Захлест
    x2 = shift_x + i_xmin + 50 # Захлест
    
    # Прямоугольник: (x1, y1) -> (x1, y2) -> (x2, y2) -> (x2, y1) - по часовой (CW)
    if x2 > x1:
        pen.moveTo((x1, y1))
        pen.lineTo((x1, y2))
        pen.lineTo((x2, y2))
        pen.lineTo((x2, y1))
        pen.closePath()
    
    builder._set_glyph_from_pen(font, "uni041F", pen, width_source_name)
    builder._add_to_cmap(font, 0x041F, "uni041F")
    
    output = 'generated_fonts/test_p_bridge.ttf'
    font.save(output)
    
    # Render preview
    img = render_font_sample(output, text="Г П И H\nАВПГ", size=(800, 200), font_size=50)
    img.save('generated_fonts/p_bridge_preview.png')
    print("Test finished and saved!")

if __name__ == '__main__':
    test_p_bridge()
