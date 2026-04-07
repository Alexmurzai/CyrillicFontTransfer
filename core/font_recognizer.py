"""
Модуль для распознавания текста (OCR) и классификации стиля шрифта.
"""

import os
import easyocr
import numpy as np
from PIL import Image
from typing import Tuple, List, Optional, Any

class FontRecognizer:
    """
    Класс для извлечения текста из изображения и базовой классификации стиля.
    """

    def __init__(self, model_dir: str = "models", gpu: bool = True):
        """
        Инициализация EasyOCR.
        gpu: флаг использования CUDA.
        """
        print(f"[*] FontRecognizer: Загрузка EasyOCR (GPU={gpu})...")
        os.makedirs(model_dir, exist_ok=True)
        
        # Загружаем поддержку английского и русского (хотя референс латинский)
        self.reader = easyocr.Reader(['en', 'ru'], gpu=gpu, model_storage_directory=model_dir)
        print("[+] FontRecognizer: EasyOCR готов.")

    def get_text(self, image_path: str) -> str:
        """
        Извлекает текст из изображения.
        Возвращает строку с наиболее вероятным текстом.
        """
        results = self.reader.readtext(image_path)
        if not results:
            return ""
        
        # Собираем весь найденный текст в одну строку
        full_text = " ".join([res[1] for res in results])
        return full_text.strip()

    def classify_style_basic(self, embedding: List[float], embedder: Any) -> str:
        """
        Реальная классификация стиля через Zero-shot CLIP.
        Сравнивает входной вектор картинки с текстовыми векторами категорий.
        """
        categories = ["Serif font", "Sans-serif font", "Script handwriting font"]
        labels = ["Serif", "Sans", "Script"]
        
        # Получаем эмбеддинги для текстовых описаний
        text_features = []
        for cat in categories:
            text_features.append(embedder.get_text_embedding(cat))
            
        # Считаем косинусное сходство (dot product, так как векторы нормализованы)
        img_vec = np.array(embedding)
        similarities = []
        for txt_vec in text_features:
            sim = np.dot(img_vec, np.array(txt_vec))
            similarities.append(sim)
            
        # Индекс максимального сходства
        best_idx = np.argmax(similarities)
        return labels[best_idx]
