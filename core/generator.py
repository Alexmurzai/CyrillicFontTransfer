"""
Генератор кириллических шрифтов на базе Stable Diffusion, ControlNet и IP-Adapter.
"""

import torch
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Потребуется pip install diffusers accelerate opencv-python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler

class FontGenerator:
    def __init__(self, device: str = "auto", load_on_init: bool = False):
        """
        Инициализация генератора.
        load_on_init: Если True, веса (около 6-8 Гб) скачаются и загрузятся в видеопамять сразу.
                      Иначе - при первой генерации (Lazy load).
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.is_loaded = False
        self.pipe = None
        
        if load_on_init:
            self.load_models()

    def load_models(self):
        if self.is_loaded:
            return
            
        print(f"[*] FontGenerator: Инициализация SD Pipeline на {self.device}... (может потребоваться загрузка ~6 ГБ)")
        
        # Используем ControlNet Canny для сохранения контуров (мы дадим ему обычный текст Arial/Times, а он обведет его)
        controlnet_id = "lllyasviel/sd-controlnet-canny"
        sd_id = "runwayml/stable-diffusion-v1-5"
        
        print("  -> Загрузка ControlNet...")
        controlnet = ControlNetModel.from_pretrained(
            controlnet_id, torch_dtype=torch.float16
        )
        
        print("  -> Загрузка Stable Diffusion v1.5...")
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            sd_id, controlnet=controlnet, torch_dtype=torch.float16,
            safety_checker=None, requires_safety_checker=False
        )
        
        print("  -> Загрузка IP-Adapter (для переноса стиля без промптинга)...")
        try:
            # IP-Adapter отлично переносит визуальный стиль картинки на генерацию
            self.pipe.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
            self.pipe.set_ip_adapter_scale(0.8) # Сила переноса стиля (0.0 - 1.0)
        except Exception as e:
            print(f"[!] Ошибка загрузки IP-Adapter: {e} | Генерация будет опираться на текст.")

        # Ускоритель сэмплера (существенно ускоряет инференс)
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        
        # На 3090 память не проблема (24GB), можем перенести полностью в VRAM
        self.pipe.to(self.device)
        
        self.is_loaded = True
        print("[+] FontGenerator успешно загружен в видеопамять.")

    def _get_canny_image(self, image: Image.Image, low_threshold=100, high_threshold=200) -> Image.Image:
        """Извлекает контуры для ControlNet."""
        image_cv = np.array(image)
        # Если RGB (а не Gray), переводим для Canny
        if len(image_cv.shape) == 3:
            image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2GRAY)
            
        edges = cv2.Canny(image_cv, low_threshold, high_threshold)
        edges = edges[:, :, None]
        edges = np.concatenate([edges, edges, edges], axis=2)
        return Image.fromarray(edges)

    def _render_base_text(self, word: str, size=(512, 512), font_name="arial.ttf") -> Image.Image:
        """Создает базовое изображение текста обычным шрифтом с автоподгонкой размера."""
        img = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(img)
        
        # Оставляем отступ (padding) 40px со всех сторон
        max_w = size[0] - 80
        max_h = size[1] - 80
        
        # Подбираем оптимальный размер шрифта, начиная с очень большого
        best_font = None
        for fs in range(400, 10, -5):
            try:
                font = ImageFont.truetype(f"C:/Windows/Fonts/{font_name}", size=fs)
            except:
                font = ImageFont.load_default()
                best_font = font
                break
                
            if "\n" in word:
                bbox = draw.multiline_textbbox((0, 0), word, font=font)
            else:
                bbox = draw.textbbox((0, 0), word, font=font)
                
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            if text_w <= max_w and text_h <= max_h:
                best_font = font
                break
                
        if best_font is None:
            best_font = ImageFont.load_default()
            
        if "\n" in word:
            bbox = draw.multiline_textbbox((0, 0), word, font=best_font)
        else:
            bbox = draw.textbbox((0, 0), word, font=best_font)
            
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size[0] - text_w) // 2
        y = (size[1] - text_h) // 2
        
        if "\n" in word:
            draw.multiline_text((x, y), word, fill="black", font=best_font, align="center")
        else:
            draw.text((x, y), word, fill="black", font=best_font)
            
        return img

    @torch.no_grad()
    def generate_cyrillic(self, style_reference_image: Image.Image, word: str = "АБВ", steps: int = 20) -> Image.Image:
        """
        Основной пайплайн: берет кириллическое слово, рендерит его обычным шрифтом (как структурна для ControlNet),
        и применяет стиль reference_image через IP-Adapter.
        """
        if not self.is_loaded:
            self.load_models()
            
        print(f"[*] Генерация кириллицы для '{word}'...")
        
        # 1. Готовим структуру (каркас букв) для Canny ControlNet
        base_text_img = self._render_base_text(word, size=(512, 512))
        canny_condition = self._get_canny_image(base_text_img)
        
        # 2. Подготавливаем референс стиля (должен быть квадратным)
        style_ref = style_reference_image.copy()
        if style_ref.size != (512, 512):
            style_ref = style_ref.resize((512, 512), Image.LANCZOS)
            
        # 3. Генерация через SD Pipeline
        # prompt опционален, так как IP-adapter тянет визуальную часть
        # Улучшенный prompt для идеально чистого белого фона
        prompt = "typography design, letters, pure white background, solid background, perfectly clean background, black text, typography, graphic design"
        negative_prompt = "lowres, bad art, ugly, messy, poor quality, watermark, colored background, noise, gradients on background, textured background, grey background, off-white background, shadows, realistic"

        # Запуск пайплайна
        # ip_adapter_image - принимает референс
        # image - принимает canny условие
        result = self.pipe(
            prompt,
            negative_prompt=negative_prompt,
            image=canny_condition,                # Условие формы
            ip_adapter_image=style_ref,           # Условие стиля
            num_inference_steps=steps,            # 20-30 шагов достаточно
            generator=torch.manual_seed(42),
            guidance_scale=7.5,
            controlnet_conditioning_scale=1.0,    # Жестко держать форму
        ).images[0]
        
        return result
