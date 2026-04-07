import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from core.cyrillic_builder import CyrillicBuilder
from core.font_utils import render_font_sample

def test_tse_sha():
    builder = CyrillicBuilder()
    source = r'D:\applications\CyrillicFontTransfer\All fonts from Office 365 [v4.37 from 2023-10-10]\Perpetua Titling MT Light.ttf'
    font = TTFont(source)
    cmap = font.getBestCmap()
    
    # Сначала Г и П
    builder._transform_glyph(font, cmap[0x004C], "uni0413", mode="v-mirror")
    builder._add_to_cmap(font, 0x0413, "uni0413")
    
    builder._synthesize_pi(font, "uni0413", cmap[0x0049], "uni041F", cmap[0x0048])
    builder._add_to_cmap(font, 0x041F, "uni041F")
    
    # 1. Ц_base (зеркало от П)
    builder._transform_glyph(font, "uni041F", "uni0426", mode="v-mirror")
    
    # Добавляем хвостик (tail) для Ц
    tse_glyph = font.getGlyphSet()["uni0426"]
    pen = RecordingPen()
    tse_glyph.draw(pen)
    
    # Хвостик: прямоугольник спускается ниже baseline справа
    xmin, ymin, xmax, ymax = builder._get_glyph_box(font, "uni0426")
    tail_w = (xmax - xmin) * 0.15
    tail_h = ymax * 0.25 # четверть высоты уходит вниз
    
    # Координаты хвостика
    tx1 = xmax - tail_w
    tx2 = xmax
    ty1 = ymin - tail_h
    ty2 = ymin
    
    pen.moveTo((tx1, ty1))
    pen.lineTo((tx1, ty2))
    pen.lineTo((tx2, ty2))
    pen.lineTo((tx2, ty1))
    pen.closePath()
    
    builder._set_glyph_from_pen(font, "uni0426", pen, cmap[0x0048])
    builder._add_to_cmap(font, 0x0426, "uni0426")
    
    # 2. Ш (Ц_base + I по центру)
    builder._transform_glyph(font, "uni041F", "uni0428", mode="v-mirror")
    sha_glyph = font.getGlyphSet()["uni0428"]
    pen_sh = RecordingPen()
    sha_glyph.draw(pen_sh)
    
    i_glyph = font.getGlyphSet()[cmap[0x0049]]
    i_xmin, i_ymin, i_xmax, i_ymax = builder._get_glyph_box(font, cmap[0x0049])
    
    # Ширина П
    p_xmin, p_ymin, p_xmax, p_ymax = builder._get_glyph_box(font, "uni041F")
    
    # Сдвиг I в центр
    center_x = (p_xmax + p_xmin) / 2
    i_width = i_xmax - i_xmin
    shift_center = center_x - i_width/2 - i_xmin
    
    t_pen = TransformPen(pen_sh, (1, 0, 0, 1, shift_center, 0))
    i_glyph.draw(t_pen)
    
    builder._set_glyph_from_pen(font, "uni0428", pen_sh, cmap[0x0048])
    builder._add_to_cmap(font, 0x0428, "uni0428")
    
    # 3. Щ (Ш + хвостик)
    builder._transform_glyph(font, "uni0428", "uni0429", mode="none")
    shcha_glyph = font.getGlyphSet()["uni0429"]
    pen_sch = RecordingPen()
    shcha_glyph.draw(pen_sch)
    
    pen_sch.moveTo((tx1, ty1))
    pen_sch.lineTo((tx1, ty2))
    pen_sch.lineTo((tx2, ty2))
    pen_sch.lineTo((tx2, ty1))
    pen_sch.closePath()
    
    builder._set_glyph_from_pen(font, "uni0429", pen_sch, cmap[0x0048])
    builder._add_to_cmap(font, 0x0429, "uni0429")
    
    output = 'generated_fonts/test_tse_sha.ttf'
    font.save(output)
    
    img = render_font_sample(output, text="Ц Ш Щ П", size=(800, 200), font_size=50)
    img.save('generated_fonts/tse_sha_preview.png')
    print("Test finished!")

if __name__ == '__main__':
    test_tse_sha()
