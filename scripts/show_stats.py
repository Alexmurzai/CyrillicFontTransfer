#!/usr/bin/env python3
"""
HFR — Show Stats CLI
Скрипт для вывода статистики использования подбора шрифтов и скачиваний в консоль.
"""
import os
import sys

# Убедимся, что корень проекта в sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from backend.stats_db import get_stats_summary

def print_header(title):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "■"))
    print("=" * 60)

def draw_bar(val, max_val, width=20):
    if max_val == 0:
        return "░" * width
    filled = int((val / max_val) * width)
    return "█" * filled + "░" * (width - filled)

def main():
    # Проверим наличие базы данных
    db_path = os.path.join(PROJECT_ROOT, "data", "hfr_stats.db")
    if not os.path.exists(db_path):
        print(f"\n[!] База данных статистики еще не создана. Запустите бэкенд для ее инициализации.")
        print(f"    Путь к БД: {db_path}\n")
        return

    stats = get_stats_summary()
    totals = stats["totals"]
    
    # 1. Заголовок
    print_header("HFR — СТАТИСТИКА ИСПОЛЬЗОВАНИЯ")
    
    # 2. Общие показатели
    print(f"  👁  Уникальные визиты:  {totals['visits']:<10} (лимит 30м на IP)")
    print(f"  🔍 Запущенные подборы: {totals['recognitions']:<10}")
    print(f"  💾 Скачанные шрифты:   {totals['downloads']:<10}")
    
    # 3. Распределение по категориям
    print_header("РАСПРЕДЕЛЕНИЕ ПО СТИЛЯМ")
    if stats["categories"]:
        max_cat = max(stats["categories"].values()) if stats["categories"].values() else 0
        for cat, count in sorted(stats["categories"].items(), key=lambda x: x[1], reverse=True):
            bar = draw_bar(count, max_cat, 15)
            print(f"  {cat.upper():<10} | {bar} {count:<4} подборов")
    else:
        print("  Данные о стилях отсутствуют.")

    # 4. Популярные совпадения
    print_header("ТОП-5 ПОПУЛЯРНЫХ СОВПАДЕНИЙ")
    if stats["top_matches"]:
        for i, item in enumerate(stats["top_matches"][:5]):
            print(f"  {i+1}. {item['top_match']:<35} | {item['count']} раз(а) подобрано")
    else:
        print("  Данные о совпадениях отсутствуют.")

    # 5. Популярные скачивания
    print_header("ТОП-5 СКАЧИВАЕМЫХ ШРИФТОВ")
    if stats["top_downloads"]:
        for i, item in enumerate(stats["top_downloads"][:5]):
            print(f"  {i+1}. {item['font_name']:<35} | {item['count']} раз(а) скачано")
    else:
        print("  Данные о скачиваниях отсутствуют.")

    # 6. Активность за последние 7 дней
    print_header("АКТИВНОСТЬ ЗА ПОСЛЕДНИЕ 7 ДНЕЙ")
    recent_activity = stats["activity_daily"][-7:] if len(stats["activity_daily"]) >= 7 else stats["activity_daily"]
    if recent_activity:
        print(f"  {'Дата':<10} | {'Визиты':<8} | {'Подборы':<8} | {'Скачивания':<10}")
        print("  " + "-" * 45)
        for d in recent_activity:
            print(f"  {d['date']:<10} | {d['visits']:<8} | {d['recognitions']:<8} | {d['downloads']:<10}")
    else:
        print("  Данные об активности отсутствуют.")
        
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
