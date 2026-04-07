"""
Модуль для экспорта растровых изображений в векторный формат .ttf
Использует OpenCV для векторизации и fontTools для внедрения глифов в шаблон.
"""

import os
import cv2
import numpy as np
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen

class FontExporter:
    def __init__(self, template_path: str = "fonts_db/arial.ttf"):
        """
        Инициализация экспортера.
        Использует существующий валидный .ttf файл в качестве структурного шаблона,
        чтобы избежать ручного создания всех низкоуровневых таблиц TrueType.
        """
        self.template_path = template_path
        if not os.path.exists(self.template_path):
            # Попытаться взять системный
            system_arial = "C:/Windows/Fonts/arial.ttf"
            if os.path.exists(system_arial):
                self.template_path = system_arial

    def export_to_ttf(self, glyph_image: Image.Image, output_path: str, font_name: str = "CustomCyrillic"):
        """
        Векторизует картинку и сохраняет в ttf.
        Для простоты реализации в этом прототипе:
        Мы конвертируем всё изображение-сетку (алфавит) в один или несколько тестовых глифов.
        В полноценном приложении здесь должна быть нарезка сетки на 66 отдельных букв (А-Я, а-я)
        и сохранение каждой буквы в свой Unicode-слот.
        """
        print(f"[*] Экспорт шрифта {font_name} в {output_path}...")
        
        # 1. Открываем шаблонный шрифт
        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Не найден шаблон {self.template_path}. Экспорт невозможен.")
            
        font = TTFont(self.template_path)
        glyph_set = font.getGlyphSet()
        
        # 2. Подготовка изображения для векторизации
        img_arr = np.array(glyph_image)
        if len(img_arr.shape) == 3:
            gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_arr
            
        # Бинаризация (черный текст на белом фоне -> белые контуры на черном фоне)
        _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
        
        # Нахождение контуров
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_TC89_KCOS)
        
        # В реальной задаче нужно группировать контуры по буквам, используя bounding boxes (x,y,w,h)
        # Здесь мы сохраним всё найденное как один глиф 'A' (или 'space') для демо-сборки,
        # так как алгоритм кластеризации 66 символов со сложным кернингом займет сотни строк.
        
        # Подготовка Pen для рисования контуров прямо в формате TrueType (glyf table)
        pen = TTGlyphPen(glyphSet=glyph_set)
        
        if contours:
            # Масштаб: картинка 512x512, EM шрифта обычно 2048. Scale ~4.0 и инверсия Y
            scale = 4.0
            height = img_arr.shape[0]
            
            for i, contour in enumerate(contours):
                # Пропускаем слишком мелкие артефакты диффузии
                if cv2.contourArea(contour) < 20:
                    continue
                    
                # hierarchy[0][i][3] == -1 означает внешний контур
                # Упрощенно рисуем полигон
                points = []
                for pt in contour:
                    x, y = pt[0]
                    # Перевод из координат изображения (Y вниз) в координаты шрифта (Y вверх)
                    font_x = int(x * scale)
                    font_y = int((height - y) * scale)
                    points.append((font_x, font_y))
                
                if len(points) > 2:
                    pen.moveTo(points[0])
                    for p in points[1:]:
                        pen.lineTo(p)
                    pen.closePath()

        # Получаем готовый TTGlyph
        new_glyph = pen.glyph()
        
        # Записываем его в кириллическую 'А' (U+0410) и латинскую 'A' (U+0041)
        # В fontTools нужно найти имя глифа через cmap:
        cmap = font.getBestCmap()
        glyph_name_A_lat = cmap.get(0x0041) # Латинская А
        glyph_name_A_cyr = cmap.get(0x0410) # Кириллическая А
        
        if glyph_name_A_lat:
            font['glyf'][glyph_name_A_lat] = new_glyph
        if glyph_name_A_cyr:
            font['glyf'][glyph_name_A_cyr] = new_glyph
            
        # Обновляем таблицу имен (Family Name)
        name_table = font['name']
        for record in name_table.names:
            if record.nameID in (1, 4, 16): # 1: FontFamily, 4: FullName, 16: Typographic Family
                try:
                    record.string = font_name.encode(record.getEncoding())
                except:
                    pass

        # Сохранение финального файла
        font.save(output_path)
        print("[+] Экспорт завершен успешно!")
