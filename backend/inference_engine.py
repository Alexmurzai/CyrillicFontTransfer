import os
import cv2
import json
import torch
import faiss
import numpy as np
from PIL import Image
from torchvision import transforms

# Локальные импорты
from ml_core.model import HFRNet

class InferenceEngine:
    def __init__(self, model_path="models/hfr_model_best.pth", 
                 index_path="data/font_signatures.faiss", 
                 meta_path="data/font_metadata.json",
                 device="cuda"):
        self.device = device if torch.cuda.is_available() else "cpu"
        
        # 1. Загрузка модели
        print(f"Loading inference model from {model_path}...")
        self.model = HFRNet(signature_dim=256).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        # 2. Загрузка FAISS индекса
        print(f"Loading FAISS index from {index_path}...")
        self.index = faiss.read_index(index_path)
        
        # 3. Загрузка метаданных
        with open(meta_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
        # Трансформы (без принудительного изменения пропорций)
        self.char_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5,), (0.5,))
        ])


    def segment_characters(self, image_path, max_chars=8):
        """
        Сегментирует изображение на отдельные символы с помощью OpenCV.
        """
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Авто-инверсия (если фон темный, а текст светлый)
        # Фон обычно занимает большую площадь, проверяем по медиане
        if np.median(gray) < 127:
            gray = cv2.bitwise_not(gray)
            
        # Максимально высветляем фон за счет контрастирования
        # Растягиваем гистограмму, чтобы самый темный стал черным (0), самый светлый — белым (255)
        gray = cv2.normalize(gray, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        # Дополнительно усиливаем контраст и яркость (смываем грязь с фона)
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
        
        # Бинаризация (черный текст на белом фоне)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Поиск контуров
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        char_crops = []
        # Фильтруем слишком маленькие контуры (шум)
        bboxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 5 and h > 10:
                bboxes.append((x, y, w, h))
        
        # Сортируем слева направо
        bboxes.sort(key=lambda b: b[0])
        
        for x, y, w, h in bboxes[:max_chars]:
            roi = gray[y:y+h, x:x+w]
            # Увеличенный паддинг (30% от размера), чтобы не обрезать края букв
            pad = int(max(w, h) * 0.3)
            roi_padded = cv2.copyMakeBorder(roi, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255)
            
            # Конвертируем в PIL
            pil_img = Image.fromarray(roi_padded)
            char_crops.append(pil_img)
            
        return char_crops


    def get_font_preview(self, font_path, text="HFR Recognition", size=64, letter_spacing=0, word_spacing=20):
        """Рендерит полноценную строку текста для превью с поддержкой интервалов."""
        from PIL import Image, ImageDraw, ImageFont
        try:
            font = ImageFont.truetype(font_path, size)
            
            # Определение высоты
            ascent, descent = font.getmetrics()
            max_height = ascent + descent
            
            # Расчет итоговой ширины
            total_width = 0
            for char in text:
                char_w = font.getlength(char)
                if char == ' ':
                    total_width += char_w + word_spacing
                else:
                    total_width += char_w + letter_spacing
            
            pad = 20
            img = Image.new("L", (int(total_width) + pad * 2, max_height + pad * 2), 255)
            draw = ImageDraw.Draw(img)
            
            # Отрисовка символ за символом
            current_x = pad
            for char in text:
                char_w = font.getlength(char)
                draw.text((current_x, pad), char, font=font, fill=0)
                if char == ' ':
                    current_x += char_w + word_spacing
                else:
                    current_x += char_w + letter_spacing
                    
            return img
        except Exception as e:
            # Fallback на случай ошибки
            return Image.new("L", (200, 64), 255)


    def preprocess_roi(self, pil_img, target_size=64):
        """Ресайз с сохранением пропорций (Letterbox)."""
        w, h = pil_img.size
        scale = target_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # Масштабируем
        pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        
        # Создаем белый квадрат и вклеиваем по центру
        new_img = Image.new("L", (target_size, target_size), 255)
        new_img.paste(pil_img, ((target_size - new_w) // 2, (target_size - new_h) // 2))
        return self.char_transform(new_img)

    def recognize_font(self, image_path, top_k=5):
        """
        Основной пайплайн: сегментация -> инференс -> поиск.
        """
        char_pil_images = self.segment_characters(image_path)
        if not char_pil_images:
            return None, {"error": "Characters not found in image"}
            
        # Подготовка тензоров с сохранением пропорций
        char_tensors = [self.preprocess_roi(img) for img in char_pil_images]
        batch = torch.stack(char_tensors).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            signature, _ = self.model(batch)
            # L2-Нормализация: критически важна для корректного поиска сходства
            signature = torch.nn.functional.normalize(signature, p=2, dim=1)
            sig_np = signature.cpu().numpy().astype('float32')


            
        # Поиск в FAISS
        distances, indices = self.index.search(sig_np, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            meta = self.metadata[idx]
            results.append({
                "id": int(idx),
                "font_name": meta["name"],
                "path": meta["path"],
                "score": float(dist),
            })
            
        return char_pil_images, results

