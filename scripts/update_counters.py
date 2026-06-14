#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOCT Font Counter Updater
Автоматическое обновление счетчиков шрифтов во всем проекте (фронтенд fallback, Readme.txt, Readme.docx).
"""
import os
import re
from pathlib import Path

def get_russian_plural(number, one, two, five):
    """Возвращает правильную форму существительного для русского языка."""
    n = abs(number) % 100
    n1 = n % 10
    if 10 < n < 20:
        return five
    if 1 < n1 < 5:
        return two
    if n1 == 1:
        return one
    return five

def update_project_counters(count):
    project_root = Path(__file__).parent.parent.absolute()
    print(f"\n[*] Запуск обновления счетчиков шрифтов во всем проекте на число: {count}")

    # 1. Обновление React-файлов (fallback значения)
    files_to_update = [
        project_root / "frontend/src/components/Sidebar/Sidebar.jsx",
        project_root / "frontend/src/App.jsx"
    ]
    
    react_pattern = re.compile(r"(\bcount:\s*)(\d+)")
    react_updated = 0
    
    for file_path in files_to_update:
        if file_path.exists():
            try:
                content = file_path.read_text(encoding="utf-8")
                new_content = react_pattern.sub(rf"\g<1>{count}", content)
                if new_content != content:
                    file_path.write_text(new_content, encoding="utf-8")
                    print(f"  [+] Обновлен fallback в JS/JSX: {file_path.name}")
                    react_updated += 1
            except Exception as e:
                print(f"  [X] Ошибка при обновлении {file_path.name}: {e}")

    # 2. Обновление Readme.txt
    readme_path = project_root / "Readme.txt"
    if readme_path.exists():
        try:
            content = readme_path.read_text(encoding="utf-8")
            
            # Вычисляем правильную грамматическую форму для русского текста
            suffix = get_russian_plural(
                count, 
                "кириллический шрифт", 
                "кириллических шрифта", 
                "кириллических шрифтов"
            )
            
            # Регулярка для замены "поиск по FAISS-индексу (XXXX кириллический...)"
            txt_pattern = re.compile(r"(поиск по FAISS-индексу \()(\d+)( кириллическ[^)]+\))")
            new_content = txt_pattern.sub(rf"\g<1>{count} {suffix})", content)
            
            if new_content != content:
                readme_path.write_text(new_content, encoding="utf-8")
                print(f"  [+] Обновлен Readme.txt (счетчик: {count} {suffix})")
        except Exception as e:
            print(f"  [X] Ошибка при обновлении Readme.txt: {e}")

    # 3. Обновление Readme.docx
    readme_docx_path = project_root / "Readme.docx"
    if readme_docx_path.exists():
        try:
            import docx
            doc = docx.Document(readme_docx_path)
            docx_updated = False
            
            suffix = get_russian_plural(
                count, 
                "кириллический шрифт", 
                "кириллических шрифта", 
                "кириллических шрифтов"
            )
            
            # Поиск и замена в параграфах
            docx_pattern = re.compile(r"(поиск по FAISS-индексу \()(\d+)( кириллическ[^)]+\))")
            for p in doc.paragraphs:
                if "FAISS-индексу" in p.text:
                    new_text = docx_pattern.sub(rf"\g<1>{count} {suffix})", p.text)
                    if p.text != new_text:
                        p.text = new_text
                        docx_updated = True
            
            if docx_updated:
                doc.save(readme_docx_path)
                print(f"  [+] Обновлен Readme.docx (счетчик: {count} {suffix})")
        except Exception as e:
            print(f"  [X] Ошибка при обновлении Readme.docx: {e}")

    print("[*] Обновление счетчиков завершено.\n")

if __name__ == "__main__":
    import sys
    # Если запущен напрямую, можно передать число аргументом
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        update_project_counters(int(sys.argv[1]))
    else:
        # По умолчанию читаем из metadata.json
        import json
        meta_file = Path(__file__).parent.parent / "data/font_metadata.json"
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    update_project_counters(len(data))
            except Exception as e:
                print(f"[X] Не удалось прочитать {meta_file}: {e}")
        else:
            print("[X] Файл data/font_metadata.json не найден. Задайте число аргументом.")
