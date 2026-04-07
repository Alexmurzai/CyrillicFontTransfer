"""
Обертка над OpenAI CLIP для извлечения стилевых векторов шрифтов на локальной машине (GPU).
"""

import torch
from transformers import CLIPModel, CLIPProcessor, CLIPTokenizer
from PIL import Image


class StyleEmbedder:
    """Извлекает 512-мерный вектор признаков (embedding) из изображения или текста."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str = "auto"):
        """
        model_name: имя модели на HuggingFace Hub.
        device: 'cuda', 'cpu', или 'auto'.
        """
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[*] StyleEmbedder: Загрузка {model_name} на {self.device}...")

        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.tokenizer = CLIPTokenizer.from_pretrained(model_name)

        self.model.eval()

        print("[+] StyleEmbedder успешно инициализирован.")

    def _to_tensor(self, obj) -> torch.Tensor:
        """
        Извлекает torch.Tensor из любого вывода CLIP.
        Использует vision_model.pooler_output как наиболее надёжный источник.
        """
        if isinstance(obj, torch.Tensor):
            return obj
        # Перебираем все стандартные атрибуты ModelOutput
        for attr in ("pooler_output", "image_embeds", "text_embeds",
                     "last_hidden_state", "logits"):
            val = getattr(obj, attr, None)
            if isinstance(val, torch.Tensor):
                # Усредняем по последовательность (seq dim), если 3D
                if val.dim() == 3:
                    val = val.mean(dim=1)
                return val
        # Последний шанс: список/кортеж
        if isinstance(obj, (list, tuple)) and len(obj) > 0:
            first = obj[0]
            if isinstance(first, torch.Tensor):
                return first
        raise TypeError(f"Не удалось извлечь тензор из вывода CLIP: {type(obj)}")

    @torch.no_grad()
    def get_embedding(self, image: Image.Image) -> list[float]:
        """Принимает на вход Pillow Image и возвращает нормализованный float32 вектор."""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)

        # Вызываем ТОЛЬКО vision_model — гарантированно возвращает BaseModelOutputWithPooling
        # у которого pooler_output — всегда torch.Tensor
        vision_out = self.model.vision_model(**inputs)
        pooled: torch.Tensor = vision_out.pooler_output  # shape: [1, 768]

        # Применяем проекцию (768 → 512) как в оригинальном CLIP
        features = self.model.visual_projection(pooled)  # shape: [1, 512]

        # L2 нормализация
        features = features / features.norm(p=2, dim=-1, keepdim=True)

        return features[0].detach().cpu().numpy().flatten().tolist()

    @torch.no_grad()
    def get_text_embedding(self, text: str) -> list[float]:
        """Принимает на вход строку и возвращает нормализованный float32 вектор."""
        inputs = self.tokenizer([text], padding=True, return_tensors="pt").to(self.device)

        # Вызываем ТОЛЬКО text_model — аналогично vision_model
        text_out = self.model.text_model(**inputs)
        pooled: torch.Tensor = text_out.pooler_output  # shape: [1, 512]

        # Применяем текстовую проекцию
        features = self.model.text_projection(pooled)  # shape: [1, 512]

        # L2 нормализация
        features = features / features.norm(p=2, dim=-1, keepdim=True)

        return features[0].detach().cpu().numpy().flatten().tolist()
