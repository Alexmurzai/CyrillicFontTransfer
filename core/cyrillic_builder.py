import os
import shutil
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointPen import AbstractPointPen, PointToSegmentPen, SegmentToPointPen

class StretchPointPen(AbstractPointPen):
    """
    Адаптер для топологического вытягивания контура: 
    сдвигает все контрольные точки, лежащие правее x_threshold, на shift_x пикселей вправо.
    Идеально для удлинения горизонтальных перекладин.
    """
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

class CyrillicBuilder:
    """
    Процедурный генератор кириллических глифов.
    Служит для алгоритмической сборки кириллицы из латинских глифов исходного TTF-шрифта.
    """
    def __init__(self):
        self.is_loaded = True
        # Кодировки (Latin -> Cyrillic) - Прямые омоглифы
        self.mapping = {
            # Заглавные
            0x0041: 0x0410, # A -> А
            0x0042: 0x0412, # B -> В
            0x0045: 0x0415, # E -> Е
            0x004B: 0x041A, # K -> К
            0x004D: 0x041C, # M -> М
            0x0048: 0x041D, # H -> Н
            0x004F: 0x041E, # O -> О
            0x0050: 0x0420, # P -> Р
            0x0043: 0x0421, # C -> С
            0x0054: 0x0422, # T -> Т
            0x0058: 0x0425, # X -> Х
            
            # Строчные
            0x0061: 0x0430, # a -> а
            0x0065: 0x0435, # e -> е
            0x006F: 0x043E, # o -> о
            0x0070: 0x0440, # p -> р
            0x0063: 0x0441, # c -> с
            0x0078: 0x0445, # x -> х
            0x0079: 0x0443, # y -> у
        }

    def build_cyrillic(self, source_ttf_path: str, output_ttf_path: str):
        """
        Читает исходный латинский шрифт и достраивает кириллицу методом маппинга и векторного синтеза.
        Возвращает список (report) произведенных изменений.
        """
        if not os.path.exists(source_ttf_path):
            raise FileNotFoundError(f"Source font not found: {source_ttf_path}")
            
        font = TTFont(source_ttf_path)
        cmap = font.getBestCmap()
        if cmap is None:
            raise ValueError(f"Не удалось получить таблицу символов (cmap) для шрифта {os.path.basename(source_ttf_path)}. Это может быть символьный (Symbol) или битый шрифт.")
            
        report = []
        changed = False
        
        # 1. Прямое копирование (Homoglyphs)
        # Для базовых омоглифов (А, В, Е...) копируем только если их НЕТ в шрифте,
        # либо если мы хотим форсировать (но обычно омоглифы идентичны).
        for lat_code, cyr_code in self.mapping.items():
            if lat_code in cmap:
                glyph_name = cmap[lat_code]
                if cyr_code not in cmap:
                    self._add_to_cmap(font, cyr_code, glyph_name)
                    report.append(f"Копирование: {chr(lat_code)} -> {chr(cyr_code)}")
                    changed = True
                else:
                    # Опционально: можно перезаписывать, если там 'пустой' глиф
                    pass

        # 2. Продвинутый контурный синтез (Contour-based)
        # ВАЖНО: Эти буквы мы будем СИНТЕЗИРОВАТЬ ВСЕГДА, даже если в шрифте 
        # есть какая-то кириллица (часто она низкого качества или "заглушка").
        
        # --- БУКВА И (ИЗ N) [H-mirror] ---
        if 0x004E in cmap:
            self._transform_glyph(font, cmap[0x004E], "uni0418", mode="h-mirror")
            self._add_to_cmap(font, 0x0418, "uni0418", overwrite=True)
            report.append("Синтез: И (из N, зеркально)")
            changed = True
            
        # --- БУКВА Г (ИЗ L) [V-mirror] ---
        if 0x004C in cmap:
            self._transform_glyph(font, cmap[0x004C], "uni0413", mode="v-mirror")
            self._add_to_cmap(font, 0x0413, "uni0413", overwrite=True)
            report.append("Синтез: Г (из L, зеркально)")
            changed = True

        # --- БУКВА Л (ИЗ V) [V-mirror] ---
        if 0x0056 in cmap:
            self._transform_glyph(font, cmap[0x0056], "uni041B", mode="v-mirror")
            self._add_to_cmap(font, 0x041B, "uni041B", overwrite=True)
            report.append("Синтез: Л (из V, зеркально)")
            changed = True

        # --- БУКВА Я (ИЗ R) [H-mirror] ---
        if 0x0052 in cmap:
            self._transform_glyph(font, cmap[0x0052], "uni042F", mode="h-mirror")
            self._add_to_cmap(font, 0x042F, "uni042F", overwrite=True)
            report.append("Синтез: Я (из R, зеркально)")
            changed = True

        # --- БУКВА П (ИЗ Г + I) ---
        if 0x0047 in cmap or 0x0413 in cmap or "uni0413" in font.getGlyphOrder():
            # Нам нужно Г (уже синтезированное) и I
            g_name = "uni0413" if "uni0413" in font.getGlyphOrder() else (cmap.get(0x0413) or cmap.get(0x0047))
            if g_name and 0x0049 in cmap:
                # Используем ширину от H для профессионального баланса
                width_source = cmap.get(0x0048, cmap[0x0049])
                self._synthesize_pi(font, g_name, cmap[0x0049], "uni041F", width_source)
                self._add_to_cmap(font, 0x041F, "uni041F", overwrite=True)
                report.append("Синтез: П (сборка из Г и I, с мостом)")
                changed = True
                
        # --- ФАЗА 2: Буквы на основе П (Ц, Ш, Щ) ---
        if "uni041F" in font.getGlyphOrder() or 0x041F in cmap:
            p_name = "uni041F" if "uni041F" in font.getGlyphOrder() else cmap[0x041F]
            
            # Ц (зеркало П + хвостик)
            self._synthesize_tse(font, p_name, "uni0426", cmap.get(0x0048, cmap[0x0049]))
            self._add_to_cmap(font, 0x0426, "uni0426", overwrite=True)
            report.append("Синтез: Ц (на основе П с хвостиком)")
            
            # Ш (зеркало П + центральная I)
            if 0x0049 in cmap:
                self._synthesize_sha(font, p_name, cmap[0x0049], "uni0428", cmap.get(0x0048, cmap[0x0049]))
                self._add_to_cmap(font, 0x0428, "uni0428", overwrite=True)
                report.append("Синтез: Ш (Ц-база + центральная мачта I)")
                
                # Щ (Ш + хвостик)
                self._synthesize_shcha(font, "uni0428", "uni0429", cmap.get(0x0048, cmap[0x0049]))
                self._add_to_cmap(font, 0x0429, "uni0429", overwrite=True)
                report.append("Синтез: Щ (Ш с хвостиком)")
        # --- ФАЗА 3: Буквы Ф и Ж
        if 0x0030 in cmap and 0x0049 in cmap:
            # Ф (из 0 и I)
            self._synthesize_ef(font, cmap[0x0030], cmap[0x0049], "uni0424", cmap[0x0049])
            self._add_to_cmap(font, 0x0424, "uni0424", overwrite=True)
            report.append("Синтез: Ф (повернутый 0 + мачта I)")
            changed = True
            
        if 0x0058 in cmap and 0x0049 in cmap:
            # Ж (из X растянутого на 1.5x и I)
            self._synthesize_zhe(font, cmap[0x0058], cmap[0x0049], "uni0416", cmap[0x0058])
            self._add_to_cmap(font, 0x0416, "uni0416", overwrite=True)
            report.append("Синтез: Ж (X растянутый до 1.5x + мачта I)")
            changed = True

        if changed:
            font.save(output_ttf_path)
            report.append(f"Файл сохранен: {output_ttf_path}")
        else:
            shutil.copy2(source_ttf_path, output_ttf_path)
            report.append("Изменений не зафиксировано, файл скопирован")
            
        return report

    def _add_to_cmap(self, font, code_point, glyph_name, overwrite=False):
        """Вспомогательный метод для добавления маппинга во все Unicode таблицы."""
        for table in font['cmap'].tables:
            if table.isUnicode() or table.format > 0:
                if overwrite or code_point not in table.cmap:
                    try:
                        table.cmap[code_point] = glyph_name
                    except:
                        continue

    def _get_glyph_box(self, font, glyph_name):
        """Возвращает (xmin, ymin, xmax, ymax) глифа, используя BoundsPen."""
        glyph_set = font.getGlyphSet()
        if glyph_name not in glyph_set:
            return 0, 0, 0, 0
            
        pen = BoundsPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        return pen.bounds if pen.bounds else (0, 0, 0, 0)

    def _transform_glyph(self, font, source_name, target_name, mode="h-mirror"):
        """Трансформирует глиф (зеркалирование) и сохраняет как новый."""
        glyph_set = font.getGlyphSet()
        if source_name not in glyph_set:
            return

        source_glyph = glyph_set[source_name]
        pen = RecordingPen()
        source_glyph.draw(pen)
        
        xmin, ymin, xmax, ymax = self._get_glyph_box(font, source_name)
        
        target_pen = RecordingPen()
        if mode == "h-mirror":
            transformation = (-1, 0, 0, 1, (xmax + xmin), 0)
        elif mode == "v-mirror":
            transformation = (1, 0, 0, -1, 0, (ymax + ymin))
        else:
            transformation = (1, 0, 0, 1, 0, 0)
            
        t_pen = TransformPen(target_pen, transformation)
        pen.replay(t_pen)
        self._set_glyph_from_pen(font, target_name, target_pen, source_name)

    def _synthesize_pi(self, font, gamma_name, i_name, target_name, width_source_name):
        """Синтезирует П из Г и I (дотягиванием перекладины, без костыльных прямоугольников)."""
        glyph_set = font.getGlyphSet()
        if gamma_name not in glyph_set or i_name not in glyph_set:
            return

        gamma_glyph = glyph_set[gamma_name]
        pen = RecordingPen()
        gamma_glyph.draw(pen)
        
        i_glyph = glyph_set[i_name]
        g_xmin, g_ymin, g_xmax, g_ymax = self._get_glyph_box(font, gamma_name)
        i_xmin, i_ymin, i_xmax, i_ymax = self._get_glyph_box(font, i_name)
        
        # Получаем желаемую ширину (из H)
        full_width = font['hmtx'][width_source_name][0]
        lsb = font['hmtx'][width_source_name][1]
        
        # Сдвигаем правую стойку (I) к правому краю буквы H (или расчетной ширине)
        shift_x = full_width - i_xmax - lsb
        
        # ТОПОЛОГИЧЕСКИЙ СДВИГ (Удлинение правого края Г)
        # Находим точки на "носике" Г (которые правее g_xmax - 50) и сдвигаем до левого края I
        gap_to_cover = shift_x + i_xmin - g_xmax + (i_xmax - i_xmin)*1.2 # захлест внутрь I
        
        stretched_pen = RecordingPen()
        if gap_to_cover > 0:
            pp_adapter = PointToSegmentPen(stretched_pen)
            stretcher = StretchPointPen(pp_adapter, x_threshold=g_xmax - 60, shift_x=gap_to_cover)
            sp_adapter = SegmentToPointPen(stretcher)
            pen.replay(sp_adapter)
        else:
            pen.replay(stretched_pen)
        
        t_pen = TransformPen(stretched_pen, (1, 0, 0, 1, shift_x, 0))
        i_glyph.draw(t_pen)
        
        self._set_glyph_from_pen(font, target_name, stretched_pen, width_source_name)

    def _set_glyph_from_pen(self, font, glyph_name, recording_pen, template_name):
        """Утилита для записи RecordingPen в таблицу glyf."""
        if 'glyf' in font:
            from fontTools.pens.ttGlyphPen import TTGlyphPen
            tt_pen = TTGlyphPen(font.getGlyphSet())
            recording_pen.replay(tt_pen)
            
            font['glyf'][glyph_name] = tt_pen.glyph()
            if glyph_name not in font.getGlyphOrder():
                font.setGlyphOrder(font.getGlyphOrder() + [glyph_name])
            
            if 'hmtx' in font:
                # Копируем метрики из шаблона (например, ширину буквы H для буквы П)
                font['hmtx'][glyph_name] = font['hmtx'][template_name]

    def _draw_tail(self, font, pen, base_glyph_name):
        """Рисует процедурный хвостик (десцендер) для Ц и Щ."""
        xmin, ymin, xmax, ymax = self._get_glyph_box(font, base_glyph_name)
        tail_w = (xmax - xmin) * 0.12 # примерно 12% ширины
        tail_h = ymax * 0.20 # 20% высоты
        
        tx1 = xmax - tail_w
        tx2 = xmax
        ty1 = ymin - tail_h
        ty2 = ymin
        
        # CCW / CW - рисуем квадратик
        if tx2 > tx1:
            pen.moveTo((tx1, ty1))
            pen.lineTo((tx1, ty2))
            pen.lineTo((tx2, ty2))
            pen.lineTo((tx2, ty1))
            pen.closePath()

    def _synthesize_tse(self, font, p_name, target_name, width_source_name):
        """Ц: Зеркальная (вверх ногами) П + хвостик."""
        self._transform_glyph(font, p_name, target_name, mode="v-mirror")
        
        # Добавляем хвостик
        glyph = font.getGlyphSet()[target_name]
        pen = RecordingPen()
        glyph.draw(pen)
        
        self._draw_tail(font, pen, target_name)
        self._set_glyph_from_pen(font, target_name, pen, width_source_name)

    def _synthesize_sha(self, font, p_name, i_name, target_name, width_source_name):
        """Ш: Ц-база вытянутая до 1.5x ширины + I в центре."""
        self._transform_glyph(font, p_name, target_name, mode="v-mirror")
        
        sha_glyph = font.getGlyphSet()[target_name]
        pen = RecordingPen()
        sha_glyph.draw(pen)
        
        i_glyph = font.getGlyphSet()[i_name]
        i_xmin, i_ymin, i_xmax, i_ymax = self._get_glyph_box(font, i_name)
        p_xmin, p_ymin, p_xmax, p_ymax = self._get_glyph_box(font, target_name)
        
        # 1.5x ширины
        full_width = font['hmtx'][width_source_name][0]
        extra_width = int(full_width * 0.5)
        
        # Топологический сдвиг: всё, что правее центра Ц_base, двигаем вправо на extra_width
        center_x = (p_xmax + p_xmin) / 2
        stretched_pen = RecordingPen()
        
        pp_adapter = PointToSegmentPen(stretched_pen)
        stretcher = StretchPointPen(pp_adapter, x_threshold=center_x, shift_x=extra_width)
        sp_adapter = SegmentToPointPen(stretcher)
        
        pen.replay(sp_adapter)
        
        # Сдвиг I в новый центр
        new_width = p_xmax - p_xmin + extra_width
        new_center_x = p_xmin + new_width / 2
        
        i_width = i_xmax - i_xmin
        shift_center = new_center_x - i_width/2 - i_xmin
        
        t_pen = TransformPen(stretched_pen, (1, 0, 0, 1, shift_center, 0))
        i_glyph.draw(t_pen)
        
        self._set_glyph_from_pen(font, target_name, stretched_pen, width_source_name)
        if 'hmtx' in font:
            metrics = font['hmtx'][width_source_name]
            font['hmtx'][target_name] = (int(metrics[0] * 1.5), metrics[1])

    def _synthesize_shcha(self, font, sha_name, target_name, width_source_name):
        """Щ: Ш + хвостик."""
        # Просто копируем Ш (без трансформаций)
        self._transform_glyph(font, sha_name, target_name, mode="none")
        
        glyph = font.getGlyphSet()[target_name]
        pen = RecordingPen()
        glyph.draw(pen)
        
        self._draw_tail(font, pen, target_name)
        self._set_glyph_from_pen(font, target_name, pen, width_source_name)

    def _synthesize_ef(self, font, zero_name, i_name, target_name, width_source_name):
        """Ф: Повернутый на 90 градусов '0' + мачта I по центру."""
        glyph_set = font.getGlyphSet()
        if zero_name not in glyph_set or i_name not in glyph_set:
            return
            
        zero_glyph = glyph_set[zero_name]
        i_glyph = glyph_set[i_name]
        
        z_xmin, z_ymin, z_xmax, z_ymax = self._get_glyph_box(font, zero_name)
        i_xmin, i_ymin, i_xmax, i_ymax = self._get_glyph_box(font, i_name)
        
        # Центр овала
        cx = (z_xmax + z_xmin) / 2.0
        cy = (z_ymax + z_ymin) / 2.0
        
        # Матрица поворота на 90 градусов (cos=0, sin=1)
        # x' = -y + (cx + cy)
        # y' = x + (cy - cx)
        tx = cx + cy
        ty = cy - cx
        
        pen = RecordingPen()
        t_pen = TransformPen(pen, (0, 1, -1, 0, tx, ty))
        zero_glyph.draw(t_pen)
        
        # Центрируем I
        i_width = i_xmax - i_xmin
        shift_center = cx - (i_width / 2.0) - i_xmin
        
        ti_pen = TransformPen(pen, (1, 0, 0, 1, shift_center, 0))
        i_glyph.draw(ti_pen)
        
        # Обновляем метрики до реальной ширины повернутого овала
        rotated_width = z_ymax - z_ymin
        lsb = font['hmtx'][width_source_name][1]
        
        self._set_glyph_from_pen(font, target_name, pen, width_source_name)
        if 'hmtx' in font:
            font['hmtx'][target_name] = (int(rotated_width + lsb*2), lsb)

    def _synthesize_zhe(self, font, x_name, i_name, target_name, width_source_name):
        """Ж: X, растянутый в 1.5 раза через сдвиг правой половины + I в центре."""
        glyph_set = font.getGlyphSet()
        if x_name not in glyph_set or i_name not in glyph_set:
            return
            
        x_glyph = glyph_set[x_name]
        i_glyph = glyph_set[i_name]
        
        x_xmin, x_ymin, x_xmax, x_ymax = self._get_glyph_box(font, x_name)
        i_xmin, i_ymin, i_xmax, i_ymax = self._get_glyph_box(font, i_name)
        
        x_width = font['hmtx'][x_name][0]
        extra_width = int(x_width * 0.5)
        
        center_x = (x_xmax + x_xmin) / 2.0
        
        pen = RecordingPen()
        pp_adapter = PointToSegmentPen(pen)
        stretcher = StretchPointPen(pp_adapter, x_threshold=center_x, shift_x=extra_width)
        sp_adapter = SegmentToPointPen(stretcher)
        
        x_glyph.draw(sp_adapter)
        
        # Сдвиг I в новый центр
        new_width = x_xmax - x_xmin + extra_width
        new_center_x = x_xmin + new_width / 2.0
        
        i_width = i_xmax - i_xmin
        shift_center = new_center_x - (i_width / 2.0) - i_xmin
        
        ti_pen = TransformPen(pen, (1, 0, 0, 1, shift_center, 0))
        i_glyph.draw(ti_pen)
        
        self._set_glyph_from_pen(font, target_name, pen, width_source_name)
        if 'hmtx' in font:
            metrics = font['hmtx'][x_name]
            font['hmtx'][target_name] = (int(metrics[0] * 1.5), metrics[1])

