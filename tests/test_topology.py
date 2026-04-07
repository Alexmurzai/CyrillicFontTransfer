import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.pointPen import AbstractPointPen
from core.cyrillic_builder import CyrillicBuilder
from core.font_utils import render_font_sample

class StretchPointPen(AbstractPointPen):
    def __init__(self, out_pen, x_threshold, shift_x):
        self.out_pen = out_pen
        self.x_threshold = x_threshold
        self.shift_x = shift_x

    def beginPath(self, **kwargs):
        self.out_pen.beginPath(**kwargs)

    def endPath(self):
        self.out_pen.endPath()

    def addPoint(self, pt, segmentType=None, color=None, name=None, **kwargs):
        x, y = pt
        if x > self.x_threshold:
            x += self.shift_x
        self.out_pen.addPoint((x, y), segmentType=segmentType, color=color, name=name, **kwargs)

    def addComponent(self, baseGlyphName, transformation, **kwargs):
        self.out_pen.addComponent(baseGlyphName, transformation, **kwargs)


def test_topology():
    builder = CyrillicBuilder()
    source = r'D:\applications\CyrillicFontTransfer\All fonts from Office 365 [v4.37 from 2023-10-10]\Perpetua Titling MT Light.ttf'
    font = TTFont(source)
    cmap = font.getBestCmap()

    # 1. Сначала Г
    builder._transform_glyph(font, cmap[0x004C], "uni0413", mode="v-mirror")
    
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
    
    # Сдвиг для правой стенки I
    shift_x = full_width - i_xmax - lsb
    
    # Сдвиг концовки Г. Нужно найти контрольные точки на правом конце Г и сдвинуть их вправо на gap.
    gap = shift_x + i_xmin - g_xmax + (i_xmax - i_xmin) # Добавляем небольшой нахлест
    
    from fontTools.pens.pointPen import PointToSegmentPen, SegmentToPointPen
    
    stretched_pen = RecordingPen()
    # Конвертер: RecordingPen -> Распаковка в PointPen -> Растягивание -> Сборка в SegmentPen -> RecordingPen
    point_pen_adapter = PointToSegmentPen(stretched_pen)
    stretcher = StretchPointPen(point_pen_adapter, x_threshold=g_xmax - 50, shift_x=gap)
    segment_to_point = SegmentToPointPen(stretcher)
    
    pen.replay(segment_to_point)
    
    # Теперь I сверху
    t_pen = TransformPen(stretched_pen, (1, 0, 0, 1, shift_x, 0))
    i_glyph.draw(t_pen)
    
    builder._set_glyph_from_pen(font, "uni041F", stretched_pen, width_source_name)
    
    output = 'generated_fonts/test_topology.ttf'
    font.save(output)
    
    # Render preview
    img = render_font_sample(output, text="П Г I", size=(400, 200), font_size=50)
    img.save('generated_fonts/test_topology.png')
    print("Test topology finished and saved!")

if __name__ == '__main__':
    test_topology()
