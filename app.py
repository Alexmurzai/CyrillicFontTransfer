"""
CyrillicFontTransfer — app.py
Главный класс приложения. Шаг 1: Каркас UI.

Все методы бизнес-логики помечены как STUB и будут
реализованы на следующих шагах разработки.
"""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

# Импорт модулей ядра (Шаг 2 и 3)
from core.font_utils import render_font_sample, render_alphabet, has_cyrillic
from core.embedder import StyleEmbedder
from core.vector_db import FontVectorDB
from core.font_recognizer import FontRecognizer
from core.cyrillic_builder import CyrillicBuilder
from core.exporter import FontExporter

# ──────────────────────────────────────────────────────────────────────────────
# Константы и настройки темы
# ──────────────────────────────────────────────────────────────────────────────

APP_TITLE = "CyrillicFontTransfer — Перенос стиля шрифта"
APP_VERSION = "0.1.0"
WINDOW_MIN_W = 1200
WINDOW_MIN_H = 720

# Акцентные цвета (тёмная тема)
ACCENT = "#6C63FF"          # Фиолетовый
ACCENT_HOVER = "#574FCC"
SUCCESS = "#2ECC71"
WARNING = "#F39C12"
ERROR_CLR = "#E74C3C"
BG_CARD = "#1E2235"         # Цвет «карточки» внутри тёмного фона
BG_DRAG = "#252A40"         # Цвет зоны Drag & Drop в обычном состоянии
BG_DRAG_HOVER = "#2E3454"   # Цвет при hover/drop
TEXT_SECONDARY = "#8892B0"  # Приглушённый текст

# Слова-примеры для превью шрифта
PREVIEW_WORDS_CYR = ["Привет", "Алексей", "Шрифт", "Дизайн"]
PREVIEW_WORDS_LAT = ["Hello", "Design", "Font", "Style"]

# Кириллический алфавит + цифры для отображения всех глифов
ALL_GLYPHS = (
    "А Б В Г Д Е Ё Ж З И Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ъ Ы Ь Э Ю Я\n"
    "а б в г д е ё ж з и й к л м н о п р с т у ф х ц ч ш щ ъ ы ь э ю я\n"
    "0 1 2 3 4 5 6 7 8 9"
)


def _apply_theme() -> None:
    """Настройка глобальной темы CustomTkinter."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогательные виджеты
# ──────────────────────────────────────────────────────────────────────────────

class SectionLabel(ctk.CTkLabel):
    """Заголовок раздела с линией-разделителем."""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(
            master,
            text=f"  {text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_SECONDARY,
            anchor="w",
            **kwargs,
        )


class AccentButton(ctk.CTkButton):
    """Кнопка в акцентном цвете."""

    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            **kwargs,
        )


class OutlineButton(ctk.CTkButton):
    """Контурная (outlined) кнопка."""

    def __init__(self, master, text: str, command=None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            fg_color="transparent",
            border_width=2,
            border_color=ACCENT,
            text_color=ACCENT,
            hover_color=BG_DRAG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            height=40,
            **kwargs,
        )


class StatusBar(ctk.CTkFrame):
    """Нижняя строка статуса с прогресс-баром."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=36, corner_radius=0, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._status_var = tk.StringVar(value="Готово к работе")
        self._label = ctk.CTkLabel(
            self,
            textvariable=self._status_var,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self._label.grid(row=0, column=0, padx=12, pady=4, sticky="w")

        self._progress = ctk.CTkProgressBar(self, width=200, height=8)
        self._progress.set(0)
        self._progress.grid(row=0, column=1, padx=12, pady=4)

        self._version = ctk.CTkLabel(
            self,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
        )
        self._version.grid(row=0, column=2, padx=12, pady=4)

    def set_status(self, text: str, color: str = None) -> None:
        self._status_var.set(text)
        if color:
            self._label.configure(text_color=color)
        else:
            self._label.configure(text_color=TEXT_SECONDARY)

    def set_progress(self, value: float) -> None:
        """value: 0.0 – 1.0"""
        self._progress.set(value)

    def start_indeterminate(self) -> None:
        self._progress.configure(mode="indeterminate")
        self._progress.start()

    def stop_indeterminate(self) -> None:
        self._progress.stop()
        self._progress.configure(mode="determinate")
        self._progress.set(0)


# ──────────────────────────────────────────────────────────────────────────────
# Виджет зоны Drag & Drop
# ──────────────────────────────────────────────────────────────────────────────

class DropZone(ctk.CTkFrame):
    """
    Зона для перетаскивания изображения (Drag & Drop).
    Поддерживает как D&D через tkinterdnd2 (если установлен),
    так и загрузку файла через кнопку.
    """

    def __init__(self, master, on_file_loaded, **kwargs):
        super().__init__(
            master,
            corner_radius=16,
            border_width=2,
            border_color=ACCENT,
            fg_color=BG_DRAG,
            **kwargs,
        )
        self.on_file_loaded = on_file_loaded
        self._image_path: Optional[Path] = None
        self._preview_label: Optional[ctk.CTkLabel] = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self._try_enable_dnd()

    # ── Построение UI ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Создаёт внутренние виджеты."""
        self._inner = ctk.CTkFrame(self, fg_color="transparent")
        self._inner.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self._inner.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self._inner.grid_columnconfigure(0, weight=1)

        # Иконка-заглушка (unicode)
        self._icon_label = ctk.CTkLabel(
            self._inner,
            text="🖼",
            font=ctk.CTkFont(size=52),
        )
        self._icon_label.grid(row=0, column=0, pady=(20, 4))

        self._hint_label = ctk.CTkLabel(
            self._inner,
            text="Перетащите изображение с латинским текстом сюда",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SECONDARY,
            wraplength=320,
            justify="center",
        )
        self._hint_label.grid(row=1, column=0, pady=4)

        self._sub_hint = ctk.CTkLabel(
            self._inner,
            text="PNG, JPG, JPEG, BMP, TIFF",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
        )
        self._sub_hint.grid(row=2, column=0, pady=(0, 8))

        self._browse_btn = AccentButton(
            self._inner,
            text="📂  Выбрать файл",
            command=self._browse_file,
            width=160,
        )
        self._browse_btn.grid(row=3, column=0, pady=(4, 20))

    def _try_enable_dnd(self) -> None:
        """Пытается подключить tkinterdnd2 для drag & drop."""
        try:
            import tkinterdnd2  # noqa: F401

            self.drop_target_register(tk.DND_FILES)  # type: ignore[attr-defined]
            self.dnd_bind("<<Drop>>", self._on_drop)  # type: ignore[attr-defined]
            self.dnd_bind("<<DragEnter>>", self._on_drag_enter)  # type: ignore[attr-defined]
            self.dnd_bind("<<DragLeave>>", self._on_drag_leave)  # type: ignore[attr-defined]
        except Exception:
            # tkinterdnd2 не установлен — работаем только через кнопку
            self._sub_hint.configure(
                text="PNG, JPG, JPEG · Drag & Drop недоступен (см. README)"
            )

    # ── Обработчики событий ───────────────────────────────────────────────

    def _on_drag_enter(self, event) -> None:
        self.configure(border_color=SUCCESS)
        self._inner.configure(fg_color=BG_DRAG_HOVER)

    def _on_drag_leave(self, event) -> None:
        self.configure(border_color=ACCENT)
        self._inner.configure(fg_color="transparent")

    def _on_drop(self, event) -> None:
        self._on_drag_leave(event)
        raw_path = event.data.strip("{}")
        path = Path(raw_path)
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}:
            self._load_image(path)
        else:
            messagebox.showwarning("Неверный формат", "Поддерживаются: PNG, JPG, JPEG, BMP, TIFF")

    def _browse_file(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Выберите изображение с латинским текстом",
            filetypes=[
                ("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("Все файлы", "*.*"),
            ],
        )
        if path_str:
            self._load_image(Path(path_str))

    def _load_image(self, path: Path) -> None:
        """Загружает и отображает превью изображения внутри DropZone."""
        self._image_path = path
        try:
            img = Image.open(path).convert("RGB")
            # Ограничиваем размер превью
            img.thumbnail((320, 200), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=img.size)

            # Скрываем placeholder-элементы
            for w in (self._icon_label, self._hint_label, self._sub_hint):
                w.grid_remove()

            if self._preview_label is None:
                self._preview_label = ctk.CTkLabel(self._inner, text="", image=ctk_img)
                self._preview_label.grid(row=0, column=0, rowspan=3, pady=(12, 4))
            else:
                self._preview_label.configure(image=ctk_img)
                self._preview_label.grid()

            # Показываем имя файла под превью
            self._browse_btn.configure(text=f"📂  {path.name}")

        except Exception as e:
            messagebox.showerror("Ошибка загрузки", str(e))
            return

        # Уведомляем родительский виджет
        if self.on_file_loaded:
            self.on_file_loaded(path)

    # ── Публичный API ──────────────────────────────────────────────────────

    def get_image_path(self) -> Optional[Path]:
        return self._image_path

    def clear(self) -> None:
        """Сбрасывает зону Drag & Drop в начальное состояние."""
        self._image_path = None
        if self._preview_label:
            self._preview_label.grid_remove()
        for w in (self._icon_label, self._hint_label, self._sub_hint):
            w.grid()
        self._browse_btn.configure(text="📂  Выбрать файл")


# ──────────────────────────────────────────────────────────────────────────────
# Панель результатов
# ──────────────────────────────────────────────────────────────────────────────

class ResultPanel(ctk.CTkFrame):
    """Правая панель: превью найденного / сгенерированного кириллического шрифта."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=16, fg_color=BG_CARD, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="Результат",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="w")

        # Блок: распознанный шрифт
        SectionLabel(self, "Распознанный латинский шрифт").grid(
            row=1, column=0, padx=12, pady=(12, 2), sticky="w"
        )
        self._recognized_var = tk.StringVar(value="—")
        self._recognized_label = ctk.CTkLabel(
            self,
            textvariable=self._recognized_var,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=ACCENT,
        )
        self._recognized_label.grid(row=2, column=0, padx=16, pady=(0, 8))

        # Блок: превью кириллического шрифта
        SectionLabel(self, "Найденный / сгенерированный кириллический шрифт").grid(
            row=3, column=0, padx=12, pady=(12, 2), sticky="w"
        )
        self._cyrillic_font_name_var = tk.StringVar(value="—")
        ctk.CTkLabel(
            self,
            textvariable=self._cyrillic_font_name_var,
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY,
        ).grid(row=4, column=0, padx=16, pady=(0, 4))

        self._preview_canvas = ctk.CTkLabel(
            self,
            text="Здесь появится превью",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
            fg_color=BG_DRAG,
            corner_radius=8,
            width=300,
            height=300,
        )
        self._preview_canvas.grid(row=5, column=0, padx=16, pady=4, sticky="ew")

        # Схожесть (confidence)
        SectionLabel(self, "Степень совпадения").grid(
            row=6, column=0, padx=12, pady=(12, 2), sticky="w"
        )
        self._similarity_bar = ctk.CTkProgressBar(self, height=12)
        self._similarity_bar.set(0)
        self._similarity_bar.grid(row=7, column=0, padx=16, pady=(0, 2), sticky="ew")

        self._similarity_var = tk.StringVar(value="0%")
        ctk.CTkLabel(
            self,
            textvariable=self._similarity_var,
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).grid(row=8, column=0, padx=16, pady=(0, 12))

        # Лог событий
        SectionLabel(self, "Лог").grid(
            row=9, column=0, padx=12, pady=(12, 2), sticky="w"
        )
        self._log_box = ctk.CTkTextbox(
            self,
            height=180,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
            wrap="word",
        )
        self._log_box.grid(row=10, column=0, padx=12, pady=(0, 12), sticky="ew")

    # ── Публичный API ──────────────────────────────────────────────────────

    def set_recognized_font(self, name: str) -> None:
        self._recognized_var.set(name)

    def set_cyrillic_preview(
        self,
        font_name: str,
        image: Optional[Image.Image] = None,
        similarity: "float | None" = None,
        generated: bool = False,
    ) -> None:
        self._cyrillic_font_name_var.set(font_name)
        if similarity is not None:
            # Реальное косинусное сходство из векторного поиска
            self._similarity_bar.set(similarity)
            self._similarity_bar.configure(progress_color=ACCENT)
            self._similarity_var.set(f"{int(similarity * 100)}%")
        else:
            # Режим генерации — показываем честную подпись
            self._similarity_bar.set(0)
            self._similarity_bar.configure(progress_color=WARNING)
            self._similarity_var.set("— (SD генерация, не поиск)")

        if image is not None:
            img = image.copy()
            img.thumbnail((300, 300), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=img.size)
            self._preview_canvas.configure(image=ctk_img, text="")
        else:
            self._preview_canvas.configure(image=None, text="Превью недоступно")

    def log(self, message: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"› {message}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def clear(self) -> None:
        self._recognized_var.set("—")
        self._cyrillic_font_name_var.set("—")
        self._preview_canvas.configure(image=None, text="Здесь появится превью")
        self._similarity_bar.set(0)
        self._similarity_bar.configure(progress_color=ACCENT)
        self._similarity_var.set("0%")


# ──────────────────────────────────────────────────────────────────────────────
# Окно алфавита
# ──────────────────────────────────────────────────────────────────────────────

class AlphabetWindow(ctk.CTkToplevel):
    """
    Вспомогательное окно для отображения всех глифов
    (А-Я, а-я, 0-9) найденного / сгенерированного шрифта.
    """

    def __init__(self, master, font_name: str = "—", glyph_image: Optional[Image.Image] = None):
        super().__init__(master)
        self.title(f"Все глифы — {font_name}")
        self.geometry("800x600")
        self.resizable(True, True)
        ctk.set_appearance_mode("dark")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=f"Шрифт: {font_name}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(20, 8))

        if glyph_image is not None:
            img = glyph_image.copy()
            img.thumbnail((760, 480), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=img.size)
            label = ctk.CTkLabel(self, text="", image=ctk_img)
            label.grid(row=1, column=0, padx=20, pady=8)
        else:
            # Placeholder текст
            box = ctk.CTkTextbox(
                self,
                font=ctk.CTkFont(family="Arial", size=24),
                state="disabled",
                wrap="word",
            )
            box.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")
            box.configure(state="normal")
            box.insert("end", ALL_GLYPHS)
            box.configure(state="disabled")

        ctk.CTkButton(
            self,
            text="Закрыть",
            command=self.destroy,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            width=120,
        ).grid(row=2, column=0, pady=(8, 20))


# ──────────────────────────────────────────────────────────────────────────────
# Главное окно приложения
# ──────────────────────────────────────────────────────────────────────────────

class CyrillicFontTransferApp(ctk.CTk):
    """
    Главное окно CyrillicFontTransfer.
    Шаг 3: Реальное распознавание и векторный поиск.
    """

    def __init__(self):
        _apply_theme()
        super().__init__()

        self.title(APP_TITLE)
        self.geometry(f"{WINDOW_MIN_W}x{WINDOW_MIN_H}")
        self.minsize(WINDOW_MIN_W, WINDOW_MIN_H)

        # Текущее состояние
        self._image_path: Optional[Path] = None
        self._recognized_font_name: Optional[str] = None
        self._found_font_name: Optional[str] = None
        self._found_font_path: Optional[str] = None
        self._generated: bool = False

        # Инициализация моделей (по умолчанию None)
        self.embedder: Optional[StyleEmbedder] = None
        self.recognizer: Optional[FontRecognizer] = None
        self.vector_db: Optional[FontVectorDB] = None
        # CyrillicBuilder инициализируется немедленно — он легковесный, не требует GPU
        self.builder = CyrillicBuilder()
        self.exporter = FontExporter()

        self._build_layout()
        
        # Инициализация моделей (асинхронно)
        self._init_models()

    def _init_models(self) -> None:
        """Загрузка нейросетей и базы данных."""
        def _task():
            try:
                self._status_bar.set_status("Инициализация моделей...")
                self._result_panel.log("Загрузка CLIP...")
                self.embedder = StyleEmbedder() # Шаг 2
                
                self._result_panel.log("Загрузка EasyOCR...")
                self.recognizer = FontRecognizer(model_dir="models") # Шаг 3
                
                self._result_panel.log("Подключение к ChromaDB...")
                self.vector_db = FontVectorDB(persist_dir="fonts_db/chroma") # Шаг 2
                
                self._result_panel.log("Инициализация CyrillicBuilder (готов мгновенно)...")
                # builder уже инициализирован в __init__
                
                self._status_bar.set_status("Готово к работе", SUCCESS)
                self._result_panel.log("Все системы готовы.")
                # Активируем кнопки только после полной загрузки
                self.after(0, lambda: self._set_buttons_state("normal"))
            except Exception as e:
                self._result_panel.log(f"Ошибка инициализации: {e}")
                self._status_bar.set_status("Ошибка запуска", ERROR_CLR)

        # Блокируем кнопки на время инициализации
        self._set_buttons_state("disabled")
        self._run_in_thread(_task)

    # ──────────────────────────────────────────────────────────────────────
    # Построение интерфейса
    # ──────────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Создаёт двухколоночный layout приложения."""
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=0)  # header
        self.grid_rowconfigure(1, weight=1)  # content
        self.grid_rowconfigure(2, weight=0)  # status bar

        self._build_header()
        self._build_left_panel()
        self._build_right_panel()
        self._build_status_bar()

    def _build_header(self) -> None:
        """Шапка приложения."""
        header = ctk.CTkFrame(self, corner_radius=0, height=56, fg_color=BG_CARD)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Логотип / название
        ctk.CTkLabel(
            header,
            text="  ✦ CyrillicFontTransfer",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ACCENT,
        ).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        # Подзаголовок
        ctk.CTkLabel(
            header,
            text="Перенос стиля латинских шрифтов на кириллицу · ML-powered",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_SECONDARY,
        ).grid(row=0, column=1, padx=8, pady=12, sticky="w")

        # Кнопка сброса
        ctk.CTkButton(
            header,
            text="🔄  Сбросить",
            command=self._reset_all,
            fg_color="transparent",
            text_color=TEXT_SECONDARY,
            hover_color=BG_DRAG_HOVER,
            width=110,
            height=32,
        ).grid(row=0, column=2, padx=16, pady=12, sticky="e")

    def _build_left_panel(self) -> None:
        """Левая панель: загрузка референса и кнопки действий."""
        left = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color="transparent", label_text=""
        )
        left.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left.grid_columnconfigure(0, weight=1)

        # ── Зона Drag & Drop ──────────────────────────────────────────────
        SectionLabel(left, "ШАГ 1 — Загрузить референс").grid(
            row=0, column=0, padx=4, pady=(4, 4), sticky="w"
        )

        self._drop_zone = DropZone(
            left,
            on_file_loaded=self._on_image_loaded,
            height=260,
        )
        self._drop_zone.grid(row=1, column=0, sticky="ew", pady=(0, 16))

        # ── Кнопки действий ───────────────────────────────────────────────
        SectionLabel(left, "ШАГ 2 — Анализ и поиск").grid(
            row=2, column=0, padx=4, pady=(4, 4), sticky="w"
        )

        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_recognize = AccentButton(
            btn_frame,
            text="🔍  Распознать шрифт",
            command=self._stub_recognize_font,
        )
        self._btn_recognize.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")

        self._btn_search = AccentButton(
            btn_frame,
            text="🎯  Найти в базе",
            command=self._stub_search_font,
        )
        self._btn_search.grid(row=0, column=1, padx=(6, 0), pady=4, sticky="ew")

        # ── Генерация ─────────────────────────────────────────────────────
        SectionLabel(left, "ШАГ 3 — Синтез кириллицы (после поиска или напрямую)").grid(
            row=4, column=0, padx=4, pady=(4, 4), sticky="w"
        )

        self._btn_generate = ctk.CTkButton(
            left,
            text="✨  Сгенерировать кириллический шрифт",
            command=self._stub_generate_cyrillic,
            fg_color=BG_CARD,
            border_width=2,
            border_color=WARNING,
            text_color=WARNING,
            hover_color=BG_DRAG_HOVER,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=44,
        )
        self._btn_generate.grid(row=5, column=0, sticky="ew", pady=(0, 4))
        
        self._btn_open_ttf = AccentButton(
            left,
            text="📂  Выбрать TTF локально и синтезировать",
            command=self._direct_synthesize_from_ttf,
        )
        self._btn_open_ttf.grid(row=6, column=0, sticky="ew", pady=(0, 8))

        self._generate_hint = ctk.CTkLabel(
            left,
            text="💡 Процедурный синтез занимает < 1 сек. Требуется .ttf исходник",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
        )
        self._generate_hint.grid(row=7, column=0, pady=(0, 16))

        # ── Дополнительные действия ───────────────────────────────────────
        SectionLabel(left, "ШАГ 4 — Экспорт").grid(
            row=7, column=0, padx=4, pady=(4, 4), sticky="w"
        )

        extra_frame = ctk.CTkFrame(left, fg_color="transparent")
        extra_frame.grid(row=8, column=0, sticky="ew", pady=(0, 8))
        extra_frame.grid_columnconfigure((0, 1), weight=1)

        self._btn_alphabet = OutlineButton(
            extra_frame,
            text="🔤  Показать алфавит",
            command=self._stub_show_alphabet,
        )
        self._btn_alphabet.grid(row=0, column=0, padx=(0, 6), pady=4, sticky="ew")

        self._btn_save = OutlineButton(
            extra_frame,
            text="💾  Сохранить .ttf / .otf",
            command=self._stub_save_font,
        )
        self._btn_save.grid(row=0, column=1, padx=(6, 0), pady=4, sticky="ew")

        # ── Настройки порога поиска ───────────────────────────────────────
        SectionLabel(left, "Параметры поиска").grid(
            row=9, column=0, padx=4, pady=(16, 4), sticky="w"
        )

        thresholds_frame = ctk.CTkFrame(left, fg_color=BG_CARD, corner_radius=10)
        thresholds_frame.grid(row=10, column=0, sticky="ew", pady=(0, 8))
        thresholds_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            thresholds_frame,
            text="Порог косинусного сходства:",
            font=ctk.CTkFont(size=12),
        ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self._threshold_var = tk.DoubleVar(value=0.55)
        self._threshold_slider = ctk.CTkSlider(
            thresholds_frame,
            from_=0.5,
            to=1.0,
            number_of_steps=50,
            variable=self._threshold_var,
        )
        self._threshold_slider.grid(row=0, column=1, padx=8, pady=10, sticky="ew")

        self._threshold_label = ctk.CTkLabel(
            thresholds_frame,
            text="0.55",
            font=ctk.CTkFont(size=12),
            width=40,
        )
        self._threshold_label.grid(row=0, column=2, padx=(0, 12), pady=10)
        self._threshold_var.trace_add(
            "write",
            lambda *_: self._threshold_label.configure(
                text=f"{self._threshold_var.get():.2f}"
            ),
        )

        ctk.CTkLabel(
            thresholds_frame,
            text="Слово для превью:",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        self._preview_word_var = tk.StringVar(value="Привет")
        self._preview_word_entry = ctk.CTkEntry(
            thresholds_frame,
            textvariable=self._preview_word_var,
            width=160,
            placeholder_text="Введите слово",
        )
        self._preview_word_entry.grid(
            row=1, column=1, columnspan=2, padx=(8, 12), pady=(0, 10), sticky="ew"
        )

    def _build_right_panel(self) -> None:
        """Правая панель: ResultPanel."""
        self._result_panel = ResultPanel(self)
        self._result_panel.grid(
            row=1, column=1, sticky="nsew", padx=(8, 16), pady=16
        )

    def _build_status_bar(self) -> None:
        """Нижняя строка статуса."""
        self._status_bar = StatusBar(self)
        self._status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    # ──────────────────────────────────────────────────────────────────────
    # Вспомогательные методы UI
    # ──────────────────────────────────────────────────────────────────────

    def _set_buttons_state(self, state: str) -> None:
        """Включает/выключает основные кнопки. state: 'normal' | 'disabled'"""
        for btn in (
            self._btn_recognize,
            self._btn_search,
            self._btn_generate,
            self._btn_alphabet,
            self._btn_save,
        ):
            btn.configure(state=state)

    def _run_in_thread(self, target, *args) -> None:
        """Запускает target в отдельном потоке, блокируя кнопки на время выполнения."""
        def wrapper():
            self._set_buttons_state("disabled")
            self._status_bar.start_indeterminate()
            try:
                target(*args)
            finally:
                self._set_buttons_state("normal")
                self._status_bar.stop_indeterminate()

        threading.Thread(target=wrapper, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────
    # Обработчики событий
    # ──────────────────────────────────────────────────────────────────────

    def _on_image_loaded(self, path: Path) -> None:
        """Вызывается, когда пользователь загрузил изображение."""
        self._image_path = path
        self._status_bar.set_status(f"Загружено: {path.name}")
        self._result_panel.log(f"Изображение загружено: {path.name}")
        # Сбрасываем предыдущие результаты
        self._result_panel.clear()

    def _reset_all(self) -> None:
        """Сбрасывает всё в начальное состояние."""
        self._image_path = None
        self._recognized_font_name = None
        self._found_font_name = None
        self._generated = False
        self._drop_zone.clear()
        self._result_panel.clear()
        self._status_bar.set_status("Готово к работе")
        self._result_panel.log("Состояние сброшено.")

    # ──────────────────────────────────────────────────────────────────────
    # STUB-функции (заглушки) — будут реализованы на следующих шагах
    # ──────────────────────────────────────────────────────────────────────

    def _stub_recognize_font(self) -> None:
        """
        РЕАЛИЗАЦИЯ: Шаг 3 — Распознавание шрифта и текста.
        """
        if not self._image_path:
            messagebox.showwarning("Нет изображения", "Сначала загрузите изображение-референс.")
            return

        def _task():
            try:
                if not self.recognizer or not self.embedder:
                    self._result_panel.log("Ошибка: Система еще не инициализирована.")
                    return

                self._status_bar.set_status("Распознавание...")
                self._result_panel.log("Запуск EasyOCR...")
                
                # 1. OCR
                text = self.recognizer.get_text(str(self._image_path))
                self._result_panel.log(f"Распознанный текст: {text or '[Пусто]'}")
                
                # 2. Определение типа (Serif/Sans/Script) через Zero-shot CLIP
                self._result_panel.log("Анализ стиля (CLIP Zero-shot)...")
                img = Image.open(self._image_path).convert("RGB")
                embedding = self.embedder.get_embedding(img)
                
                # Передаем embedder для доступа к get_text_embedding
                style_type = self.recognizer.classify_style_basic(embedding, self.embedder)
                
                self._recognized_font_name = style_type
                self._result_panel.set_recognized_font(style_type)
                self._result_panel.log(f"Стиль классифицирован: {style_type}")
                self._status_bar.set_status(f"Распознано: {style_type}", SUCCESS)
            except Exception as e:
                self._result_panel.log(f"Ошибка распознавания: {e}")
                self._status_bar.set_status("Ошибка!", ERROR_CLR)

        self._run_in_thread(_task)

    def _stub_search_font(self) -> None:
        """
        РЕАЛИЗАЦИЯ: Шаг 3 — Векторный поиск похожего кириллического шрифта.
        Возвращает топ-5 кандидатов с фильтрацией по наличию кириллики.
        """
        if not self._image_path:
            messagebox.showwarning("Нет изображения", "Сначала загрузите изображение-референс.")
            return

        threshold = self._threshold_var.get()
        word_to_preview = self._preview_word_var.get() or "Шрифт"

        def _task():
            try:
                self._status_bar.set_status("Поиск в базе...")
                self._result_panel.log("Извлечение эмбеддинга изображения...")

                img = Image.open(self._image_path).convert("RGB")
                embedding = self.embedder.get_embedding(img)

                # Берём широкую выборку для последующей фильтрации по кириллике
                self._result_panel.log(f"Поиск в ChromaDB (порог {threshold:.2f}, top-15)...")
                raw_results = self.vector_db.search(embedding, top_k=15)

                if not raw_results:
                    self._result_panel.log("База данных пуста или недоступна.")
                    self._status_bar.set_status("Нет результатов", WARNING)
                    return

                # ── Шаг 1: фильтруем по наличию кириллики ────────────────────
                cyrillic_results = [
                    r for r in raw_results
                    if has_cyrillic(r.get("file_path", ""))
                ]
                self._result_panel.log(
                    f"Кириллических шрифтов в топ-15: {len(cyrillic_results)} / {len(raw_results)}"
                )

                # ── Шаг 2: если кириллических нет → используем все ───────────
                if not cyrillic_results:
                    self._result_panel.log(
                        "⚠ Кириллических шрифтов в выборке нет. Показываем все результаты."
                    )
                    filtered = raw_results
                else:
                    filtered = cyrillic_results

                # ── Шаг 3: применяем порог сходства и берём топ-5 ────────────
                above_threshold = [r for r in filtered if r["similarity"] >= threshold]
                if not above_threshold:
                    best_sim = filtered[0]["similarity"] if filtered else 0.0
                    self._result_panel.log(
                        f"Совпадений выше порога {threshold:.0%} не найдено "
                        f"(лучшее: {best_sim:.1%}). Снизьте порог сходства."
                    )
                    self._status_bar.set_status("Порог не достигнут — снизьте Порог сходства", WARNING)
                    return

                top5 = above_threshold[:5]

                # ── Шаг 4: рендерим превью для лучшего и показываем ──────────
                best = top5[0]
                self._found_font_name = best["id"]
                self._found_font_path = best["file_path"]
                self._generated = False

                is_cyr = has_cyrillic(best["file_path"])
                cyr_tag = "✓ Кириллица" if is_cyr else "✗ Нет кириллики"
                self._result_panel.log(
                    f"Лучший: {best['id']} | {best['similarity']:.1%} | {cyr_tag}"
                )

                for i, r in enumerate(top5[1:], 2):
                    tag = "✓" if has_cyrillic(r.get("file_path", "")) else "✗"
                    self._result_panel.log(
                        f"  #{i}: {r['id']} | {r['similarity']:.1%} | {tag}"
                    )

                preview_img = render_font_sample(
                    best["file_path"],
                    text=word_to_preview if is_cyr else "ABCDE abc",
                    size=(300, 300),
                    font_size=50,
                )

                self.after(0, lambda: self._result_panel.set_cyrillic_preview(
                    f"{best['id']} ({cyr_tag})",
                    preview_img,
                    best["similarity"],
                ))
                self._status_bar.set_status(f"Найден: {best['id']} ({best['similarity']:.1%})", SUCCESS)

            except Exception as e:
                import traceback
                self._result_panel.log(f"Ошибка поиска: {e}")
                self._result_panel.log(traceback.format_exc()[:300])
                self._status_bar.set_status("Ошибка поиска", ERROR_CLR)

        self._run_in_thread(_task)

    def _direct_synthesize_from_ttf(self) -> None:
        """Прямой выбор TTF-файла для синтеза кириллицы."""
        path_str = filedialog.askopenfilename(
            title="Выберите исходный TrueType шрифт",
            filetypes=[("TrueType Font", "*.ttf"), ("Все файлы", "*.*")],
            initialdir="fonts_db",
        )
        if not path_str:
            return
        self._found_font_path = path_str
        self._found_font_name = Path(path_str).stem
        self._result_panel.log(f"Выбран шрифт: {self._found_font_name}")
        # Тут же запускаем синтез
        self._stub_generate_cyrillic()

    def _stub_generate_cyrillic(self) -> None:
        """
        РЕАЛИЗАЦИЯ: Шаг 4 — Процедурная генерация кириллицы из найденного латинского шрифта.
        """
        if not self._found_font_path:
            messagebox.showwarning("Нет шрифта", "Сначала выберите шрифт через Поиск.")
            return

        def _task():
            self._status_bar.set_status("Синтез кириллицы (fontTools)...")
            
            output_dir = Path("generated_fonts")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"Cyrillic_{self._found_font_name}.ttf"
            
            try:
                # Проверка что builder доступен
                if self.builder is None:
                    self.builder = CyrillicBuilder()
                # Генерируем (Сшиваем латинские векторы в кириллические слоты)
                report = self.builder.build_cyrillic(self._found_font_path, str(output_path))
                
                for line in report:
                    self._result_panel.log(line)
                
                self._generated = True
                self._found_font_path = str(output_path) # Переключаемся на новый файл
                
                # Рендерим превью нового шрифта
                word = self._preview_word_var.get() or "Шрифт"
                preview_img = render_font_sample(
                    str(output_path),
                    text=word,
                    size=(300, 300),
                    font_size=50,
                )
                
                self._result_panel.set_cyrillic_preview(
                    f"Синтезировано: {self._found_font_name}",
                    preview_img,
                    similarity=1.0, 
                    generated=True
                )
                
                self._status_bar.set_status("Синтез завершен!", SUCCESS)
            except Exception as e:
                import traceback
                self._result_panel.log(f"Ошибка при синтезе: {e}")
                self._result_panel.log(traceback.format_exc()[:300])
                self._status_bar.set_status("Ошибка синтеза", ERROR_CLR)

        self._run_in_thread(_task)

    def _stub_show_alphabet(self) -> None:
        """
        РЕАЛИЗАЦИЯ: Шаг 3 — Показать полный алфавит и цифры.
        """
        if not self._found_font_name and not self._generated:
            messagebox.showinfo(
                "Нет результата",
                "Сначала выполните поиск или генерацию шрифта.",
            )
            return

        font_name = self._found_font_name or "Неизвестный шрифт"
        self._result_panel.log(f"Генерация алфавита для: {font_name}")

        if self._found_font_path:
            # Рендерим алфавит реальным шрифтом (либо найденным, либо уже синтезированным)
            alphabet_img = render_alphabet(
                self._found_font_path,
                size=(800, 400),
                font_size=32
            )
            win = AlphabetWindow(self, font_name=font_name, glyph_image=alphabet_img)
            win.grab_set()
        else:
            messagebox.showinfo("Нет шрифта", "Сначала найдите или синтезируйте шрифт.")

    def __show_alphabet_window_sync(self, font_name, image):
        win = AlphabetWindow(self, font_name=font_name, glyph_image=image)
        win.grab_set()

    def _stub_save_font(self) -> None:
        """
        РЕАЛИЗАЦИЯ: Шаг 5 — Экспорт сгенерированных глифов в .ttf файл.
        """
        if not self._generated and not self._found_font_path:
            messagebox.showwarning("Нет файла", "Сначала сгенерируйте или найдите шрифт.")
            return

        font_name_default = self._found_font_name or "CustomFont"
        
        file_path = filedialog.asksaveasfilename(
            title="Сохранить шрифт как",
            initialfile=f"{font_name_default}.ttf",
            defaultextension=".ttf",
            filetypes=[("TrueType Font", "*.ttf")]
        )

        if not file_path:
            return

        def _task():
            self._status_bar.set_status("Экспорт TTF (векторизация OpenCV)...")
            self._result_panel.log(f"Сборка .ttf структуры в файл: {file_path}")
            
            try:
                if self._generated:
                    # Генерируем тестовый глиф для экспорта (или используем кэш)
                    style_img = Image.open(self._image_path).convert("RGB")
                    target_image = self.generator.generate_cyrillic(
                        style_reference_image=style_img, 
                        word="А", 
                        steps=15
                    )
                    exporter = FontExporter()
                    exporter.export_to_ttf(target_image, file_path, font_name=font_name_default)
                    self._result_panel.log("Успешно: Векторные контуры записаны в TTF.")
                elif self._found_font_path:
                    # Просто копируем существующий ttf (shutil)
                    import shutil
                    shutil.copy(self._found_font_path, file_path)
                    self._result_panel.log("Успешно: Файл шрифта скопирован из базы.")

                self._status_bar.set_status("Сохранено!", SUCCESS)
                
                # Попробуем открыть папку с результатом (Windows)
                import os
                os.startfile(os.path.dirname(file_path))
                
            except Exception as e:
                self._result_panel.log(f"Ошибка экспорта: {e}")
                self._status_bar.set_status("Ошибка сохранения TTF", ERROR_CLR)

        self._run_in_thread(_task)


# ──────────────────────────────────────────────────────────────────────────────
# Утилита: рендер заглушки-превью
# ──────────────────────────────────────────────────────────────────────────────

def _render_stub_preview(
    word: str,
    size: tuple[int, int] = (360, 100),
    generated: bool = False,
) -> Image.Image:
    """
    Рендерит текстовое превью шрифта системными средствами Pillow.
    Используется как заглушка до реализации настоящего рендерера.
    """
    bg_color = (30, 34, 53)  # BG_CARD
    text_color = (108, 99, 255) if not generated else (46, 204, 113)

    img = Image.new("RGB", size, bg_color)
    draw = ImageDraw.Draw(img)

    try:
        # Пробуем загрузить системный шрифт Windows
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size=40)
    except Exception:
        font = ImageFont.load_default()

    # Центрируем текст
    bbox = draw.textbbox((0, 0), word, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size[0] - text_w) // 2
    y = (size[1] - text_h) // 2
    draw.text((x, y), word, fill=text_color, font=font)

    label = "СГЕНЕРИРОВАНО" if generated else "НАЙДЕНО В БАЗЕ"
    try:
        small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size=11)
    except Exception:
        small_font = ImageFont.load_default()

    draw.text((6, 4), f"[STUB] {label}", fill=(100, 110, 140), font=small_font)
    return img

if __name__ == "__main__":
    _apply_theme()
    app = CyrillicFontTransferApp()
    app.mainloop()
