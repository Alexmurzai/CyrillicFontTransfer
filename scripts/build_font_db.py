"""
CLI скрипт для индексации шрифтов в векторную базу данных.
Использование: 
py -3 scripts/build_font_db.py
"""

import os
import sys
import shutil
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импорт модулей ядра
from core.font_utils import render_font_sample
from core.embedder import StyleEmbedder
from core.vector_db import FontVectorDB

def prepare_test_fonts(fonts_dir: Path):
    """(Для теста) копирует стандартные шрифты Windows, если папка пуста."""
    if not fonts_dir.exists():
        fonts_dir.mkdir(parents=True)
    
    ttf_files = list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf"))
    if not ttf_files:
        print("[!] Папка fonts_db пуста. Копируем тестовые шрифты из C:\\Windows\\Fonts...")
        windows_fonts = ["arial.ttf", "calibri.ttf", "times.ttf"] # Популярные кириллические шрифты
        for wf in windows_fonts:
            src = Path(f"C:\\Windows\\Fonts\\{wf}")
            if src.exists():
                shutil.copy(src, fonts_dir / src.name)
        
        ttf_files = list(fonts_dir.glob("*.ttf"))

    return ttf_files


def build_db(fonts_dir_name: str = "fonts_db", sample_text: str = "АБВГД\nабвгд\n12345"):
    
    project_root = Path(__file__).parent.parent
    fonts_dir = project_root / fonts_dir_name
    
    print("=" * 50)
    print("Индексация кириллических шрифтов...")
    print("=" * 50)
    
    ttf_files = prepare_test_fonts(fonts_dir)
    
    if not ttf_files:
        print("[X] Ошибка: Шрифты не найдены!")
        return
        
    print(f"[*] Найдено шрифтов: {len(ttf_files)}")
    
    # 1. Запуск БД и CLIP
    db = FontVectorDB(persist_dir=str(fonts_dir / "chroma"))
    embedder = StyleEmbedder() # При первом запуске скачает openai/clip (~340 MB)
    
    # 2. Индексация
    for font_path in ttf_files:
        font_name = font_path.stem  # Название файла без расширения
        
        # Шаг 2.1: Рендеринг
        print(f"  -> Обработка: {font_name}...", end=" ")
        image = render_font_sample(str(font_path), text=sample_text, size=(224, 224))
        
        if image is None:
            print("ОШИБКА рендеринга")
            continue
            
        # Шаг 2.2: Получение эмбеддинга от CLIP
        vector = embedder.get_embedding(image)
        
        # Шаг 2.3: Сохранение в ChromaDB
        db.add_font(
            font_name=font_name,
            file_path=str(font_path.absolute()),
            embedding=vector
        )
        print("ОК")
        
    print("=" * 50)
    print(f"[+] Успешно! Всего записей в Векторной БД: {db.count()}")
    print("=" * 50)

if __name__ == "__main__":
    build_db()
