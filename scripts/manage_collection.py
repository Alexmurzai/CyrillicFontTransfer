#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOCT Font Collection Manager
Управление коллекцией шрифтов: удаление триальных/демо шрифтов, импорт новых и пересборка базы FAISS.
"""
import os
import sys
import hashlib
import shutil
import torch
from pathlib import Path

# Убедимся, что корень проекта в sys.path
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Импортируем существующие скрипты
try:
    from scripts.prepare_fonts import FONT_ROOTS, OUTPUT, build_index
    from scripts.database_builder import build_vector_db
except ImportError as e:
    print(f"[X] Ошибка импорта системных скриптов: {e}")
    sys.exit(1)

# Ключевые слова для поиска демонстрационных/триальных шрифтов
TRIAL_KEYWORDS = ['trial', 'demo', 'free-version', 'personal-use', 'watermark', 'watermarked', 'restricted', 'sample']

def get_file_hash(file_path):
    """Вычисляет MD5 хэш файла."""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"[X] Ошибка чтения файла {file_path}: {e}")
        return None

def scan_existing_hashes():
    """Сканирует все существующие шрифты в FONT_ROOTS и возвращает их хэши."""
    hashes = {}
    print("[*] Сканирование существующей коллекции шрифтов для поиска дубликатов...")
    for root_dir in FONT_ROOTS:
        path = Path(root_dir)
        if not path.exists():
            continue
        for f in path.glob("**/*"):
            if f.is_file() and f.suffix.lower() in ['.ttf', '.otf']:
                f_hash = get_file_hash(f)
                if f_hash:
                    hashes[f_hash] = f
    return hashes

def action_cleanup():
    """Поиск и удаление триальных/демо шрифтов."""
    print("\n" + "="*60)
    print(" ПОИСК И УДАЛЕНИЕ ДЕМОНСТРАЦИОННЫХ/ТРИАЛЬНЫХ ШРИФТОВ ".center(60, "■"))
    print("="*60)
    
    found_files = []
    
    # Сканируем все директории из FONT_ROOTS
    for root_dir in FONT_ROOTS:
        path = Path(root_dir)
        if not path.exists():
            continue
            
        print(f"[*] Сканирование папки: {path}")
        for f in path.glob("**/*"):
            if f.is_file() and f.suffix.lower() in ['.ttf', '.otf']:
                name_lower = f.name.lower()
                # Проверяем на наличие ключевых слов
                if any(kw in name_lower for kw in TRIAL_KEYWORDS):
                    found_files.append(f)
                    
    if not found_files:
        print("\n[OK] Демонстрационных или триальных шрифтов в коллекции не найдено!")
        return
        
    print(f"\n[!] Найдено демонстрационных/триальных шрифтов: {len(found_files)}")
    print("-" * 60)
    for idx, f in enumerate(found_files, 1):
        size_mb = f.stat().st_size / (1024 * 1024)
        # Вывод относительного пути от корня проекта, если возможно
        try:
            rel_path = f.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = f
        print(f"  [{idx}] {f.name} ({size_mb:.2f} MB)")
        print(f"      Путь: {rel_path}")
        print("-" * 60)
        
    print("\nВыберите действие:")
    print("  1. Удалить ВСЕ найденные файлы")
    print("  2. Выбрать и удалить определенные файлы по номерам")
    print("  3. Отмена")
    
    choice = input("\nВаш выбор (1-3): ").strip()
    
    if choice == '1':
        confirm = input("[?] Вы уверены, что хотите безвозвратно удалить все эти файлы? (y/n): ").strip().lower()
        if confirm == 'y':
            deleted_count = 0
            for f in found_files:
                try:
                    f.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"[X] Не удалось удалить {f.name}: {e}")
            print(f"\n[+] Успешно удалено файлов: {deleted_count} из {len(found_files)}")
            ask_rebuild_db()
        else:
            print("[*] Удаление отменено.")
            
    elif choice == '2':
        nums_str = input("[?] Введите номера файлов через запятую (например: 1, 3, 5): ").strip()
        try:
            indices = [int(n.strip()) - 1 for n in nums_str.split(",") if n.strip().isdigit()]
            valid_files = [found_files[i] for i in indices if 0 <= i < len(found_files)]
            
            if not valid_files:
                print("[X] Неверный выбор номеров.")
                return
                
            print(f"\nВыбрано для удаления ({len(valid_files)} шт.):")
            for vf in valid_files:
                print(f"  - {vf.name}")
                
            confirm = input("[?] Вы уверены, что хотите удалить эти файлы? (y/n): ").strip().lower()
            if confirm == 'y':
                deleted_count = 0
                for f in valid_files:
                    try:
                        f.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"[X] Не удалось удалить {f.name}: {e}")
                print(f"\n[+] Успешно удалено файлов: {deleted_count}")
                ask_rebuild_db()
            else:
                print("[*] Удаление отменено.")
        except Exception as e:
            print(f"[X] Ошибка обработки выбора: {e}")
    else:
        print("[*] Возврат в главное меню.")

def action_import():
    """Импорт новых шрифтов из внешней папки с проверкой на дубликаты."""
    print("\n" + "="*60)
    print(" ИМПОРТ НОВЫХ ШРИФТОВ В КОЛЛЕКЦИЮ ".center(60, "■"))
    print("="*60)
    
    source_dir_str = input("[?] Введите путь к внешней папке со шрифтами: ").strip()
    source_path = Path(source_dir_str.strip('"')) # убираем кавычки, если путь перетащили в консоль
    
    if not source_path.exists() or not source_path.is_dir():
        print("[X] Ошибка: Указанный путь не существует или не является папкой.")
        return
        
    # Целевая папка для импортированных шрифтов
    target_path = PROJECT_ROOT / "fonts_db" / "imported_fonts"
    target_path.mkdir(parents=True, exist_ok=True)
    
    # 1. Сканируем существующие шрифты
    existing_hashes_map = scan_existing_hashes()
    
    # 2. Ищем кандидатов во внешней папке
    print(f"[*] Сканирование новых шрифтов в {source_path}...")
    candidate_files = list(source_path.glob("**/*.ttf")) + list(source_path.glob("**/*.otf"))
    print(f"[*] Найдено файлов во внешней папке: {len(candidate_files)}")
    
    if not candidate_files:
        print("[!] Шрифтов (.ttf / .otf) во внешней папке не найдено.")
        return
        
    added_count = 0
    duplicate_count = 0
    
    print("\n[*] Обработка и копирование уникальных шрифтов...")
    for f in candidate_files:
        f_hash = get_file_hash(f)
        if not f_hash:
            continue
            
        # Проверяем дубликаты по хэшу
        if f_hash in existing_hashes_map:
            duplicate_count += 1
            continue
            
        # Уникальный шрифт, копируем его
        target_file = target_path / f.name
        
        # Разрешение коллизий имен (одинаковые имена, разные хэши)
        if target_file.exists():
            target_file = target_path / f"{f.stem}_{f_hash[:8]}{f.suffix}"
            
        try:
            shutil.copy2(f, target_file)
            existing_hashes_map[f_hash] = target_file
            added_count += 1
            print(f"  [+] Скопирован: {f.name} -> {target_file.name}")
        except Exception as e:
            print(f"  [X] Ошибка копирования {f.name}: {e}")
            
    print("\n" + "="*50)
    print(f"[+] Импорт завершен!")
    print(f"[*] Скопировано новых уникальных шрифтов: {added_count}")
    print(f"[*] Пропущено дубликатов: {duplicate_count}")
    print("="*50)
    
    if added_count > 0:
        ask_rebuild_db()

def action_rebuild():
    """Программный запуск индексации и пересборки FAISS базы."""
    print("\n" + "="*60)
    print(" ПЕРЕСБОРКА ВЕКТОРНОЙ БАЗЫ ДАННЫХ ШРИФТОВ (FAISS) ".center(60, "■"))
    print("="*60)
    print("[*] Запуск процесса переиндексации коллекции...")
    
    try:
        # Шаг 1: пересборка fonts_index.json
        print("\n[1/2] Обновление списка поддерживаемых языков (fonts_index.json)...")
        build_index(FONT_ROOTS, OUTPUT)
        
        # Шаг 2: пересборка базы FAISS
        print("\n[2/2] Генерация векторных признаков и сохранение FAISS индекса...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[*] Используемое устройство для вычислений: {device.upper()}")
        build_vector_db(device=device)
        
        print("\n[OK] База данных успешно обновлена и готова к работе!")
        print("     Для применения изменений перезапустите FastAPI сервер бэкенда (start_github.bat / start_local.bat).")
    except Exception as e:
        print(f"\n[X] Произошла ошибка при пересборке базы данных: {e}")

def ask_rebuild_db():
    """Спрашивает пользователя, нужно ли обновить базу сейчас."""
    confirm = input("\n[?] Изменения внесены. Хотите запустить пересборку базы данных FAISS прямо сейчас? (y/n): ").strip().lower()
    if confirm == 'y':
        action_rebuild()
    else:
        print("[*] Пересборка отложена. Помните, что для отображения изменений на сайте базу нужно пересобрать (выбрав пункт 3 в меню).")

def main_menu():
    while True:
        print("\n" + "="*60)
        print(" MOCT — УПРАВЛЕНИЕ КОЛЛЕКЦИЕЙ ШРИФТОВ ".center(60, "█"))
        print("="*60)
        print("  [1] Найти и удалить демо/триал шрифты (Очистка)")
        print("  [2] Импортировать новые шрифты из внешней папки")
        print("  [3] Пересобрать векторную базу данных (FAISS)")
        print("  [4] Выйти")
        print("="*60)
        
        choice = input("Выберите действие (1-4): ").strip()
        
        if choice == '1':
            action_cleanup()
        elif choice == '2':
            action_import()
        elif choice == '3':
            action_rebuild()
        elif choice == '4':
            print("\nВыход из программы. Хорошего дня!")
            break
        else:
            print("[X] Неверный пункт меню. Пожалуйста, введите число от 1 до 4.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем. Выход.")
        sys.exit(0)
