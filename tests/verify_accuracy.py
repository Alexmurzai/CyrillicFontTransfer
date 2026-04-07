import torch
import json
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.inference_engine import InferenceEngine
from ml_core.dataset import FontDataset

def run_diagnostic():
    print("--- HFR Accuracy Diagnostic ---")
    
    # 1. Загрузка компонентов
    eng = InferenceEngine()
    with open('data/fonts_index.json', 'r', encoding='utf-8') as f:
        idx = json.load(f)
    
    # Берем случайный шрифт из базы (пусть будет 100-й из 'both')
    test_font = idx['both'][250]
    print(f"Target font: {test_font['name']}")
    print(f"Path: {test_font['path']}")

    # 2. Генерируем "идеальный" скриншот для теста
    text = "HOagnsep"
    img_h, img_w = 120, 600
    test_img = Image.new('L', (img_w, img_h), 255)
    
    try:
        font_obj = ImageFont.truetype(test_font['path'], 60)
        draw = ImageDraw.Draw(test_img)
        draw.text((20, 20), text, font=font_obj, fill=0)
    except Exception as e:
        print(f"Error rendering font: {e}")
        return

    os.makedirs('temp/test', exist_ok=True)
    img_path = 'temp/test/diagnostic.png'
    test_img.save(img_path)
    print(f"Diagnostic image saved to {img_path}")

    # 3. Запускаем распознавание
    print("\nRunning recognition...")
    chars, results = eng.recognize_font(img_path)
    
    if results and "error" in results:
        print(f"Inference Error: {results['error']}")
        return

    print(f"Number of characters segmented: {len(chars) if chars else 0}")
    
    print("\nTop 5 Results:")
    found_target = False
    for i, r in enumerate(results):
        is_match = r['font_name'] == test_font['name']
        match_str = "[MATCH!]" if is_match else ""
        if is_match: found_target = True
        
        # Считаем "чистое" расстояние и наш процент
        dist = r['score']
        score_pct = max(0, min(100, 100 * (1 - dist / 1.5)))
        
        print(f"{i+1}. {r['font_name']} | Dist: {dist:.4f} | Sim: {score_pct:.1f}% {match_str}")
        print(f"   Path: {r['path']}")

    if not found_target:
        print("\n[CRITICAL] Target font NOT found in Top 5 Results!")
    else:
        print("\n[OK] Target font identified correctly.")

if __name__ == "__main__":
    run_diagnostic()
