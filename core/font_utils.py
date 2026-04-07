"""
Утилиты для работы со шрифтами. Отрисовка текста + анализ глифов.
"""

import functools
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

# ── Кириллические кодовые точки для проверки глифов ──────────────────────────
# Проверяем подмножество А-Я (U+0410…U+042F) + а-я (U+0430…U+044F)
_CYRILLIC_SAMPLE = [
    0x0410, 0x0411, 0x0412, 0x0413, 0x041E, 0x041F,  # А Б В Г О П
    0x0420, 0x0421, 0x0422, 0x0423,                    # Р С Т У
    0x0430, 0x0431, 0x0432, 0x0433, 0x043E, 0x043F,  # а б в г о п
]
_MIN_CYRILLIC_GLYPHS = 8  # Минимум совпадений, чтобы считать шрифт кириллическим

# Тёмные цвета UI-приложения
_BG_DARK  = (37, 42, 64)    # BG_DRAG #252A40
_TEXT_LITE = (220, 220, 235) # почти белый


@functools.lru_cache(maxsize=4096)
def has_cyrillic(font_path: str) -> bool:
    """
    Возвращает True, если TTF/OTF шрифт содержит достаточно кириллических глифов
    (минимум _MIN_CYRILLIC_GLYPHS из _CYRILLIC_SAMPLE).

    Использует fonttools для проверки cmap таблицы.
    Результат кэшируется: первичный вызов ~2–5 мс, повторный — мгновенный.
    """
    try:
        from fontTools.ttLib import TTFont  # noqa: PLC0415
        tt = TTFont(font_path, lazy=True)
        cmap = tt.getBestCmap()
        if cmap is None:
            return False
        count = sum(1 for cp in _CYRILLIC_SAMPLE if cp in cmap)
        return count >= _MIN_CYRILLIC_GLYPHS
    except Exception:
        return False


# Набор fallback-строк: пробуем от кириллицы к латинице к символам
_FALLBACK_TEXTS = [
    "АБВГД ЕЖЗИЙ\nКЛМНО ПРСТУ",   # кириллица
    "ABCDE FGHIJ\nKLMNO PQRST",    # латиница
    "12345 67890\nABCDE FGHIJ",    # цифры + латиница
    "!@#$% ^&*()\n<>?/\\|~`±",     # символы
]

_ALPHABET_TEXTS = [
    (
        "А Б В Г Д Е Ё Ж З И Й\n"
        "К Л М Н О П Р С Т У Ф\n"
        "Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я\n"
        "а б в г д е ё ж з и й\n"
        "к л м н о п р с т у ф\n"
        "х ц ч ш щ ъ ы ь э ю я\n"
        "0 1 2 3 4 5 6 7 8 9"
    ),
    (
        "A B C D E F G H I J K\n"
        "L M N O P Q R S T U V\n"
        "W X Y Z a b c d e f g\n"
        "h i j k l m n o p q r\n"
        "s t u v w x y z\n"
        "0 1 2 3 4 5 6 7 8 9"
    ),
    "! @ # $ % ^ & * ( ) < > ? /",
]


def _image_has_drawing(img: Image.Image, threshold: float = 0.97) -> bool:
    """
    Возвращает True, если изображение содержит хоть какой-то нарисованный контент,
    а не является монотонным (пустым) полотном.
    threshold=0.97 → если >97 % пикселей одного цвета — считаем пустым.
    """
    pixels = list(img.getdata())
    if not pixels:
        return False
    dominant = max(set(pixels), key=pixels.count)
    ratio = pixels.count(dominant) / len(pixels)
    return ratio < threshold


def render_font_sample(
    font_path: str,
    text: str = "АБВГД\nЕЖЗИЙ\nКЛМНО",
    size: tuple[int, int] = (224, 224),
    font_size: int = 24,
    bg_color: tuple | str = _BG_DARK,
    text_color: tuple | str = _TEXT_LITE,
    smart_fallback: bool = True,
) -> Optional[Image.Image]:
    """
    Рендерит текст шрифтом из .ttf/.otf файла в тёмном стиле приложения.

    smart_fallback=True: если символы не отображаются (шрифт не поддерживает
    Unicode-блок), автоматически подбирает альтернативную строку.
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"[Font Error] Не удалось загрузить '{font_path}': {e}")
        return None

    def _render(txt: str) -> Image.Image:
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)
        try:
            bbox = draw.textbbox((0, 0), txt, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            bbox = (0, 0, 0, 0)
            text_w = text_h = 0

        x = max(4, (size[0] - text_w) // 2)
        y = max(4, (size[1] - text_h) // 2)
        draw.text((x, y), txt, fill=text_color, font=font)
        return img

    # Пробуем переданный текст
    img = _render(text)
    if not smart_fallback or _image_has_drawing(img):
        return img

    # Автоматический fallback: подбираем текст, который шрифт может отобразить
    for fallback in _FALLBACK_TEXTS:
        img = _render(fallback)
        if _image_has_drawing(img):
            return img

    # Если ничего не вышло — вернём пустой canvas с подписью
    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)
    note_font = ImageFont.load_default()
    draw.text((6, size[1] // 2 - 8), "символьный / декоративный шрифт", fill=(100, 110, 140), font=note_font)
    return img


def render_alphabet(
    font_path: str,
    size: tuple[int, int] = (800, 400),
    font_size: int = 28,
    bg_color: tuple | str = _BG_DARK,
    text_color: tuple | str = _TEXT_LITE,
) -> Optional[Image.Image]:
    """
    Рендерит полный алфавит (А-Я + a-я + 0-9) с умным fallback на латиницу.
    Используется в AlphabetWindow.
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"[Font Error] Не удалось загрузить '{font_path}': {e}")
        return None

    def _render(txt: str) -> Image.Image:
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)
        draw.multiline_text((16, 16), txt, fill=text_color, font=font, spacing=8)
        return img

    for alphabet in _ALPHABET_TEXTS:
        img = _render(alphabet)
        if _image_has_drawing(img):
            return img

    return _render(_ALPHABET_TEXTS[-1])
